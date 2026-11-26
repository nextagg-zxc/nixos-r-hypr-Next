"""Privileged half on Linux. Runs as root via pkexec (from the GUI) or systemd
(fw-up / run / fw-down). Prints plain log lines; structured events are lines
starting with '@@' followed by JSON. Long operations abort when stdin is
closed (the GUI's way to cancel, since it cannot signal root)."""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.error

from . import config, core, testrun, updates

SERVICE = "zapret-hub.service"
# everything install.sh puts outside /opt (uninstall --system, used by the AppImage)
SYSTEM_FILES = ["/usr/lib/systemd/system/zapret-hub.service", "/usr/share/polkit-1/actions/org.zaprethub.helper.policy",
                "/usr/bin/zapret-hub", "/usr/share/applications/zapret-hub.desktop",
                "/usr/share/icons/hicolor/scalable/apps/zapret-hub.svg", "/usr/lib/zapret-hub"]
CONFLICT_UNITS = {"zapret_gui": "zapret-gui.service", "zapret_service": "zapret.service"}
cancelled = threading.Event()


def log(msg):
    print(msg, flush=True)


def event(**kw):
    print("@@" + json.dumps(kw, ensure_ascii=False), flush=True)


def die(msg, code=1):
    log(f"ОШИБКА: {msg}")
    sys.exit(code)


def watch_stdin():
    """Set `cancelled` when the GUI closes our stdin."""
    def run():
        # raw fd, not sys.stdin: a daemon thread blocked inside a buffered
        # reader aborts the interpreter at exit
        try:
            while os.read(0, 4096):
                pass
        except OSError:
            pass
        cancelled.set()
    if not sys.stdin.isatty():
        threading.Thread(target=run, daemon=True).start()


def read_stdin_text(limit=8 * 1024 * 1024):
    data = sys.stdin.buffer.read(limit + 1)
    if len(data) > limit:
        die("слишком большой ввод")
    return data.decode("utf-8")


