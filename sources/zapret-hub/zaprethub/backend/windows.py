"""Windows: the app runs elevated (uac_admin manifest) and drives winws.exe
from the Flowseal release directly. "On" = a Windows service ZapretHub
running winws.exe with the strategy's arguments, exactly like Flowseal's
service.bat does, so it keeps working with the window closed and after a
reboot. System state is read through psutil/winreg (not localized sc/netsh
output) and collected into one snapshot dict so the rules are testable."""

import json
import os
import re
import shutil
import subprocess
import time

from .. import config, core, testrun, updates
from .base import BLOCKING_CONFLICTS, CONFLICTS, Backend, Check, ConflictError, Status

SERVICE = "ZapretHub"
NO_WINDOW = 0x08000000
FLOWSEAL = "https://github.com/Flowseal/zapret-discord-youtube"


# Everything Flowseal strategies use; no spaces, quotes or shell metacharacters.
ARG_RE = re.compile(r"^[A-Za-z0-9!+,\-.:=\\_/~@]+$")


def service_cmd(exe, args):
    """binPath value for the service. The service runs as LocalSystem and
    sc.exe re-parses this string, so only plain characters are allowed."""
    for a in args:
        if not ARG_RE.match(a):
            raise ValueError(f"недопустимые символы в аргументе стратегии: {a}")
    return f'"{exe}" ' + " ".join(args)


def sc_create_line(binpath, auto):
    inner = binpath.replace('"', '\\"')
    return (f'sc create {SERVICE} binPath= "{inner}" DisplayName= "Zapret Hub" '
            f'start= {"auto" if auto else "demand"}')


# Protected DACL for DATA_DIR: admins and SYSTEM full, users read/execute,
# nothing inherited from ProgramData (where any user may create folders).
SECURE_SDDL = "D:P(A;OICI;FA;;;BA)(A;OICI;FA;;;SY)(A;OICI;0x1200a9;;;BU)"
READ_ONLY_RIGHTS = {"FR", "GR", "GRGX", "FRFX", "GXGR", "0x1200a9", "0x1200a0", "0x120089"}
TRUSTED_SIDS = {"BA", "SY", "S-1-5-32-544", "S-1-5-18"}
ACE_RE = re.compile(r"\(([^)]*)\)")


def sddl_trusted(sddl):
    """True when only admins/SYSTEM own and can write the folder and its
    DACL does not inherit from the parent."""
    m = re.match(r"^O:([^:]+?)(?:G:[^:]+?)?D:([A-Z]*)\(", sddl or "")
    if not m or m.group(1) not in TRUSTED_SIDS or "P" not in m.group(2):
        return False
    dacl = sddl[sddl.index("D:"):]
    for ace in ACE_RE.findall(dacl):
        parts = ace.split(";")
        if len(parts) < 6:
            return False
        kind, flags, rights, sid = parts[0], parts[1], parts[2], parts[5]
        if kind != "A" or sid in TRUSTED_SIDS:
            continue
        if "IO" in flags and sid == "CO":
            return False
        if rights not in READ_ONLY_RIGHTS:
            return False
    return True


def is_link(path):
    """Symlink or NTFS junction (reparse point)."""
    return os.path.islink(path) or (hasattr(os.path, "isjunction") and os.path.isjunction(path))


# ---------------------------------------------------------------- rules

def _svc(snap, name):
    return next((s for s in snap["services"] if s["name"].lower() == name.lower()), None)


def _running(snap, name):
    s = _svc(snap, name)
    return bool(s) and s["status"] in ("running", "start_pending", "stop_pending")


def conflicts(snap):
    out = []
    if _running(snap, "zapret"):
        out.append("flowseal_service")
    if any(s["name"].lower().startswith("goodbyedpi") and s["status"] == "running" for s in snap["services"]):
        out.append("goodbyedpi")
    ours = _svc(snap, SERVICE)
    our_pid = ours["pid"] if ours and ours["status"] == "running" else None
    winws = [pid for pid, name in snap["processes"] if name.lower() == "winws.exe"]
    flowseal_pid = (_svc(snap, "zapret") or {}).get("pid")
    if [p for p in winws if p not in (our_pid, flowseal_pid)]:
        out.append("stray_winws")
    if not winws and _running(snap, "WinDivert"):
        out.append("windivert_stale")
    return out


