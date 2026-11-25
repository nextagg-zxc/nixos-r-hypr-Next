"""Логика малых программ без GTK: отчёт о проблеме (вычистка личного), запуск .exe/AppImage, RustDesk."""
from __future__ import annotations

import json
import re
from pathlib import Path

# ── «Сообщить о проблеме»: что убрать из журналов ──
_MAC = re.compile(r"\b[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}\b")
_IP4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b")
# IPv6: «::» или не меньше трёх двоеточий (PCI-адрес 0000:03:00.0 и время 12:30:45 — не адреса)
_IP6 = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){3,7}[0-9a-fA-F]{1,4}\b"
                  r"|\b[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4})*::(?:[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4})*)?\b")
_SECRET = re.compile(r"(?i)(bearer\s+|password[=:]\s*|passwd[=:]\s*|token[=:]\s*|secret[=:]\s*|[?&]key=|apikey[=:]\s*)"
                     r"(\S+?)(?=['\"\s&]|$)")


def redact(text: str, user: str, ssids: list[str]) -> str:
    if user:
        text = text.replace(f"/home/{user}", "~").replace(f"/run/media/{user}", "/run/media/<user>")
    for s in ssids:
        if s:
            text = text.replace(s, "<wifi>")
    text = _SECRET.sub(lambda m: m.group(1) + "<скрыто>", text)
    text = _MAC.sub("<mac>", text)
    text = _IP4.sub("<ip>", text)
    text = _IP6.sub("<ip>", text)
    return text


# ── .exe / .msi / AppImage двойным кликом ──
def kind_of(path) -> str | None:
    try:
        head = Path(path).read_bytes()[:16]
    except OSError:
        return None
    if head[:2] == b"MZ" or head[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return "exe"
    if head[:4] == b"\x7fELF" and head[8:11] == b"AI\x02":
        return "appimage"
    return None


def run_command(how: str, path: str) -> list[str]:
    if how == "appimage":
        return ["appimage-run", path]
    if how == "msi":
        return ["wine", "msiexec", "/i", path]
    if how == "proton":
        return ["umu-run", path]
    return ["wine", path]


def remembered(store, path: str) -> str | None:
    try:
        return json.loads(Path(store).read_text(encoding="utf-8")).get(path)
    except (OSError, ValueError):
        return None


def remember(store, path: str, how: str) -> None:
    store = Path(store)
    try:
        data = json.loads(store.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    data[path] = how
    store.parent.mkdir(parents=True, exist_ok=True)
    store.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


# ── «Позвать на помощь»: RustDesk со своим сервером ──
def rustdesk_config(host: str, key: str) -> str:
    return (f"rendezvous_server = '{host}:21116'\nnat_type = 1\nserial = 0\n\n[options]\n"
            f"custom-rendezvous-server = '{host}'\nrelay-server = '{host}'\nkey = '{key}'\n")