def sh(cmd, check=True, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if check and r.returncode:
        die(f"{' '.join(cmd)}: {(r.stderr or r.stdout).strip()}")
    return r


def service_active():
    return sh(["systemctl", "is-active", "--quiet", SERVICE], check=False).returncode == 0


def set_autostart(on):
    """Служба при загрузке: на NixOS — файл-флаг (юниты в /etc/systemd только для чтения), иначе systemctl."""
    if config.NIXOS:
        if on:
            open(config.AUTOSTART_FLAG, "a").close()
        elif os.path.exists(config.AUTOSTART_FLAG):
            os.remove(config.AUTOSTART_FLAG)
    else:
        sh(["systemctl", "enable" if on else "disable", SERVICE], check=False)


def is_installed():
    return os.access(config.nfqws(), os.X_OK) and os.path.isdir(config.BUILTIN_DIR)


def save_state(st):
    updates.write_file(config.STATE_FILE, json.dumps(st, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------- install / update

def install_zapret(work, versions):
    log("Узнаю последнюю версию zapret (bol-van)…")
    with updates.http_get(config.url("zapret_api"), "application/vnd.github+json") as r:
        rel = json.load(r)
    tag = rel["tag_name"]
    if os.access(os.path.join(config.ZAPRET_DIR, "nfq", "nfqws"), os.X_OK) and versions.get("zapret") == tag:
        log(f"zapret {tag} уже стоит")
        return
    asset = next(x for x in rel["assets"] if re.fullmatch(r"zapret-v[\d.]+\.tar\.gz", x["name"]))
    tgz = os.path.join(work, "zapret.tar.gz")
    log(f"Скачиваю zapret {tag}…")
    updates.download(config.mirror(asset["browser_download_url"]), tgz)
    ex = os.path.join(work, "zapret")
    os.mkdir(ex)
    with tarfile.open(tgz) as t:
        t.extractall(ex, filter="data")
    src = updates.strip_top(ex)
    log("Подбираю nfqws под систему (install_bin.sh)…")
    r = subprocess.run(["sh", "./install_bin.sh"], cwd=src, capture_output=True, text=True)
    if r.returncode or not os.access(os.path.join(src, "nfq/nfqws"), os.X_OK):
        die(f"install_bin.sh не смог подобрать nfqws: {r.stderr.strip()}")
    updates.swap_dir(src, config.ZAPRET_DIR)
    versions["zapret"] = tag


def cmd_install(a):
    watch_stdin()
    os.makedirs(config.DATA_DIR, mode=0o755, exist_ok=True)
    os.chmod(config.DATA_DIR, 0o755)
    work = tempfile.mkdtemp(dir=config.DATA_DIR, prefix=".dl-")
    try:
        versions = core.load_json(config.VERSIONS_FILE)
        try:
            install_zapret(work, versions)
        except (OSError, ValueError, KeyError, StopIteration, urllib.error.URLError) as e:
            if not os.access(config.nfqws(), os.X_OK):
                die(f"не удалось скачать zapret: {e}. Проверь интернет и попробуй ещё раз.")
            if config.nfqws() == config.NFQWS_FALLBACK:
                log(f"zapret не скачан ({e}), беру nfqws из системы (nixpkgs)")
                versions["zapret"] = "nixpkgs"
            else:
                log(f"zapret не обновлён ({e}), оставляю установленный")
        if cancelled.is_set():
            die("отменено")
        try:
            versions["flowseal"] = updates.install_flowseal(config.FLOWSEAL_DIR, log, windows=False)
        except RuntimeError as e:
            die(str(e))
        updates.convert_builtin(config.FLOWSEAL_DIR, config.BUILTIN_DIR, log)
        st = core.load_state(config.STATE_FILE)
        updates.setup_lists(config.FLOWSEAL_DIR, config.LISTS_DIR, st["ipset"], config.IPSET_FULL)
        updates.install_targets(config.FLOWSEAL_DIR, config.TARGETS_FILE)
        os.makedirs(config.CUSTOM_DIR, mode=0o755, exist_ok=True)
        if not os.path.exists(config.STATE_FILE):
            save_state(dict(core.DEFAULT_STATE))
        updates.write_file(config.VERSIONS_FILE, json.dumps(versions, indent=2))
        for root, dirs, files in os.walk(config.DATA_DIR):
            os.chmod(root, 0o755)
        sh(["systemctl", "daemon-reload"], check=False)
        if service_active():
            log("Перезапускаю службу…")
            sh(["systemctl", "restart", SERVICE], check=False)
        log(f"Готово: zapret {versions.get('zapret')}, стратегии Flowseal {versions['flowseal']}")
        event(type="done", ok=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ---------------------------------------------------------------- firewall / daemon

def current_build(name=None, game=None):
    st = core.load_state(config.STATE_FILE)
    name = name or st["strategy"]
    path = core.strategy_path(name, config.BUILTIN_DIR, config.CUSTOM_DIR)
    if not os.path.exists(path):
        die(f"стратегия «{name}» не найдена")
    with open(path, encoding="utf-8") as f:
        return core.build(f.read(), game or st["game_filter"], config.BIN_DIR, config.LISTS_DIR)


def nfqws_argv(args):
    return [config.nfqws(), f"--qnum={core.QNUM}", f"--dpi-desync-fwmark={core.DESYNC_MARK:#x}", "--user=nobody"] + args


def fw_up(tcp, udp):
    sh(["nft", "-f", "-"], input=core.nft_ruleset(tcp, udp))


def fw_down():
    sh(["nft", "delete", "table", "inet", core.NFT_TABLE], check=False)


def cmd_fw_up(a):
    _, tcp, udp = current_build()
    fw_up(tcp, udp)


def cmd_fw_down(a):
    fw_down()


def cmd_run(a):
    if not is_installed():
        die("zapret не установлен")
    args, _, _ = current_build()
    argv = nfqws_argv(args)
    os.execv(argv[0], argv)


def check_current():
    args, tcp, udp = current_build()
    core.merge_ports(tcp or "1")
    core.merge_ports(udp or "1")
    r = subprocess.run([config.nfqws(), "--dry-run"] + nfqws_argv(args)[1:], capture_output=True, text=True)
    if r.returncode:
        lines = (r.stdout + r.stderr).strip().splitlines()
        raise ValueError(lines[-1] if lines else "nfqws отверг параметры")


def service_start():
    if not is_installed():
        die("zapret не установлен — нажми «Установить»")
    try:
        check_current()
    except (OSError, ValueError) as e:
        die(f"стратегия не прошла проверку: {e}")
    st = core.load_state(config.STATE_FILE)
    set_autostart(st["autostart"])
    r = sh(["systemctl", "restart", SERVICE], check=False)
    time.sleep(1)
    if r.returncode or not service_active():
        jr = sh(["journalctl", "-u", SERVICE, "-n", "12", "--no-pager", "-o", "cat"], check=False)
        die(f"служба не запустилась. Попробуй другую стратегию.\n{jr.stdout.strip()}")


def cmd_service(a):
    if a.action == "start":
        service_start()
        log("Обход включён")
    else:
        sh(["systemctl", "stop", SERVICE], check=False)
        set_autostart(False)
        fw_down()
        log("Обход выключен")


def restart_if_active():
    if service_active():
        log("Перезапускаю службу…")
        service_start()


def cmd_set_state(a):
    data = json.loads(read_stdin_text())
    st = core.load_state(config.STATE_FILE)
    if "strategy" in data:
        if not core.valid_name(data["strategy"]) or not os.path.exists(
                core.strategy_path(data["strategy"], config.BUILTIN_DIR, config.CUSTOM_DIR)):
            die("нет такой стратегии")
        st["strategy"] = data["strategy"]
    if "game_filter" in data:
        if data["game_filter"] not in core.GAME_FILTER_MODES:
            die("неверный режим игрового фильтра")
        st["game_filter"] = data["game_filter"]
    if "ipset" in data:
        if data["ipset"] not in core.IPSET_MODES:
            die("неверный режим IPSet")
        st["ipset"] = data["ipset"]
        updates.apply_ipset_mode(config.LISTS_DIR, st["ipset"], config.IPSET_FULL)
    if "autostart" in data:
        st["autostart"] = bool(data["autostart"])
        if service_active():
            set_autostart(st["autostart"])
    old = core.load_state(config.STATE_FILE)
    save_state(st)
    try:
        if is_installed():
            check_current()
    except ValueError as e:
        save_state(old)
        die(f"стратегия не прошла проверку: {e}")
    if any(k in data for k in ("strategy", "game_filter", "ipset")):
        restart_if_active()
    log("OK")


# ---------------------------------------------------------------- files

def cmd_write_list(a):
    if a.name not in core.USER_LISTS:
        die("этот список нельзя менять")
    updates.write_file(os.path.join(config.LISTS_DIR, a.name), core.clean_list(a.name, read_stdin_text()))
    restart_if_active()
    log("Список сохранён")


def cmd_ipset_update(a):
    log("Скачиваю список IPSet от Flowseal…")
    try:
        text = updates.fetch_ipset()
    except (OSError, RuntimeError, urllib.error.URLError) as e:
        die(str(e))
    updates.write_file(config.IPSET_FULL, text)
    log(f"Адресов в списке: {text.count(chr(10))}")
    if core.load_state(config.STATE_FILE)["ipset"] == "loaded":
        updates.apply_ipset_mode(config.LISTS_DIR, "loaded", config.IPSET_FULL)
        restart_if_active()


def cmd_hosts(a):
    with open(config.HOSTS_FILE) as f:
        cur = f.read()
    block = ""
    if a.action == "update":
        log("Скачиваю hosts от Flowseal…")
        try:
            block = updates.fetch_hosts()
        except (OSError, RuntimeError, urllib.error.URLError) as e:
            die(str(e))
    shutil.copy(config.HOSTS_FILE, config.HOSTS_FILE + ".zapret-hub.bak")
    updates.write_file(config.HOSTS_FILE, core.hosts_block_replace(cur, block))
    # копия блока: на NixOS модуль дописывает его в /etc/hosts после каждой пересборки
    if block.strip():
        updates.write_file(config.HOSTS_BLOCK_FILE, block.strip() + "\n")
    elif os.path.exists(config.HOSTS_BLOCK_FILE):
        os.remove(config.HOSTS_BLOCK_FILE)
    log("hosts обновлён" if block else "Записи убраны из hosts")


def cmd_hosts_restore(a):
    """NixOS: активация кладёт /etc/hosts заново — возвращаем наш блок из HOSTS_BLOCK_FILE."""
    try:
        with open(config.HOSTS_BLOCK_FILE, encoding="utf-8") as f:
            block = f.read()
    except OSError:
        return
    if not block.strip():
        return
    with open(config.HOSTS_FILE, encoding="utf-8") as f:
        cur = f.read()
    new = core.hosts_block_replace(cur, block)
    if new != cur:
        updates.write_file(config.HOSTS_FILE, new)


def cmd_fix(a):
    unit = CONFLICT_UNITS.get(a.id)
    if not unit:
        die("это нужно исправить вручную")
    if config.NIXOS:
        # юниты NixOS в /etc/systemd только для чтения: disable невозможен — маскируем до перезагрузки
        sh(["systemctl", "stop", unit], check=False)
        sh(["systemctl", "mask", "--runtime", unit], check=False)
    else:
        sh(["systemctl", "disable", "--now", unit], check=False)
    if unit == "zapret-gui.service":
        sh(["nft", "delete", "table", "inet", "zapret_gui"], check=False)
    log(f"{unit} остановлен" + (" до перезагрузки (на NixOS отключи его в конфигурации системы)" if config.NIXOS
                                else " и отключён"))


def cmd_uninstall(a):
    sh(["systemctl", "stop", SERVICE], check=False)
    set_autostart(False)
    fw_down()
    try:
        with open(config.HOSTS_FILE) as f:
            cur = f.read()
        if core.HOSTS_BEGIN in cur:
            updates.write_file(config.HOSTS_FILE, core.hosts_block_replace(cur, ""))
    except OSError:
        pass
    if os.path.realpath(config.DATA_DIR) == "/opt/zapret-hub":
        shutil.rmtree(config.DATA_DIR, ignore_errors=True)
    log("Файлы zapret удалены")
    if getattr(a, "system", False):
        for p in SYSTEM_FILES:
            if os.path.isdir(p) and not os.path.islink(p):
                shutil.rmtree(p, ignore_errors=True)
            elif os.path.lexists(p):
                os.remove(p)
        sh(["systemctl", "daemon-reload"], check=False)
        log("Служба и права администратора удалены")


# ---------------------------------------------------------------- tests

class Runner:
    """nfqws with a given strategy outside the systemd service."""

    def __init__(self, game):
        self.game, self.proc = game, None

    def start(self, name):
        args, tcp, udp = current_build(name, self.game)
        fw_up(tcp, udp)
        self.proc = subprocess.Popen(nfqws_argv(args), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        time.sleep(1.2)
        if self.proc.poll() is not None:
            err = self.proc.stderr.read().strip().splitlines()
            self.stop()
            raise RuntimeError(err[-1] if err else "nfqws завершился")

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(3)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None
        fw_down()


def cmd_test(a):
    watch_stdin()
    if not is_installed():
        die("zapret не установлен")
    names = [n for n in a.strategies.split("|") if n] or \
        [n for n, _ in core.list_strategies(config.BUILTIN_DIR, config.CUSTOM_DIR)]
    for n in names:
        if not core.valid_name(n):
            die(f"недопустимое имя: {n}")
    try:
        with open(config.TARGETS_FILE) as f:
            targets = core.parse_targets(f.read())
    except OSError:
        targets = []
    if not targets:
        die("нет целей для теста — нажми «Обновить»")
    was_active = service_active()
    runner = Runner(core.load_state(config.STATE_FILE)["game_filter"])

    def restore(*_):
        runner.stop()
        if was_active:
            sh(["systemctl", "start", SERVICE], check=False)

    signal.signal(signal.SIGTERM, lambda *_: (restore(), sys.exit(1)))
    if was_active:
        log("Останавливаю службу на время теста…")
        sh(["systemctl", "stop", SERVICE], check=False)
    fw_down()
    try:
        res = testrun.run(names, runner.start, runner.stop, targets, lambda e: event(**e), cancelled, a.timeout)
        updates.write_file(config.RESULTS_FILE, json.dumps(
            testrun.merge(core.load_json(config.RESULTS_FILE), res), ensure_ascii=False, indent=1))
    finally:
        restore()


# ---------------------------------------------------------------- main

def main():
    if os.geteuid() != 0:
        die("нужны права root (запускай через программу Zapret Hub)")
    os.umask(0o022)
    ap = argparse.ArgumentParser(prog="zapret-hub-helper")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("install").set_defaults(fn=cmd_install)
    sub.add_parser("fw-up").set_defaults(fn=cmd_fw_up)
    sub.add_parser("fw-down").set_defaults(fn=cmd_fw_down)
    sub.add_parser("run").set_defaults(fn=cmd_run)
    p = sub.add_parser("service")
    p.add_argument("action", choices=["start", "stop"])
    p.set_defaults(fn=cmd_service)
    sub.add_parser("set-state").set_defaults(fn=cmd_set_state)
    p = sub.add_parser("write-list")
    p.add_argument("name")
    p.set_defaults(fn=cmd_write_list)
    sub.add_parser("ipset-update").set_defaults(fn=cmd_ipset_update)
    p = sub.add_parser("hosts")
    p.add_argument("action", choices=["update", "remove"])
    p.set_defaults(fn=cmd_hosts)
    sub.add_parser("hosts-restore").set_defaults(fn=cmd_hosts_restore)
    p = sub.add_parser("fix")
    p.add_argument("id")
    p.set_defaults(fn=cmd_fix)
    p = sub.add_parser("uninstall")
    p.add_argument("--system", action="store_true")
    p.set_defaults(fn=cmd_uninstall)
    p = sub.add_parser("test")
    p.add_argument("--strategies", default="")
    p.add_argument("--timeout", type=int, default=4)
    p.set_defaults(fn=cmd_test)
    a = ap.parse_args()
    try:
        a.fn(a)
    except KeyboardInterrupt:
        die("прервано")
    except (OSError, ValueError, StopIteration, urllib.error.URLError) as e:
        die(str(e) or type(e).__name__)
