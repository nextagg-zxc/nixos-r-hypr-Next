"""Linux: the GUI runs as the user and reads /opt/zapret-hub directly; every
change goes through the root helper via pkexec. Helper output is plain log
lines plus '@@{json}' events; closing its stdin cancels long operations.

Inside an AppImage the root side (helper, unit, polkit action) cannot run
from the FUSE mount, so the first privileged action installs it into
/usr/lib/zapret-hub with install.sh --system, and again whenever the bundled
copy's fingerprint differs from the installed one."""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import threading

from .. import config, core
from .base import BLOCKING_CONFLICTS, CONFLICTS, Backend, Check, ConflictError, Status

SERVICE = "zapret-hub.service"
INSTALLED_ROOT = "/usr/lib/zapret-hub"
INSTALLED_HELPER = INSTALLED_ROOT + "/zapret-hub-helper"
SOURCE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
DEV_HELPER = os.path.join(SOURCE_ROOT, "packaging", "linux", "zapret-hub-helper")
SYSTEM_PACKAGING = ["install.sh", "zapret-hub-helper", "zapret-hub.service", "org.zaprethub.helper.policy"]
CONFLICT_UNITS = {"zapret_gui": "zapret-gui.service", "zapret_service": "zapret.service"}


def parse_helper_line(line):
    line = line.rstrip("\n")
    if line.startswith("@@"):
        try:
            return "event", json.loads(line[2:])
        except ValueError:
            pass
    return "log", line


def unit_active(unit):
    return subprocess.run(["systemctl", "is-active", "--quiet", unit]).returncode == 0


def conflicts(is_active=unit_active):
    return [cid for cid, unit in CONFLICT_UNITS.items() if is_active(unit)]


# ---------------------------------------------------------------- AppImage

def fingerprint(root):
    """SHA-256 of what runs as root: the package without the GUI, plus the
    helper, unit, policy and installer."""
    files = []
    pkg = os.path.join(root, "zaprethub")
    for d, dirs, names in os.walk(pkg):
        rel = os.path.relpath(d, pkg)
        dirs[:] = sorted(x for x in dirs if x != "__pycache__" and not (rel == "." and x == "ui"))
        files += [os.path.join(d, n) for n in sorted(names) if n.endswith(".py")]
    files += [os.path.join(root, "packaging", "linux", n) for n in SYSTEM_PACKAGING]
    h = hashlib.sha256()
    for f in files:
        h.update(os.path.relpath(f, root).encode() + b"\0")
        with open(f, "rb") as fh:
            h.update(fh.read() + b"\0")
    return h.hexdigest()


def appimage_bundle(root=SOURCE_ROOT):
    """The bundled source root when running from an AppImage, else None."""
    if os.environ.get("APPIMAGE") and os.path.isfile(os.path.join(root, "packaging", "linux", "install.sh")):
        return root
    return None


def _data_home():
    return os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")


def integrate_desktop(appimage, data_home=None):
    """Menu entry and icon for the AppImage (the user's own copy, no root)."""
    data_home = data_home or _data_home()
    icon = os.path.join(data_home, "icons", "hicolor", "scalable", "apps", "zapret-hub.svg")
    os.makedirs(os.path.dirname(icon), exist_ok=True)
    shutil.copyfile(os.path.join(SOURCE_ROOT, "zaprethub", "ui", "assets", "icon.svg"), icon)
    entry = os.path.join(data_home, "applications", "zapret-hub.desktop")
    os.makedirs(os.path.dirname(entry), exist_ok=True)
    text = ("[Desktop Entry]\nType=Application\nName=Zapret Hub\n"
            "Comment=Обход блокировок Discord и YouTube, прокси для Telegram\n"
            f'Exec="{appimage}"\nIcon=zapret-hub\nTerminal=false\nCategories=Network;\n'
            "StartupWMClass=zapret-hub\n")
    tmp = entry + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, entry)


