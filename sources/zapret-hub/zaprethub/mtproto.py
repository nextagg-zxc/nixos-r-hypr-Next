"""Public MTProto proxies for Telegram: collect links from open lists, check
which servers answer, remember favorites and the user's own servers."""

import concurrent.futures
import html
import json
import os
import re
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass

from . import config, probe

LINK_RE = re.compile(r"(?:tg://proxy|https?://t\.me/proxy)\?[^\s\"'<>]+", re.I)
HOST_RE = re.compile(r"^[A-Za-z0-9.\-_:\[\]]{1,253}$")
HEX_SECRET_RE = re.compile(r"^(?:[0-9a-fA-F]{2}){16,}$")
B64_SECRET_RE = re.compile(r"^[A-Za-z0-9_\-+/=]{16,}$")


@dataclass
class Proxy:
    server: str
    port: int
    secret: str
    source: str
    ping: float = None
    alive: bool = None

    @property
    def key(self):
        return f"{self.server.lower()}:{self.port}:{self.secret.lower()}"

    @property
    def kind(self):
        s = self.secret.lower()
        if s.startswith("ee"):
            return "Fake TLS"
        if s.startswith("dd"):
            return "Secure"
        return "Обычный"

    def tg_url(self):
        q = urllib.parse.urlencode({"server": self.server, "port": self.port, "secret": self.secret})
        return f"tg://proxy?{q}"


def parse_link(link, source):
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(html.unescape(link)).query)
    server = (q.get("server") or [""])[0].strip().rstrip(".")
    secret = (q.get("secret") or [""])[0].strip()
    try:
        port = int((q.get("port") or [""])[0])
    except ValueError:
        return None
    if not server or not HOST_RE.match(server) or not 0 < port < 65536:
        return None
    if not (HEX_SECRET_RE.match(secret) or B64_SECRET_RE.match(secret)):
        return None
    return Proxy(server, port, secret, source)


def parse_links(text, source):
    out, seen = [], set()
    for m in LINK_RE.finditer(text):
        p = parse_link(m.group(0), source)
        if p and p.key not in seen:
            seen.add(p.key)
            out.append(p)
    return out


def http_fetch(u, timeout):
    req = urllib.request.Request(config.mirror(u), headers={"User-Agent": "zapret-hub", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(4 * 1024 * 1024).decode("utf-8", "replace")


def fetch_all(sources, timeout=15, fetch=http_fetch):
    """Download every source in parallel -> (unique proxies, error messages).
    A broken source never hides the others."""
    def one(src):
        try:
            found = parse_links(fetch(src["url"], timeout), src["name"])
        except Exception as e:  # noqa: BLE001
            return [], f"{src['name']}: не удалось загрузить ({e})"
        if not found:
            return [], f"{src['name']}: в ответе нет ни одного прокси"
        return found, None

    proxies, errors, seen = [], [], set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for found, err in ex.map(one, sources):
            if err:
                errors.append(err)
            for p in found:
                if p.key not in seen:
                    seen.add(p.key)
                    proxies.append(p)
    return proxies, errors


def sort_key(p):
    return (not p.alive, p.ping if p.ping is not None else 1e9)


def check_all(proxies, workers=64, timeout=3, ping=probe.tcp_ping, on_progress=None):
    """TCP-connect every proxy; fills ping/alive and returns them alive-first by ping."""
    done = 0

    def one(p):
        p.ping = ping(p.server, p.port, timeout)
        p.alive = p.ping is not None
        return p

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        for _ in ex.map(one, proxies):
            done += 1
            if on_progress:
                on_progress(done, len(proxies))
    return sorted(proxies, key=sort_key)


class Store:
    """mtproto.json in the user's profile: last list, favorites, own servers, sources."""

    def __init__(self, path=None):
        self.path = path or config.MTPROTO_CACHE
        self.proxies, self.custom, self.favorites = [], [], []
        self.sources = [dict(s) for s in config.MTPROTO_SOURCES]
        self.updated = None
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return
        self.proxies = self._load(data.get("proxies"))
        self.custom = self._load(data.get("custom"))
        self.favorites = [k for k in data.get("favorites", []) if isinstance(k, str)]
        if isinstance(data.get("sources"), list) and data["sources"]:
            self.sources = [s for s in data["sources"] if isinstance(s, dict) and s.get("url")]
        self.updated = data.get("updated")

    @staticmethod
    def _load(items):
        out = []
        for d in items or []:
            try:
                out.append(Proxy(str(d["server"]), int(d["port"]), str(d["secret"]), str(d.get("source", "")),
                                 d.get("ping"), d.get("alive")))
            except (KeyError, TypeError, ValueError):
                continue
        return out

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        data = {"updated": self.updated, "proxies": [asdict(p) for p in self.proxies],
                "custom": [asdict(p) for p in self.custom], "favorites": self.favorites,
                "sources": self.sources}
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, self.path)

    def set_list(self, proxies):
        self.proxies = proxies
        self.updated = time.time()

    def toggle_favorite(self, key):
        if key in self.favorites:
            self.favorites.remove(key)
        else:
            self.favorites.append(key)

    def add_custom(self, link):
        ps = parse_links(link, "Свой")
        if not ps:
            return False
        keys = {p.key for p in self.custom}
        self.custom += [p for p in ps if p.key not in keys]
        return True

    def remove_custom(self, key):
        self.custom = [p for p in self.custom if p.key != key]

    def all(self):
        """Own servers first, then the downloaded list, without duplicates."""
        seen, out = set(), []
        for p in self.custom + self.proxies:
            if p.key not in seen:
                seen.add(p.key)
                out.append(p)
        return out