def _find(snap, *words):
    """Services whose name or display name contains every word."""
    hits = []
    for s in snap["services"]:
        text = f'{s["name"]} {s["display_name"]}'.lower()
        if all(w.lower() in text for w in words):
            hits.append(s["display_name"] or s["name"])
    return hits


def evaluate(snap):
    checks = []

    def add(cid, bad, level, title_ok, title_bad, detail="", fixable=False, fix_label="Исправить"):
        if bad:
            checks.append(Check(cid, level, title_bad, detail, fixable, fix_label))
        else:
            checks.append(Check(cid, "ok", title_ok))

    add("bfe", not _running(snap, "BFE"), "error", "Служба BFE работает",
        "Не работает служба Base Filtering Engine (BFE)",
        "Без неё WinDivert не запускается. Включим её и поставим автозапуск.", True, "Включить BFE")
    enabled, server = snap["proxy"]
    add("proxy", enabled, "warn", "Системный прокси выключен", "Включён системный прокси",
        f"Прокси: {server}. Если ты им не пользуешься — выключи в Параметры → Сеть → Прокси.")
    add("tcp_timestamps", snap["tcp_timestamps"] is False, "warn", "TCP timestamps включены",
        "Выключены TCP timestamps", "Многие стратегии Flowseal без них не работают.", True, "Включить")
    procs = {name.lower() for _, name in snap["processes"]}
    add("adguard", "adguardsvc.exe" in procs, "error", "Adguard не мешает", "Найден Adguard",
        "Adguard часто ломает Discord вместе с zapret. Выключи его или добавь Discord в исключения.")
    for cid, words, name in (("killer", ("killer",), "Killer"),
                             ("intel", ("intel", "connectivity", "network"), "Intel Connectivity Network Service"),
                             ("checkpoint", ("tracsrvwrapper",), "Check Point"),
                             ("smartbyte", ("smartbyte",), "SmartByte")):
        hits = _find(snap, *words)
        if cid == "checkpoint":
            hits += _find(snap, "epwd")
        add(cid, bool(hits), "error", f"{name} не мешает", f"Найден {name}",
            f"{name} конфликтует с zapret. Удали его или отключи его службы в services.msc.")
    vpn = [s["display_name"] or s["name"] for s in snap["services"]
           if "vpn" in f'{s["name"]} {s["display_name"]}'.lower() and s["status"] == "running"]
    add("vpn", bool(vpn), "warn", "VPN не мешает", "Работают службы VPN",
        "Найдены: " + ", ".join(vpn) + ". Включённый VPN может мешать zapret — выключи его на время.")
    add("doh", not snap["doh"], "warn", "Безопасный DNS настроен", "Не настроен безопасный DNS",
        "Провайдер может подменять адреса сайтов. Включи «DNS через HTTPS» в браузере "
        "(Настройки → Конфиденциальность) или в Windows 11: Параметры → Сеть → DNS.")
    hosts = snap["hosts"].lower()
    yt = any(("youtube.com" in l or "youtu.be" in l) and not l.lstrip().startswith("#") for l in hosts.splitlines())
    add("hosts", yt, "warn", "Файл hosts в порядке", "В hosts есть записи YouTube",
        "Они могут мешать YouTube. Удали их из C:\\Windows\\System32\\drivers\\etc\\hosts.")
    if snap.get("installed", True):
        add("windivert_files", not snap["windivert_files"], "error", "Файлы WinDivert на месте",
            "Нет файлов WinDivert", "Их мог удалить антивирус. Добавь папку C:\\ProgramData\\ZapretHub в исключения "
            "и нажми «Переустановить».", True, "Переустановить")
    else:
        checks.append(Check("installed", "warn", "Обход ещё не установлен",
                            "Нажми большую кнопку на Главной или «Установить» здесь — программа скачает стратегии "
                            "Flowseal.", True, "Установить"))
    for cid in conflicts(snap):
        title, detail, label = CONFLICTS[cid]
        checks.append(Check(cid, "error" if cid in BLOCKING_CONFLICTS else "warn", title, detail, True, label))
    return checks


