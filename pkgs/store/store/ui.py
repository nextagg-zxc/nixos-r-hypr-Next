"""«Магазин» (раздаваемая система): поиск и установка программ из nixpkgs и Flathub.
nixpkgs — через root-помощник (packages.json + пересборка, pkexec), Flathub — `flatpak --user`."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from . import catalog  # noqa: E402

APP_ID = "org.nixos.Store"
CSS = """
:root { --accent-bg-color: #4c8bf5; --accent-color: #78a9ff; --accent-fg-color: #ffffff; }
.badge { font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 6px; }
.badge.nixpkgs { background: #5277c3; color: #ffffff; }
.badge.flathub { background: #4a86cf; color: #ffffff; }
.log { font-family: monospace; font-size: 11px; }
"""


def env(name, default):
    return os.environ.get(name) or default


def index_path():
    return env("NIXOS_STORE_INDEX", "/var/lib/nixos-store/index.json")


def flake():
    return env("NIXOS_SHARE_ETC", "/etc/nixos")


def helper_cmd():
    h = os.environ.get("NIXOS_SETTINGS_HELPER")
    return [h] if h else ["pkexec", "@helper@"]


def flatpak():
    return env("NIXOS_STORE_FLATPAK", "flatpak")


def kde():
    return "KDE" in os.environ.get("XDG_CURRENT_DESKTOP", "").split(":")


def installed_nix() -> set[str]:
    try:
        return set(json.loads((Path(flake()) / "hosts/share/packages.json").read_text()))
    except (OSError, ValueError):
        return set()


def installed_flatpaks() -> set[str]:
    try:
        out = subprocess.run([flatpak(), "list", "--user", "--app", "--columns=application"],
                             capture_output=True, text=True, timeout=20).stdout
        return {l.strip() for l in out.splitlines() if l.strip()}
    except (OSError, subprocess.SubprocessError):
        return set()


def apps_dirs():
    return [Path(env("NIXOS_STORE_SYSAPPS", "/run/current-system/sw/share/applications")),
            Path.home() / ".local/share/flatpak/exports/share/applications"]


def desktop_dir() -> Path:
    try:
        d = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True).stdout.strip()
        if d and d != str(Path.home()):
            return Path(d)
    except OSError:
        pass
    return Path.home() / "Desktop"


class RunDialog(Adw.Dialog):
    def __init__(self, title):
        super().__init__(title=title, content_width=600, content_height=380, can_close=False)
        tv = Adw.ToolbarView()
        tv.add_top_bar(Adw.HeaderBar(show_end_title_buttons=False))
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=10, margin_bottom=12,
                      margin_start=12, margin_end=12)
        top = Gtk.Box(spacing=10)
        self.spinner = Adw.Spinner()
        self.status = Gtk.Label(label="Устанавливаю… это может занять несколько минут", xalign=0, wrap=True)
        top.append(self.spinner)
        top.append(self.status)
        self.buf = Gtk.TextBuffer()
        self.scroll = Gtk.ScrolledWindow(child=Gtk.TextView(buffer=self.buf, editable=False, monospace=True,
                                                            wrap_mode=Gtk.WrapMode.WORD_CHAR,
                                                            css_classes=["log"]), vexpand=True)
        self.close_btn = Gtk.Button(label="Закрыть", sensitive=False, halign=Gtk.Align.END,
                                    css_classes=["suggested-action", "pill"])
        self.close_btn.connect("clicked", lambda *_: self.force_close())
        for w in (top, self.scroll, self.close_btn):
            box.append(w)
        tv.set_content(box)
        self.set_child(tv)

    def append(self, line):
        self.buf.insert(self.buf.get_end_iter(), line + "\n")
        adj = self.scroll.get_vadjustment()
        GLib.idle_add(lambda: adj.set_value(adj.get_upper()) or False)

    def finish(self, ok, msg):
        self.spinner.set_visible(False)
        self.status.set_label(msg)
        self.close_btn.set_sensitive(True)
        self.set_can_close(True)


class Window(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Магазин", default_width=960, default_height=700)
        self.index = catalog.load_index(index_path())
        self.flathub: list[catalog.Entry] = []
        self.toasts = Adw.ToastOverlay()
        tv = Adw.ToolbarView()
        header = Adw.HeaderBar()
        self.search = Gtk.SearchEntry(placeholder_text="Найти программу: браузер, steam, obs, офис…",
                                      hexpand=True, width_request=420)
        self.search.connect("activate", lambda *_: self.do_search())
        self.search.connect("search-changed", lambda *_: self.schedule_search())
        header.set_title_widget(self.search)
        self.installed_btn = Gtk.ToggleButton(icon_name="view-list-symbolic", tooltip_text="Установленные")
        self.installed_btn.connect("toggled", lambda *_: self.show_installed() if self.installed_btn.get_active()
                                   else self.do_search())
        header.pack_end(self.installed_btn)
        tv.add_top_bar(header)
        self.shortcut = Gtk.CheckButton(label="Ярлык на рабочем столе", active=True, visible=kde(),
                                        margin_start=18, margin_top=8)
        self.list = Gtk.ListBox(css_classes=["boxed-list"], selection_mode=Gtk.SelectionMode.NONE,
                                margin_top=12, margin_bottom=18, margin_start=18, margin_end=18, valign=Gtk.Align.START)
        self.status = Adw.StatusPage(icon_name="org.nixos.Store", title="Магазин программ",
                                     description=self.intro(), vexpand=True)
        self.stack = Gtk.Stack()
        self.stack.add_named(self.status, "status")
        self.stack.add_named(Gtk.ScrolledWindow(child=Adw.Clamp(maximum_size=860, child=self.list)), "list")
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        body.append(self.shortcut)
        body.append(self.stack)
        tv.set_content(body)
        self.toasts.set_child(tv)
        self.set_content(self.toasts)
        self.rows: dict[str, Gtk.Button] = {}
        self._timer = 0
        threading.Thread(target=self.init_flathub, daemon=True).start()

    def intro(self):
        if self.index is None:
            return "Готовлю список программ NixOS (первые минуты после установки). Flathub уже доступен."
        return "Наберите название или что нужно — например «браузер», «запись экрана», «офис»."

    def toast(self, t):
        self.toasts.add_toast(Adw.Toast(title=t, timeout=4))

    # ── Flathub ──
    def init_flathub(self):
        try:
            subprocess.run([flatpak(), "remote-add", "--user", "--if-not-exists", "flathub",
                            "https://dl.flathub.org/repo/flathub.flatpakrepo"], capture_output=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            pass

    def flathub_search(self, q):
        try:
            out = subprocess.run([flatpak(), "search", "--user", "--columns=application,name,description,version", q],
                                 capture_output=True, text=True, timeout=30).stdout
            return catalog.parse_flatpak_search(out)
        except (OSError, subprocess.SubprocessError):
            return []

    # ── поиск ──
    def schedule_search(self):
        if self._timer:
            GLib.source_remove(self._timer)
        self._timer = GLib.timeout_add(400, self._timer_fire)

    def _timer_fire(self):
        self._timer = 0
        self.do_search()
        return False

    def do_search(self):
        q = self.search.get_text().strip()
        if self.installed_btn.get_active():
            self.installed_btn.set_active(False)
            return
        if not q:
            self.stack.set_visible_child_name("status")
            return

        def work():
            flat = self.flathub_search(q)
            if self.index is None:
                self.index = catalog.load_index(index_path())
            res = catalog.search(q, self.index, flat)
            GLib.idle_add(self.show, res, f"Ничего не нашлось по «{q}»")
        threading.Thread(target=work, daemon=True).start()

    def show_installed(self):
        def work():
            nix = installed_nix()
            flat = installed_flatpaks()
            idx = {e.attr: e for e in (self.index or [])}
            res = [idx.get(a, catalog.Entry(a, a, "", "", "nixpkgs")) for a in sorted(nix)]
            res += [catalog.Entry(a, a.split(".")[-1], "", "", "flathub") for a in sorted(flat)]
            GLib.idle_add(self.show, res, "Из Магазина пока ничего не установлено")
        threading.Thread(target=work, daemon=True).start()

    def show(self, entries, empty):
        while (r := self.list.get_first_child()) is not None:
            self.list.remove(r)
        self.rows = {}
        if not entries:
            self.status.set_description(empty)
            self.stack.set_visible_child_name("status")
            return False
        nix, flat = installed_nix(), installed_flatpaks()
        for e in entries:
            row = Adw.ActionRow(title=GLib.markup_escape_text(e.name),
                                subtitle=GLib.markup_escape_text((e.description or "")[:160]))
            icon = Gtk.Image(icon_name=e.attr if e.source == "flathub" else e.name, pixel_size=36)
            if not Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).has_icon(icon.get_icon_name() or ""):
                icon.set_from_icon_name("application-x-executable")
            row.add_prefix(icon)
            badge = Gtk.Label(label="NixOS" if e.source == "nixpkgs" else "Flathub", valign=Gtk.Align.CENTER,
                              css_classes=["badge", e.source])
            row.add_suffix(badge)
            have = e.attr in (nix if e.source == "nixpkgs" else flat)
            btn = Gtk.Button(label="Удалить" if have else "Установить", valign=Gtk.Align.CENTER,
                             css_classes=["destructive-action" if have else "suggested-action"])
            btn.connect("clicked", lambda _b, e=e, have=have: self.remove(e) if have else self.install(e))
            row.add_suffix(btn)
            self.rows[e.source + ":" + e.attr] = btn
            self.list.append(row)
        self.stack.set_visible_child_name("list")
        return False

    # ── установка ──
    def run(self, title, cmd, done):
        dlg = RunDialog(title)
        dlg.present(self)

        def work():
            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                     errors="replace", stdin=subprocess.DEVNULL)
                for line in p.stdout:
                    line = line.rstrip("\n")
                    if not line.startswith("@@"):
                        GLib.idle_add(dlg.append, line)
                rc = p.wait()
            except OSError as err:
                GLib.idle_add(dlg.append, str(err))
                rc = 1
            ok = rc == 0
            GLib.idle_add(dlg.finish, ok, "Готово" if ok else "Не получилось — подробности в журнале")
            GLib.idle_add(done, ok)
        threading.Thread(target=work, daemon=True).start()

    def apps_snapshot(self):
        out = set()
        for d in apps_dirs():
            if d.is_dir():
                out |= {p.name for p in d.glob("*.desktop")}
        return out

    def install(self, e):
        before = self.apps_snapshot()
        if e.source == "nixpkgs":
            cmd = helper_cmd() + ["packages-add", e.attr]
        else:
            cmd = [flatpak(), "install", "--user", "-y", "--noninteractive", "flathub", e.attr]

        def done(ok):
            if ok:
                self.toast(f"«{e.name}» установлена")
                if self.shortcut.get_visible() and self.shortcut.get_active():
                    self.add_shortcut(e, before)
            self.do_search() if self.search.get_text().strip() else self.show_installed()
            return False
        self.run(f"Установка «{e.name}»", cmd, done)

    def remove(self, e):
        if e.source == "nixpkgs":
            cmd = helper_cmd() + ["packages-remove", e.attr]
        else:
            cmd = [flatpak(), "uninstall", "--user", "-y", "--noninteractive", e.attr]

        def done(ok):
            self.toast(f"«{e.name}» удалена" if ok else "Не получилось удалить")
            self.do_search() if self.search.get_text().strip() else self.show_installed()
            return False
        self.run(f"Удаление «{e.name}»", cmd, done)

    def add_shortcut(self, e, before):
        new = sorted(self.apps_snapshot() - before)
        if e.source == "flathub":
            new = [f"{e.attr}.desktop"] if f"{e.attr}.desktop" in self.apps_snapshot() else new
        desk = desktop_dir()
        desk.mkdir(parents=True, exist_ok=True)
        for name in new[:2]:
            for d in apps_dirs():
                src = d / name
                if src.is_file():
                    dst = desk / name
                    if not dst.exists():
                        shutil.copy(src, dst)
                        dst.chmod(0o755)
                    break


def make_app(on_window=None):
    app = Adw.Application(application_id=APP_ID, flags=Gio.ApplicationFlags.NON_UNIQUE)

    def activate(app):
        css = Gtk.CssProvider()
        css.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        win = Window(app)
        win.present()
        if on_window:
            on_window(win)

    app.connect("activate", activate)
    return app


def main(argv):
    return make_app().run(argv)
