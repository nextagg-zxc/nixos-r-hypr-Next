"""Самопроверка малых программ в изолированном Wayland: шпаргалка, «Сообщить о проблеме», окно запуска .exe.
Печатает SELFTEST PASS / FAIL; снимки — $NEWBIE_SHOT-<шаг>.png. Команды подменены, HOME временный."""
from __future__ import annotations

import os
import shutil
import tarfile
import tempfile
from pathlib import Path

from gi.repository import GLib, Gtk

from . import apps, report


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="newbie-selftest-"))
    (root / "home").mkdir()
    (root / "bin").mkdir()
    log = root / "calls.log"
    for name in ("umu-run", "wine"):
        f = root / "bin" / name
        f.write_text(f"#!/usr/bin/env bash\necho \"{name} $*\" >>{log}\n")
        f.chmod(0o755)
    os.environ.update(HOME=str(root / "home"), XDG_CONFIG_HOME=str(root / "home/.config"),
                      PATH=f"{root / 'bin'}:{os.environ['PATH']}", NIXOS_SHARE_ETC=str(root / "none"))
    report.COMMANDS[:] = [("journal.txt", ["echo", f"/home/{os.environ.get('USER', 'x')}/a password=hunter2"])]
    exe = root / "home/setup.exe"
    exe.write_bytes(b"MZ\x90\x00" + b"\x00" * 64)
    result = {"ok": True, "msg": ""}

    def shot(win, name):
        p = os.environ.get("NEWBIE_SHOT")
        if not p:
            return
        paintable = Gtk.WidgetPaintable(widget=win)
        snap = Gtk.Snapshot()
        paintable.snapshot(snap, win.get_width(), win.get_height())
        win.get_renderer().render_texture(snap.to_node(), None).save_to_png(f"{p}-{name}.png")

    def drive(steps):
        def on_window(win):
            it = steps(win)

            def tick():
                try:
                    next(it)
                    return True
                except StopIteration:
                    pass
                except Exception as err:  # noqa: BLE001
                    result.update(ok=False, msg=f"{type(err).__name__}: {err}")
                win.get_application().quit()
                return False
            GLib.timeout_add(300, tick)
        return on_window

    def check(c, m):
        if not c:
            raise AssertionError(m)

    def keys_steps(win):
        yield
        yield
        shot(win, "keys")
        check(win.get_width() > 300, "шпаргалка не показалась")

    def report_steps(win):
        yield
        shot(win, "report")
        win.report_btn.emit("clicked")
        for _ in range(30):
            yield
            if getattr(win, "report_path", None):
                break
        yield
        shot(win, "report-done")
        p = getattr(win, "report_path", None)
        check(p and p.exists(), "архив не создан")
        with tarfile.open(p) as t:
            text = "".join(t.extractfile(m).read().decode() for m in t.getmembers() if m.isfile())
        check("hunter2" not in text and "<скрыто>" in text, "пароль не вычищен")

    def exe_steps(win):
        yield
        yield
        shot(win, "exe")
        win.remember.set_active(True)
        win.how_buttons["proton"].emit("clicked")

    apps.keys(on_window=drive(keys_steps))
    if result["ok"]:
        apps.report(on_window=drive(report_steps))
    if result["ok"]:
        apps.run_exe(str(exe), on_window=drive(exe_steps))
        import time
        for _ in range(20):
            if log.exists() and "umu-run" in log.read_text():
                break
            time.sleep(0.2)
        if not (log.exists() and f"umu-run {exe}" in log.read_text()):
            result.update(ok=False, msg="Proton не запущен")
        elif apps.logic.remembered(root / "home/.config/nixos-run-exe/choices.json", str(exe)) != "proton":
            result.update(ok=False, msg="выбор не запомнен")
        else:
            # второй запуск — без окна, сразу запомненным способом
            log.write_text("")
            apps.run_exe(str(exe))
            if f"umu-run {exe}" not in log.read_text():
                result.update(ok=False, msg="запомненный выбор не применён")
    shutil.rmtree(root, ignore_errors=True)
    print("SELFTEST PASS" if result["ok"] else f"SELFTEST FAIL: {result['msg']}", flush=True)
    return 0 if result["ok"] else 1