# ---------------------------------------------------------------- system access

class WinSys:
    """Thin layer over the real Windows; tests replace it."""

    def run(self, cmd):
        # never through cmd.exe: a str goes to CreateProcess as the command line as-is
        r = subprocess.run(cmd, capture_output=True, creationflags=NO_WINDOW)
        out = (r.stdout + r.stderr).decode("oem", "replace") if config.IS_WINDOWS else ""
        return r.returncode, out.strip()

    def services(self):
        import psutil
        # status()/pid() only: as_dict() also reads the service config, which
        # fails (WinError 1734) for our long winws command line
        out = []
        for s in psutil.win_service_iter():
            try:
                out.append({"name": s.name(), "display_name": s.display_name() or "",
                            "status": s.status() or "", "pid": s.pid() or 0})
            except Exception:  # noqa: BLE001 - services vanish / deny access
                continue
        return out

    def processes(self):
        import psutil
        return [(p.info["pid"], p.info["name"] or "") for p in psutil.process_iter(["pid", "name"])]

    def proxy(self):
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings") as k:
                enabled = winreg.QueryValueEx(k, "ProxyEnable")[0] == 1
                server = winreg.QueryValueEx(k, "ProxyServer")[0] if enabled else ""
                return enabled, server
        except OSError:
            return False, ""

    def tcp_timestamps(self):
        rc, out = self.run(["powershell", "-NoProfile", "-Command",
                            "(Get-NetTCPSetting -SettingName Internet).Timestamps"])
        if rc or not out:
            return None
        return out.strip().lower() != "disabled"

    def doh(self):
        import winreg
        base = r"SYSTEM\CurrentControlSet\Services\Dnscache\InterfaceSpecificParameters"
        try:
            root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
        except OSError:
            return False
        stack = [(root, base)]
        while stack:
            key, path = stack.pop()
            try:
                if winreg.QueryValueEx(key, "DohFlags")[0] > 0:
                    return True
            except OSError:
                pass
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(key, i)
                except OSError:
                    break
                try:
                    stack.append((winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, f"{path}\\{sub}"), f"{path}\\{sub}"))
                except OSError:
                    pass
                i += 1
        return False

    def hosts(self):
        try:
            with open(config.HOSTS_FILE, encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError:
            return ""

    def sddl(self, path):
        lit = path.replace("'", "''")
        rc, out = self.run(["powershell", "-NoProfile", "-Command", f"(Get-Acl -LiteralPath '{lit}').Sddl"])
        return out.strip() if rc == 0 and out.strip() else None   # None: could not check

    def create_secure_dir(self, path):
        """CreateDirectoryW with SECURE_SDDL: no moment where the folder exists unprotected."""
        import ctypes
        from ctypes import wintypes
        advapi = ctypes.WinDLL("advapi32", use_last_error=True)
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)

        class SA(ctypes.Structure):
            _fields_ = [("nLength", wintypes.DWORD), ("lpSecurityDescriptor", ctypes.c_void_p),
                        ("bInheritHandle", wintypes.BOOL)]
        sd = ctypes.c_void_p()
        if not advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW(SECURE_SDDL, 1, ctypes.byref(sd), None):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            sa = SA(ctypes.sizeof(SA), sd, False)
            if not k32.CreateDirectoryW(path, ctypes.byref(sa)):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            k32.LocalFree(sd)

    def snapshot(self, full=True):
        snap = {"services": self.services(), "processes": self.processes()}
        if full:
            snap.update(proxy=self.proxy(), tcp_timestamps=self.tcp_timestamps(), doh=self.doh(),
                        hosts=self.hosts(),
                        windivert_files=all(os.path.exists(os.path.join(config.BIN_DIR, f))
                                            for f in ("WinDivert.dll", "WinDivert64.sys")))
        return snap


# ---------------------------------------------------------------- backend

