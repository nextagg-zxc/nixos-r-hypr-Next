"""Paths and URLs. Everything that touches the network goes through url() so a
local mirror (ZAPRETHUB_MIRROR) can stand in for GitHub during tests."""

import os
import sys

IS_WINDOWS = sys.platform == "win32"
APP_NAME = "Zapret Hub"


def _is_root():
    return not IS_WINDOWS and os.geteuid() == 0


if IS_WINDOWS:
    DATA_DIR = os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"), "ZapretHub")
    USER_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "ZapretHub")
else:
    # ZAPRETHUB_BASE lets the unprivileged GUI run against a test tree; root ignores it.
    DATA_DIR = "/opt/zapret-hub" if _is_root() else os.environ.get("ZAPRETHUB_BASE", "/opt/zapret-hub")
    USER_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "zapret-hub")

FLOWSEAL_DIR = os.path.join(DATA_DIR, "flowseal")   # unpacked Flowseal release
BIN_DIR = os.path.join(FLOWSEAL_DIR, "bin")         # fakes (+ winws.exe on Windows)
LISTS_DIR = os.path.join(DATA_DIR, "lists")
BUILTIN_DIR = os.path.join(DATA_DIR, "strategies-builtin")
CUSTOM_DIR = os.path.join(DATA_DIR, "strategies")
STATE_FILE = os.path.join(DATA_DIR, "state.json")
VERSIONS_FILE = os.path.join(DATA_DIR, "versions.json")
TARGETS_FILE = os.path.join(DATA_DIR, "targets.txt")
RESULTS_FILE = os.path.join(DATA_DIR, "test-results.json")
IPSET_FULL = os.path.join(LISTS_DIR, "ipset-all.full.txt")
ZAPRET_DIR = os.path.join(DATA_DIR, "zapret")       # Linux: bol-van/zapret (nfqws)
NFQWS = os.path.join(ZAPRET_DIR, "nfq", "nfqws")   # скачанный свежий zapret (bol-van)
# NixOS: nfqws из nixpkgs — только запасной, если скачать/подобрать свежий не вышло (стратегии Flowseal
# ждут свежий nfqws, а nixpkgs, особенно стабильная ветка, отстаёт). Путь задаёт обёртка пакета;
# pkexec сбрасывает окружение, так что root видит только то, что задала обёртка из хранилища Nix.
NFQWS_FALLBACK = os.environ.get("ZAPRETHUB_NFQWS_FALLBACK", "")


def nfqws():
    """Скачанный nfqws, если он есть; иначе запасной из системы; иначе путь скачанного."""
    downloaded = os.path.join(ZAPRET_DIR, "nfq", "nfqws")
    if os.access(downloaded, os.X_OK) or not NFQWS_FALLBACK:
        return downloaded
    return NFQWS_FALLBACK
# NixOS: юнит и /etc/hosts описывает модуль. Автозапуск — файл-флаг (модуль запускает службу, если он
# есть), блок hosts хранится в файле и возвращается модулем после пересборки системы.
NIXOS = os.environ.get("ZAPRETHUB_NIXOS") == "1"
AUTOSTART_FLAG = os.path.join(DATA_DIR, "autostart")
HOSTS_BLOCK_FILE = os.path.join(DATA_DIR, "hosts.block")
WINWS = os.path.join(BIN_DIR, "winws.exe")
HOSTS_FILE = (os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "drivers", "etc", "hosts")
              if IS_WINDOWS else "/etc/hosts")

USER_SETTINGS = os.path.join(USER_DIR, "settings.json")
MTPROTO_CACHE = os.path.join(USER_DIR, "mtproto.json")

_RAW = "https://raw.githubusercontent.com"
_API = "https://api.github.com"
_GH = "https://github.com"

URLS = {
    "flowseal_version": f"{_RAW}/Flowseal/zapret-discord-youtube/main/.service/version.txt",
    "flowseal_api": f"{_API}/repos/Flowseal/zapret-discord-youtube/releases/latest",
    "flowseal_ipset": f"{_RAW}/Flowseal/zapret-discord-youtube/refs/heads/main/.service/ipset-service.txt",
    "flowseal_hosts": f"{_RAW}/Flowseal/zapret-discord-youtube/refs/heads/main/.service/hosts",
    "flowseal_releases": f"{_GH}/Flowseal/zapret-discord-youtube/releases",
    "zapret_api": f"{_API}/repos/bol-van/zapret/releases/latest",
    "tgws_api": f"{_API}/repos/Flowseal/tg-ws-proxy/releases/latest",
}

MTPROTO_SOURCES = [
    {"name": "Россия (kort0881)", "url": f"{_RAW}/kort0881/telegram-proxy-collector/main/proxy_ru.txt"},
    {"name": "Весь мир (kort0881)", "url": f"{_RAW}/kort0881/telegram-proxy-collector/main/proxy_all.txt"},
    {"name": "SoliSpirit", "url": f"{_RAW}/SoliSpirit/mtproto/master/all_proxies.txt"},
    {"name": "Grim1313", "url": f"{_RAW}/Grim1313/mtproto-for-telegram/master/all_proxies.txt"},
]


def mirror(u):
    """Rewrite a GitHub URL onto ZAPRETHUB_MIRROR when it is set."""
    m = os.environ.get("ZAPRETHUB_MIRROR", "").rstrip("/")
    if not m:
        return u
    for prefix, sub in ((_RAW, "raw"), (_API, "api"), (_GH, "gh")):
        if u.startswith(prefix + "/"):
            return f"{m}/{sub}{u[len(prefix):]}"
    return u


def url(name):
    return mirror(URLS[name])
