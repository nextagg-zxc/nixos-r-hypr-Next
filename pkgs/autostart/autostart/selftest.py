"""Самопроверка окна: python3 -m autostart --selftest
Во временной папке (своя XDG_CONFIG_HOME/DIRS и XDG_DATA_*) открывает окно и через те же виджеты,
что и человек, выключает системную запись, добавляет приложение (скрыто, задержка 5, только KDE),
добавляет и убирает свою команду; проверяет файлы через model. Снимок окна — в $AUTOSTART_SHOT.
Печатает SELFTEST PASS / SELFTEST FAIL: … и выходит с 0/1.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path


def fixture(root: Path) -> None:
    (root / "home/autostart").mkdir(parents=True)
    (root / "xdg/autostart").mkdir(parents=True)
    (root / "data/applications").mkdir(parents=True)
    (root / "xdg/autostart/sysapp.desktop").write_text(
        "[Desktop Entry]\nType=Application\nName=Системная\nExec=sysapp\nIcon=preferences-system\n")
    (root / "data/applications/alpha.desktop").write_text(
        "[Desktop Entry]\nType=Application\nName=Alpha\nExec=alpha %U\nIcon=applications-games\n")
    (root / "data/applications/beta.desktop").write_text(
        "[Desktop Entry]\nType=Application\nName=Beta\nExec=beta\n")


def main(argv: list[str]) -> int:
    root = Path(tempfile.mkdtemp(prefix="autostart-selftest-"))
    fixture(root)
    os.environ.update(XDG_CONFIG_HOME=str(root / "home"), XDG_CONFIG_DIRS=str(root / "xdg"),
                      XDG_DATA_HOME=str(root / "data"), XDG_DATA_DIRS=str(root / "nonexistent"))

    from gi.repository import GLib, Gsk, Gtk  # noqa: F401

    from . import model, ui

    result = {"ok": False, "msg": "не дошли до конца"}
    home = root / "home"

    def entries():
        return {e.id: e for e in model.load_entries(home, [root / "xdg"])}

    def check(cond, msg):
        if not cond:
            raise AssertionError(msg)

    def shot(win, suffix=""):
        path = os.environ.get("AUTOSTART_SHOT")
        if not path:
            return
        if suffix:
            path = path.replace(".png", f"-{suffix}.png")
        w, h = win.get_width(), win.get_height()
        paintable = Gtk.WidgetPaintable(widget=win)
        snap = Gtk.Snapshot()
        paintable.snapshot(snap, w, h)
        node = snap.to_node()
        tex = win.get_renderer().render_texture(node, None)
        tex.save_to_png(path)

    def steps(win):
        yield
        check(set(win.rows) == {"sysapp.desktop"}, f"строки: {list(win.rows)}")
        sysrow = win.rows["sysapp.desktop"]
        check(sysrow.remove_btn is None, "у системной записи есть «Убрать»")
        sysrow.switch.set_active(False)
        yield
        e = entries()["sysapp.desktop"]
        check(not e.enabled and (home / "autostart/sysapp.desktop").is_file(), "системная не выключилась")

        d = win.open_add_dialog()
        yield
        check(set(d.app_rows) == {"alpha.desktop", "beta.desktop"}, f"приложения: {list(d.app_rows)}")
        d.search.set_text("alp")
        yield
        shot(win, "dialog")
        d.app_rows["alpha.desktop"].emit("activated")
        yield
        check("alpha.desktop" in win.rows, "Alpha не добавлен")
        r = win.rows["alpha.desktop"]
        r.hidden.set_active(True)
        r.delay.set_value(5)
        r.where.set_selected(2)
        yield
        text = (home / "autostart/alpha.desktop").read_text()
        check("Exec=autostart-run 5 alpha -- alpha\n" in text, f"Exec alpha: {text}")
        check("OnlyShowIn=KDE;" in text, "нет OnlyShowIn=KDE;")
        e = entries()["alpha.desktop"]
        check((e.command, e.delay, e.hidden, e.where) == ("alpha", 5, True, "kde"), f"alpha: {e}")

        d = win.open_add_dialog()
        yield
        d.name_row.set_text("Мой скрипт")
        d.cmd_row.set_text("sh -c 'echo \"$HOME\"'")
        d.add_custom_btn.emit("clicked")
        yield
        check("moy-skript.desktop" in win.rows, f"своя команда не добавлена: {list(win.rows)}")
        e = entries()["moy-skript.desktop"]
        check(model.exec_split(e.command) == ["sh", "-c", 'echo "$HOME"'], f"команда: {e.command!r}")
        win.rows["alpha.desktop"].row.set_expanded(True)
        yield
        shot(win)
        win.rows["moy-skript.desktop"].remove_btn.emit("clicked")
        yield
        check("moy-skript.desktop" not in win.rows and not (home / "autostart/moy-skript.desktop").exists(),
              "своя команда не убрана")
        result.update(ok=True, msg="")

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

        GLib.timeout_add(400, tick)

    app = ui.make_app(on_window)
    app.run([sys.argv[0]])
    shutil.rmtree(root, ignore_errors=True)
    print("SELFTEST PASS" if result["ok"] else f"SELFTEST FAIL: {result['msg']}", flush=True)
    return 0 if result["ok"] else 1
