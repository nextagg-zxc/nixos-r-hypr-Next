"""Малые программы раздаваемой системы (GTK4/Adw):
  exe <файл>   — «Как запустить?» для .exe/.msi (Wine / Proton), AppImage — сразу
  keys         — шпаргалка клавиш (KDE «как Windows»)
  report       — «Сообщить о проблеме»: архив с журналами без личного
  help         — «Позвать на помощь»: RustDesk со своим сервером
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

from . import logic  # noqa: E402
from .report import collect_report  # noqa: E402

RUSTDESK_HOST = "@rustdesk_host@"
RUSTDESK_KEY = "@rustdesk_key@"

KEYS = [
    ("Окна и рабочий стол", [
        ("Win", "Меню «Пуск»"), ("Win + D", "Свернуть всё / показать рабочий стол"),
        ("Win + ← / →", "Окно на половину экрана"), ("Win + ↑", "Развернуть окно"),
        ("Alt + Tab", "Переключить окно"), ("Alt + F4", "Закрыть окно"), ("Win + L", "Заблокировать компьютер"),
    ]),
    ("Программы", [
        ("Win + E", "Проводник (Dolphin)"), ("Win + R", "Выполнить / поиск"), ("Win + I", "Параметры"),
        ("Ctrl + Shift + Esc", "Диспетчер задач"), ("Win + K", "Эта шпаргалка"),
    ]),
    ("Текст и скриншоты", [
        ("Win + Shift + S", "Скриншот области"), ("Print Screen", "Скриншот экрана"),
        ("Win + V", "Журнал буфера обмена"), ("Win + .", "Эмодзи"), ("Alt + Shift", "Сменить язык"),
    ]),
]


def run_app(build, app_id):
    app = Adw.Application(application_id=app_id, flags=Gio.ApplicationFlags.NON_UNIQUE)
    app.connect("activate", lambda a: build(a))
    return app.run([sys.argv[0]])


# ── .exe / .msi / AppImage ──
def run_exe(path: str, choice: str | None = None, on_window=None) -> int:
    kind = logic.kind_of(path)
    store = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "nixos-run-exe" / "choices.json"
    if kind == "appimage":
        return subprocess.call(logic.run_command("appimage", path))
    if kind != "exe":
        return _message("Не программа для Windows", f"«{Path(path).name}» нельзя запустить таким способом.")
    if path.lower().endswith(".msi"):
        return subprocess.call(logic.run_command("msi", path))
    how = choice or logic.remembered(store, path)
    if how:
        return subprocess.call(logic.run_command(how, path))

    def build(app):
        win = Adw.ApplicationWindow(application=app, title="Запуск программы Windows", default_width=520)
        tv = Adw.ToolbarView()
        tv.add_top_bar(Adw.HeaderBar())
        page = Adw.StatusPage(icon_name="application-x-executable-symbolic",
                              title=f"Как запустить «{Path(path).name}»?",
                              description="Программы Windows работают через совместимость. "
                                          "Для обычных программ — Wine, для игр — Proton (как в Steam).")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, halign=Gtk.Align.CENTER)
        remember = Gtk.CheckButton(label="Запомнить для этого файла")
        win.how_buttons, win.remember = {}, remember
        for how, label in (("wine", "Как программу (Wine)"), ("proton", "Как игру (Proton)")):
            b = Gtk.Button(label=label, css_classes=["pill"] + (["suggested-action"] if how == "wine" else []))
            b.connect("clicked", lambda _b, h=how: (logic.remember(store, path, h) if remember.get_active() else None,
                                                     subprocess.Popen(logic.run_command(h, path),
                                                                      start_new_session=True), app.quit()))
            box.append(b)
            win.how_buttons[how] = b
        box.append(remember)
        page.set_child(box)
        tv.set_content(page)
        win.set_content(tv)
        win.present()
        if on_window:
            on_window(win)
    return run_app(build, "org.nixos.RunExe")


def _message(title, text) -> int:
    def build(app):
        dlg = Adw.AlertDialog(heading=title, body=text)
        dlg.add_response("ok", "Понятно")
        win = Adw.ApplicationWindow(application=app, default_width=1, default_height=1)
        dlg.connect("response", lambda *_: app.quit())
        win.present()
        dlg.present(win)
    run_app(build, "org.nixos.RunExe")
    return 1


# ── шпаргалка ──
def keys(on_window=None) -> int:
    def build(app):
        win = Adw.ApplicationWindow(application=app, title="Горячие клавиши", default_width=560, default_height=640)
        tv = Adw.ToolbarView()
        tv.add_top_bar(Adw.HeaderBar())
        page = Adw.PreferencesPage()
        for title, rows in KEYS:
            g = Adw.PreferencesGroup(title=title)
            for key, what in rows:
                r = Adw.ActionRow(title=what)
                r.add_suffix(Gtk.Label(label=key, css_classes=["dim-label", "monospace"]))
                g.add(r)
            page.add(g)
        tv.set_content(page)
        win.set_content(tv)
        win.present()
        if on_window:
            on_window(win)
    return run_app(build, "org.nixos.Keys")


# ── отчёт о проблеме ──
def report(on_window=None) -> int:
    def build(app):
        win = Adw.ApplicationWindow(application=app, title="Сообщить о проблеме", default_width=620,
                                    default_height=520)
        tv = Adw.ToolbarView()
        tv.add_top_bar(Adw.HeaderBar())
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=18, margin_bottom=18,
                      margin_start=18, margin_end=18)
        box.append(Gtk.Label(label="Опишите, что случилось и когда. Программа соберёт журналы и сведения о "
                                   "компьютере в один файл — пароли, адреса и названия Wi‑Fi из него убираются. "
                                   "Ничего не отправляется само: перешлите файл тому, кто помогает.",
                             wrap=True, xalign=0))
        note = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR, top_margin=8, left_margin=8, right_margin=8)
        box.append(Gtk.Frame(child=Gtk.ScrolledWindow(child=note, vexpand=True)))
        status = Gtk.Label(xalign=0, wrap=True)
        btn = Gtk.Button(label="Собрать отчёт", halign=Gtk.Align.END, css_classes=["suggested-action", "pill"])
        open_btn = Gtk.Button(label="Открыть папку", halign=Gtk.Align.END, visible=False, css_classes=["pill"])
        row = Gtk.Box(spacing=10, halign=Gtk.Align.END)
        row.append(open_btn)
        row.append(btn)
        box.append(status)
        box.append(row)

        def go(*_):
            btn.set_sensitive(False)
            status.set_label("Собираю… (до минуты)")
            buf = note.get_buffer()
            text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)

            def work():
                path = collect_report(text, Path.home())
                win.report_path = path
                GLib.idle_add(status.set_label, f"Готово: {path}")
                GLib.idle_add(open_btn.set_visible, True)
                GLib.idle_add(btn.set_sensitive, True)
            threading.Thread(target=work, daemon=True).start()
        btn.connect("clicked", go)
        open_btn.connect("clicked", lambda *_: subprocess.Popen(["xdg-open", str(Path.home())]))
        win.report_btn = btn
        tv.set_content(box)
        win.set_content(tv)
        win.present()
        if on_window:
            on_window(win)
    return run_app(build, "org.nixos.Report")


# ── удалённая помощь ──
def help_() -> int:
    cfg = Path.home() / ".config/rustdesk/RustDesk2.toml"
    if RUSTDESK_HOST and not cfg.exists():   # без своего сервера (публичная сборка) — серверы RustDesk
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(logic.rustdesk_config(RUSTDESK_HOST, RUSTDESK_KEY), encoding="utf-8")
    exe = shutil.which("rustdesk")
    if not exe:
        return _message("Нет RustDesk", "Программа удалённой помощи не установлена.")
    os.execv(exe, [exe])


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "--selftest":
        from . import selftest
        return selftest.main()
    if cmd == "exe" and len(argv) > 2:
        return run_exe(argv[2])
    if cmd == "keys":
        return keys()
    if cmd == "report":
        return report()
    if cmd == "help":
        return help_()
    print(__doc__, file=sys.stderr)
    return 2
