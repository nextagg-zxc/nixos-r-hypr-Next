"""Flowseal tg-ws-proxy (local MTProto proxy for Telegram Desktop), managed
per user on both platforms. The binary lives in our user dir, its config in
the app's own standard dir (%APPDATA%\\TgWsProxy or ~/.config/TgWsProxy)."""

import csv
import hashlib
import io
import json
import os
import re
import shutil
import signal
import subprocess
import urllib.request

from . import config

PROC_NAME = "TgWsProxy"   # the app's own single-instance check matches on this name
PHOTO_FIX_DC = ["4:149.154.167.220"]
DEFAULTS = {"host": "127.0.0.1", "port": 1443, "dc_ip": ["2:149.154.167.220", "4:149.154.167.220"],
            "check_updates": True, "language": "ru"}
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_TAG = "-- zapret-hub:tg-ws-proxy"
CONFIG_DIR_OVERRIDE = None   # tests
NO_WINDOW = 0x08000000       # CREATE_NO_WINDOW


def asset_name():
    return "TgWsProxy_windows.exe" if config.IS_WINDOWS else "TgWsProxy_linux_amd64"


def install_dir():
    return os.path.join(config.USER_DIR, "TgWsProxy")


def binary():
    return os.path.join(install_dir(), PROC_NAME + (".exe" if config.IS_WINDOWS else ""))


def config_dir():
    if CONFIG_DIR_OVERRIDE:
        return CONFIG_DIR_OVERRIDE
    if config.IS_WINDOWS:
        return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), PROC_NAME)
    return os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), PROC_NAME)


def config_file():
    return os.path.join(config_dir(), "config.json")


def log_file():
    return os.path.join(config_dir(), "proxy.log")


def is_installed():
    return os.path.isfile(binary())


def installed_version():
    try:
        with open(os.path.join(install_dir(), "version")) as f:
            return f.read().strip()
    except OSError:
        return None


# ---------------------------------------------------------------- config

def load_config():
    cfg = dict(DEFAULTS)
    try:
        with open(config_file(), encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            cfg.update(data)
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    os.makedirs(config_dir(), exist_ok=True)
    tmp = config_file() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    os.replace(tmp, config_file())


def ensure_config():
    """Create a config with a fresh secret so the link works before the first
    launch, and skip the app's own first-run window (our page replaces it)."""
    cfg = load_config()
    if not re.fullmatch(r"[0-9a-fA-F]{32}", str(cfg.get("secret", ""))):
        cfg["secret"] = os.urandom(16).hex()
    save_config(cfg)
    # skip the app's own first-run window and one-time IPv6 popup: our page explains both
    for name in (".first_run_done_mtproto", ".ipv6_warned"):
        marker = os.path.join(config_dir(), name)
        if not os.path.exists(marker):
            open(marker, "w").close()
    return cfg


def proxy_url(cfg):
    host = cfg.get("host", "127.0.0.1")
    if host == "0.0.0.0":
        host = "127.0.0.1"
    return f"tg://proxy?server={host}&port={cfg.get('port', 1443)}&secret=dd{cfg.get('secret', '')}"


def parse_dc_lines(text):
    """'2:1.2.3.4' per line/comma -> list, or raises ValueError."""
    out = []
    for part in re.split(r"[\s,;]+", text.strip()):
        if not part:
            continue
        if not re.fullmatch(r"-?\d{1,3}:[0-9a-fA-F:.]+", part):
            raise ValueError(f"неверная запись DC: {part} (нужно DC:IP, например 4:149.154.167.220)")
        out.append(part)
    return out


# ---------------------------------------------------------------- process

def parse_tasklist(out):
    pids = []
    for row in csv.reader(io.StringIO(out)):
        if len(row) >= 2 and row[0].lower() == PROC_NAME.lower() + ".exe" and row[1].isdigit():
            pids.append(int(row[1]))
    return pids


def running_pids():
    if config.IS_WINDOWS:
        r = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {PROC_NAME}.exe", "/FO", "CSV", "/NH"],
                           capture_output=True, text=True, creationflags=NO_WINDOW)
        return parse_tasklist(r.stdout)
    pids, uid = [], os.getuid()
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            if os.stat(f"/proc/{d}").st_uid != uid:
                continue
            with open(f"/proc/{d}/comm") as f:
                if f.read().strip() == PROC_NAME:
                    pids.append(int(d))
        except OSError:
            continue
    return pids


def is_running():
    return bool(running_pids())


def start():
    if is_running():
        return
    if config.IS_WINDOWS:
        # through explorer so it runs as the desktop user, not elevated like us
        subprocess.Popen(["explorer.exe", binary()], creationflags=NO_WINDOW)
        return
    in_hyprland = bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"))
    cmd = ["uwsm-app", "--", binary()] if in_hyprland and shutil.which("uwsm-app") else [binary()]
    subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)