def remove_desktop(data_home=None):
    data_home = data_home or _data_home()
    for p in (os.path.join(data_home, "applications", "zapret-hub.desktop"),
              os.path.join(data_home, "icons", "hicolor", "scalable", "apps", "zapret-hub.svg")):
        if os.path.exists(p):
            os.remove(p)


class LinuxBackend(Backend):
    needs_admin_prompt = True

    def __init__(self, prefix=None, bundle=None, installed_root=INSTALLED_ROOT, setup_prefix=("pkexec", "/bin/bash")):
        if prefix is None:
            bundle = appimage_bundle()
            # the AppImage's own copy sits on a FUSE mount root cannot read
            helper = INSTALLED_HELPER if bundle or os.path.exists(INSTALLED_HELPER) else DEV_HELPER
            # пакет NixOS: помощник в хранилище Nix (его путь — в правиле polkit этого пакета)
            helper = os.environ.get("ZAPRETHUB_HELPER") or helper
            prefix = ["pkexec", helper]
        self.prefix = prefix
        self.bundle = bundle
        self.installed_root = installed_root
        self.setup_prefix = list(setup_prefix)
        self.setup_args = ["--system"]
        self._fingerprint = None

    # ------------------------------------------------------------ system part (AppImage)
    def needs_setup(self):
        if not self.bundle:
            return False
        if self._fingerprint is None:
            self._fingerprint = fingerprint(self.bundle)
        try:
            with open(os.path.join(self.installed_root, "FINGERPRINT")) as f:
                return f.read().strip() != self._fingerprint
        except OSError:
            return True

    def setup(self, log):
        """Copy the root side out of the AppImage and install it (one password prompt)."""
        log("Ставлю системную часть: службу и права администратора для zapret")
        stage = tempfile.mkdtemp(prefix="zapret-hub-setup-")
        try:
            shutil.copytree(os.path.join(self.bundle, "zaprethub"), os.path.join(stage, "zaprethub"),
                            ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(os.path.join(self.bundle, "packaging", "linux"), os.path.join(stage, "packaging", "linux"))
            with open(os.path.join(stage, "FINGERPRINT"), "w") as f:
                f.write(fingerprint(self.bundle) + "\n")
            self._run(self.setup_prefix + [os.path.join(stage, "packaging", "linux", "install.sh")] + self.setup_args,
                      log)
        finally:
            shutil.rmtree(stage, ignore_errors=True)
        if self.needs_setup():
            raise RuntimeError("Системная часть не установилась — смотри журнал выше.")

    # ------------------------------------------------------------ helper call
    def call(self, args, log, on_event=None, stdin_text=None, cancel=None):
        if self.needs_setup():
            self.setup(log)
        self._run(self.prefix + args, log, on_event, stdin_text, cancel)

    def _run(self, argv, log, on_event=None, stdin_text=None, cancel=None):
        p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1)
        if stdin_text is not None:
            p.stdin.write(stdin_text)
            p.stdin.close()
        elif cancel is not None:
            def closer():
                cancel.wait()
                try:
                    p.stdin.close()
                except OSError:
                    pass
            threading.Thread(target=closer, daemon=True).start()
        else:
            p.stdin.close()
        errors, tail = [], []
        for line in p.stdout:
            kind, val = parse_helper_line(line)
            if kind == "event":
                if on_event:
                    on_event(val)
                continue
            if val.startswith("ОШИБКА: "):
                errors.append(val[len("ОШИБКА: "):])
                continue
            tail = (tail + [val])[-5:]
            log(val)
        p.stdout.close()
        rc = p.wait()
        if cancel is not None and not cancel.is_set():
            cancel.set()   # release the closer thread
        if rc in (126, 127) and not errors:
            raise RuntimeError("Нужен пароль администратора — действие отменено.")
        if rc:
            raise RuntimeError(errors[-1] if errors else ("\n".join(tail) or f"helper завершился с кодом {rc}"))

    # ------------------------------------------------------------ status
    def is_installed(self):
        return os.access(config.nfqws(), os.X_OK) and os.path.isdir(config.BUILTIN_DIR)

    def status(self):
        st = self.state()
        return Status(installed=self.is_installed(), running=unit_active(SERVICE), autostart=st["autostart"],
                      strategy=st["strategy"], game_filter=st["game_filter"], ipset=st["ipset"],
                      versions=self.versions(), conflicts=conflicts())

    # ------------------------------------------------------------ changes
    def install(self, log):
        self.call(["install"], log, cancel=threading.Event())

    def start(self, log):
        blocking = [c for c in conflicts() if c in BLOCKING_CONFLICTS]
        if blocking:
            raise ConflictError(blocking)
        self.call(["service", "start"], log)

    def stop(self, log):
        self.call(["service", "stop"], log)

    def set_autostart(self, on, log):
        self.call(["set-state"], log, stdin_text=json.dumps({"autostart": bool(on)}))

    def set_state(self, changes, log):
        self.call(["set-state"], log, stdin_text=json.dumps(changes))

    def write_list(self, name, text, log):
        self.call(["write-list", name], log, stdin_text=text)

    def ipset_update(self, log):
        self.call(["ipset-update"], log)

    def hosts(self, action, log):
        self.call(["hosts", action], log)

    def run_tests(self, names, on_event, cancel, timeout=4):
        self.call(["test", "--strategies", "|".join(names), "--timeout", str(timeout)],
                  lambda m: on_event({"type": "log", "text": m}), on_event=on_event, cancel=cancel)
        return self.results()

    def diagnostics(self):
        checks = []
        if self.bundle:
            checks.append(Check("system", "warn", "Системная часть ещё не установлена",
                                "Поставится сама при первом включении: система один раз спросит пароль.",
                                True, "Установить") if self.needs_setup() else
                          Check("system", "ok", "Системная часть установлена"))
        nft = shutil.which("nft") or os.path.exists("/usr/sbin/nft")
        checks.append(Check("nft", "ok", "nftables установлен") if nft else
                      Check("nft", "error", "Не найден nftables", "Установи пакет nftables (install.sh ставит его сам)."))
        if self.is_installed():
            checks.append(Check("nfqws", "ok", "zapret (nfqws) установлен"))
        else:
            checks.append(Check("nfqws", "error", "zapret не установлен", "Нажми «Установить».", True, "Установить"))
        failed = subprocess.run(["systemctl", "is-failed", "--quiet", SERVICE]).returncode == 0
        if failed:
            jr = subprocess.run(["journalctl", "-u", SERVICE, "-n", "8", "--no-pager", "-o", "cat"],
                                capture_output=True, text=True)
            checks.append(Check("service_failed", "error", "Служба zapret-hub упала",
                                (jr.stdout.strip() or "Журнал пуст") + "\n\nПопробуй другую стратегию.", False))
        else:
            checks.append(Check("service_failed", "ok", "Служба без ошибок"))
        if os.path.exists("/etc/hosts"):
            with open("/etc/hosts", encoding="utf-8", errors="replace") as f:
                yt = [l for l in f if "youtube" in l.lower() and not l.lstrip().startswith("#")
                      and core.HOSTS_BEGIN not in l]
            checks.append(Check("hosts", "warn", "В /etc/hosts есть записи YouTube",
                                "Они могут мешать YouTube.") if yt else Check("hosts", "ok", "Файл hosts в порядке"))
        for cid in conflicts():
            title, detail, label = CONFLICTS[cid]
            checks.append(Check(cid, "error", title, detail, True, label))
        return checks

    def fix(self, check_id, log):
        if check_id == "system":
            return self.setup(log)
        if check_id == "nfqws":
            return self.install(log)
        if check_id not in CONFLICT_UNITS:
            raise RuntimeError("Это нужно исправить вручную — смотри подсказку.")
        self.call(["fix", check_id], log)

    def uninstall(self, log):
        if not self.bundle:
            return self.call(["uninstall"], log)
        # AppImage: also remove the root side, so deleting the file leaves nothing behind
        if os.path.exists(os.path.join(self.installed_root, "zapret-hub-helper")):
            self.call(["uninstall", "--system"], log)
        remove_desktop()