class WindowsBackend(Backend):
    def __init__(self, system=None):
        self.sys = system or WinSys()

    def is_installed(self):
        return os.path.isfile(config.WINWS) and os.path.isdir(config.BUILTIN_DIR)

    def _service(self):
        return _svc({"services": self.sys.services()}, SERVICE)

    def _save_state(self, st):
        updates.write_file(config.STATE_FILE, json.dumps(st, indent=2, ensure_ascii=False))

    def secure(self, log):
        """Make sure DATA_DIR is ours before anything runs as SYSTEM from it.
        A folder made by someone else (or a link) is moved aside and deleted.
        Checked on every call: uninstall or another admin may have removed it."""
        d = config.DATA_DIR

        def acl(path):
            sd = self.sys.sddl(path)
            if sd is None:   # never delete anything on a failed check
                raise RuntimeError(f"Не удалось проверить права папки {path} (PowerShell недоступен?). "
                                   "Запусти программу ещё раз.")
            return sd
        if os.path.lexists(d):
            link = is_link(d)
            if link or not sddl_trusted(acl(d)):
                log("Папку данных создал не администратор — пересоздаю её")
                aside = f"{d}.untrusted-{int(time.time())}"
                os.rename(d, aside)
                if os.path.islink(aside):
                    os.unlink(aside)
                elif link:
                    os.rmdir(aside)   # a junction: removes the link, not its target
                else:
                    shutil.rmtree(aside, ignore_errors=True)
        if not os.path.lexists(d):
            os.makedirs(os.path.dirname(d), exist_ok=True)
            self.sys.create_secure_dir(d)   # fails if someone recreated it meanwhile
        if is_link(d) or not sddl_trusted(acl(d)):
            raise RuntimeError(f"Не удалось защитить папку {d} — запусти программу от администратора.")

    def status(self):
        snap = self.sys.snapshot(full=False)
        st = self.state()
        ours = _svc(snap, SERVICE)
        return Status(installed=self.is_installed(), running=bool(ours) and ours["status"] == "running",
                      autostart=st["autostart"], strategy=st["strategy"], game_filter=st["game_filter"],
                      ipset=st["ipset"], versions=self.versions(), conflicts=conflicts(snap))

    # ------------------------------------------------------------ install
    def install(self, log):
        was_running = bool(self._service()) and self._service()["status"] == "running"
        if was_running:
            log("Останавливаю обход на время обновления…")
            self.stop(log)
        self.secure(log)
        versions = self.versions()
        tag = updates.install_flowseal(config.FLOWSEAL_DIR, log, windows=True)
        versions["flowseal"] = tag
        updates.convert_builtin(config.FLOWSEAL_DIR, config.BUILTIN_DIR, log)
        updates.setup_lists(config.FLOWSEAL_DIR, config.LISTS_DIR, self.state()["ipset"], config.IPSET_FULL)
        updates.install_targets(config.FLOWSEAL_DIR, config.TARGETS_FILE)
        os.makedirs(config.CUSTOM_DIR, exist_ok=True)
        if not os.path.exists(config.STATE_FILE):
            self._save_state(dict(core.DEFAULT_STATE))
        updates.write_file(config.VERSIONS_FILE, json.dumps(versions, indent=2))
        if was_running:
            self.start(log)
        log(f"Готово: стратегии Flowseal {tag}")

    # ------------------------------------------------------------ run
    def _args(self, name=None, game=None, st=None):
        st = st or self.state()
        name = name or st["strategy"]
        path = core.strategy_path(name, config.BUILTIN_DIR, config.CUSTOM_DIR)
        if not os.path.exists(path):
            raise RuntimeError(f"Стратегия «{name}» не найдена — выбери другую.")
        with open(path, encoding="utf-8") as f:
            args, _, _ = core.build(f.read(), game or st["game_filter"], config.BIN_DIR, config.LISTS_DIR,
                                    keep_wf=True)
        return args

    def _wait(self, want, seconds=8):
        end = time.time() + seconds
        while time.time() < end:
            s = self._service()
            if (s["status"] if s else "absent") == want:
                return True
            time.sleep(0.3)
        return False

    def _clean_windivert(self):
        if not any(n.lower() == "winws.exe" for _, n in self.sys.processes()):
            self.sys.run(["sc", "stop", "WinDivert"])
            self.sys.run(["sc", "delete", "WinDivert"])

    def start(self, log):
        self.secure(log)
        if not self.is_installed():
            raise RuntimeError("Сначала нажми «Установить».")
        found = conflicts(self.sys.snapshot(full=False))
        blocking = [c for c in found if c in BLOCKING_CONFLICTS]
        if blocking:
            raise ConflictError(blocking)
        if "windivert_stale" in found:
            self.fix("windivert_stale", log)
        self.sys.run(["netsh", "interface", "tcp", "set", "global", "timestamps=enabled"])
        binpath = service_cmd(config.WINWS, self._args())
        if self._service():
            self.sys.run(["sc", "stop", SERVICE])
            self._wait("stopped", 5)
            self.sys.run(["sc", "delete", SERVICE])
            self._wait("absent", 5)
        log(f"Запускаю стратегию «{self.state()['strategy']}»…")
        rc, out = self.sys.run(sc_create_line(binpath, self.state()["autostart"]))
        if rc:
            raise RuntimeError(f"Не удалось создать службу: {out}")
        self.sys.run(["sc", "description", SERVICE, "Обход блокировок Discord и YouTube (zapret, стратегии Flowseal)"])
        rc, out = self.sys.run(["sc", "start", SERVICE])
        if rc or not self._wait("running", 10):
            self.sys.run(["sc", "stop", SERVICE])
            self.sys.run(["sc", "delete", SERVICE])
            raise RuntimeError("winws.exe не запустился. Попробуй другую стратегию или открой «Диагностику»."
                               + (f"\n\n{out}" if rc and out else ""))
        log("Обход включён")

    def stop(self, log):
        if self._service():
            self.sys.run(["sc", "stop", SERVICE])
            self._wait("stopped", 8)
            self.sys.run(["sc", "delete", SERVICE])
            self._wait("absent", 5)
        self._clean_windivert()
        log("Обход выключен")

    def _running(self):
        s = self._service()
        return bool(s) and s["status"] == "running"

    def _restart_if_running(self, log):
        if self._running():
            self.start(log)

    def set_autostart(self, on, log):
        self.secure(log)
        st = self.state()
        st["autostart"] = bool(on)
        self._save_state(st)
        if self._service():
            self.sys.run(["sc", "config", SERVICE, "start=", "auto" if on else "demand"])
        log("Автозапуск " + ("включён" if on else "выключен"))

    def set_state(self, changes, log):
        self.secure(log)
        st = self.state()
        if "strategy" in changes:
            if not core.valid_name(changes["strategy"]) or not os.path.exists(
                    core.strategy_path(changes["strategy"], config.BUILTIN_DIR, config.CUSTOM_DIR)):
                raise RuntimeError("Нет такой стратегии")
            st["strategy"] = changes["strategy"]
        if "game_filter" in changes:
            if changes["game_filter"] not in core.GAME_FILTER_MODES:
                raise RuntimeError("Неверный режим игрового фильтра")
            st["game_filter"] = changes["game_filter"]
        if "ipset" in changes:
            if changes["ipset"] not in core.IPSET_MODES:
                raise RuntimeError("Неверный режим IPSet")
            st["ipset"] = changes["ipset"]
            updates.apply_ipset_mode(config.LISTS_DIR, st["ipset"], config.IPSET_FULL)
        try:
            self._args(st=st)   # validate the new combination before it is saved
        except ValueError as e:
            raise RuntimeError(f"Стратегия не подходит: {e}") from e
        self._save_state(st)
        self._restart_if_running(log)

    def write_list(self, name, text, log):
        self.secure(log)
        if name not in core.USER_LISTS:
            raise RuntimeError("Этот список менять нельзя")
        updates.write_file(os.path.join(config.LISTS_DIR, name), core.clean_list(name, text))
        self._restart_if_running(log)
        log("Список сохранён")

    def ipset_update(self, log):
        self.secure(log)
        log("Скачиваю список IPSet от Flowseal…")
        text = updates.fetch_ipset()
        updates.write_file(config.IPSET_FULL, text)
        log(f"Адресов в списке: {text.count(chr(10))}")
        if self.state()["ipset"] == "loaded":
            updates.apply_ipset_mode(config.LISTS_DIR, "loaded", config.IPSET_FULL)
            self._restart_if_running(log)

    def hosts(self, action, log):
        block = ""
        if action == "update":
            log("Скачиваю hosts от Flowseal…")
            block = updates.fetch_hosts()
        cur = self.sys.hosts()
        shutil.copy(config.HOSTS_FILE, config.HOSTS_FILE + ".zapret-hub.bak")
        with open(config.HOSTS_FILE, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(core.hosts_block_replace(cur, block))
        self.sys.run(["ipconfig", "/flushdns"])
        log("hosts обновлён" if block else "Записи убраны из hosts")

    # ------------------------------------------------------------ tests
    def run_tests(self, names, on_event, cancel, timeout=4):
        self.secure(lambda m: None)
        if not self.is_installed():
            raise RuntimeError("Сначала нажми «Установить».")
        try:
            with open(config.TARGETS_FILE, encoding="utf-8") as f:
                targets = core.parse_targets(f.read())
        except OSError:
            targets = []
        if not targets:
            raise RuntimeError("Нет целей для теста (targets.txt) — нажми «Обновить».")
        was_running = self._running()
        if was_running:
            self.stop(lambda m: None)
        proc = {}

        def start(name):
            p = subprocess.Popen([config.WINWS] + self._args(name), cwd=config.BIN_DIR, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.PIPE, creationflags=NO_WINDOW)
            time.sleep(1.5)
            if p.poll() is not None:
                err = (p.stderr.read() or b"").decode("oem" if config.IS_WINDOWS else "utf-8", "replace").strip()
                raise RuntimeError(err.splitlines()[-1] if err else "winws.exe завершился")
            proc["p"] = p

        def stop():
            p = proc.pop("p", None)
            if p and p.poll() is None:
                p.kill()
                p.wait(5)

        try:
            res = testrun.run(names, start, stop, targets, on_event, cancel, timeout)
            updates.write_file(config.RESULTS_FILE, json.dumps(testrun.merge(self.results(), res),
                                                                    ensure_ascii=False, indent=1))
        finally:
            stop()
            if was_running:
                self.start(lambda m: None)
            else:
                self._clean_windivert()
        return res

    # ------------------------------------------------------------ diagnostics
    def diagnostics(self):
        snap = self.sys.snapshot()
        snap["installed"] = self.is_installed()
        return evaluate(snap)

    def fix(self, check_id, log):
        run = self.sys.run
        if check_id == "bfe":
            run(["sc", "config", "BFE", "start=", "auto"])
            run(["sc", "start", "BFE"])
        elif check_id == "tcp_timestamps":
            run(["netsh", "interface", "tcp", "set", "global", "timestamps=enabled"])
        elif check_id == "flowseal_service":
            run(["sc", "stop", "zapret"])
            time.sleep(1)
            run(["sc", "delete", "zapret"])
        elif check_id == "goodbyedpi":
            for s in self.sys.services():
                if s["name"].lower().startswith("goodbyedpi"):
                    run(["sc", "stop", s["name"]])
                    run(["sc", "config", s["name"], "start=", "disabled"])
        elif check_id == "stray_winws":
            ours = self._service()
            our_pid = ours["pid"] if ours and ours["status"] == "running" else None
            for pid, name in self.sys.processes():
                if name.lower() == "winws.exe" and pid != our_pid:
                    run(["taskkill", "/PID", str(pid), "/F"])
        elif check_id == "windivert_stale":
            self._clean_windivert()
        elif check_id in ("windivert_files", "installed"):
            self.install(log)
        else:
            raise RuntimeError("Это нужно исправить вручную — смотри подсказку.")
        log("Готово")

    def uninstall(self, log):
        self.stop(log)
        cur = self.sys.hosts()
        if core.HOSTS_BEGIN in cur:
            with open(config.HOSTS_FILE, "w", encoding="utf-8", newline="\r\n") as f:
                f.write(core.hosts_block_replace(cur, ""))
        shutil.rmtree(config.DATA_DIR, ignore_errors=True)
        log("Файлы zapret удалены")