def stop():
    if config.IS_WINDOWS:
        subprocess.run(["taskkill", "/IM", PROC_NAME + ".exe", "/F"], capture_output=True, creationflags=NO_WINDOW)
        return
    for pid in running_pids():
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass


def open_tg_url(u):
    """Open a tg:// link in Telegram as the desktop user."""
    if config.IS_WINDOWS:
        subprocess.Popen(["explorer.exe", u], creationflags=NO_WINDOW)
    else:
        subprocess.Popen(["xdg-open", u], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


# ---------------------------------------------------------------- autostart

def _linux_paths():
    xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(xdg, "hypr", "autostart.lua"), os.path.join(xdg, "autostart", "tg-ws-proxy.desktop")


def desktop_entry():
    return ("[Desktop Entry]\nType=Application\nName=TG WS Proxy\n"
            "Comment=Локальный прокси для Telegram (Flowseal)\n"
            f"Exec={binary()}\nIcon=telegram\nTerminal=false\nCategories=Network;\n")


def autostart_enabled():
    if config.IS_WINDOWS:
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
                return bool(winreg.QueryValueEx(k, PROC_NAME)[0])
        except OSError:
            return False
    hypr, xdg = _linux_paths()
    try:
        with open(hypr) as f:
            if AUTOSTART_TAG in f.read():
                return True
    except OSError:
        pass
    return os.path.exists(xdg)


def set_autostart(enabled):
    if config.IS_WINDOWS:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            if enabled:
                # same value the app itself writes, so its own checkbox agrees
                winreg.SetValueEx(k, PROC_NAME, 0, winreg.REG_SZ, f'"{binary()}"')
            else:
                try:
                    winreg.DeleteValue(k, PROC_NAME)
                except OSError:
                    pass
        return
    # Hyprland/Omarchy read hypr/autostart.lua, other desktops XDG autostart;
    # the app's own single-instance lock prevents a double start
    hypr, xdg = _linux_paths()
    if os.path.exists(hypr):
        with open(hypr) as f:
            lines = [l for l in f.read().splitlines() if AUTOSTART_TAG not in l]
        if enabled:
            lines.append(f'o.launch_on_start("{binary()}") {AUTOSTART_TAG}')
        with open(hypr, "w") as f:
            f.write("\n".join(lines) + "\n")
    if enabled:
        os.makedirs(os.path.dirname(xdg), exist_ok=True)
        with open(xdg, "w") as f:
            f.write(desktop_entry())
    elif os.path.exists(xdg):
        os.remove(xdg)


# ---------------------------------------------------------------- install

def latest_release():
    req = urllib.request.Request(config.url("tgws_api"),
                                 headers={"User-Agent": "zapret-hub", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        rel = json.load(r)
    asset = next((a for a in rel.get("assets", []) if a["name"] == asset_name()), None)
    if not asset:
        raise RuntimeError("в релизе TG WS Proxy нет сборки для этой системы")
    return rel["tag_name"], config.mirror(asset["browser_download_url"]), (asset.get("digest") or "").removeprefix("sha256:")


def install(progress=lambda f: None):
    """Download the release binary, verify SHA-256, put it in install_dir()."""
    tag, u, digest = latest_release()
    os.makedirs(install_dir(), exist_ok=True)
    tmp = binary() + ".download"
    h = hashlib.sha256()
    req = urllib.request.Request(u, headers={"User-Agent": "zapret-hub"})
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while chunk := r.read(256 * 1024):
            f.write(chunk)
            h.update(chunk)
            done += len(chunk)
            if total:
                progress(done / total)
    if digest and h.hexdigest() != digest:
        os.remove(tmp)
        raise RuntimeError("контрольная сумма не совпала — файл повреждён, попробуй ещё раз")
    os.chmod(tmp, 0o755)
    was_running = is_running()
    if was_running:
        stop()
    os.replace(tmp, binary())
    with open(os.path.join(install_dir(), "version"), "w") as f:
        f.write(tag + "\n")
    if not config.IS_WINDOWS:
        p = os.path.expanduser("~/.local/share/applications/tg-ws-proxy.desktop")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(desktop_entry())
    ensure_config()
    if was_running:
        start()
    return tag


def uninstall():
    stop()
    set_autostart(False)
    if not config.IS_WINDOWS:
        p = os.path.expanduser("~/.local/share/applications/tg-ws-proxy.desktop")
        if os.path.exists(p):
            os.remove(p)
    shutil.rmtree(install_dir(), ignore_errors=True)


def read_log(lines=300):
    try:
        with open(log_file(), encoding="utf-8", errors="replace") as f:
            return f.readlines()[-lines:]
    except OSError:
        return []
