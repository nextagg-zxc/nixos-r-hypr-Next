"""Окно «Автозапуск» (GTK4 + libadwaita): что стартует при входе, вкл/выкл, где, скрыто, задержка."""
from __future__ import annotations

import os
import shlex
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from . import model  # noqa: E402

APP_ID = "org.nixos.Autostart"
WHERE = [("all", "Везде"), ("hyprland", "Только Hyprland"), ("kde", "Только KDE")]

CSS = """
:root {
  --accent-bg-color: #b4befe; --accent-color: #b4befe; --accent-fg-color: #11111b;
  --window-bg-color: #0b0b12; --window-fg-color: #e6e6f0;
  --view-bg-color: #0b0b12; --headerbar-bg-color: #0b0b12; --headerbar-shade-color: transparent;
  --card-bg-color: #14141e; --card-shade-color: #1e1e2b;
  --popover-bg-color: #171722; --dialog-bg-color: #14141e;
}
.hint { color: #8e8ea0; font-size: 12px; }
.cmd { font-family: monospace; font-size: 12px; }
"""


def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def config_dirs() -> list[Path]:
    return [Path(p) for p in (os.environ.get("XDG_CONFIG_DIRS") or "/etc/xdg").split(":") if p]


def data_dirs() -> list[Path]:
    home = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    rest = (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":")
    return [home, *(Path(p) for p in rest if p)]


def shown(command: str) -> str:
    """Exec → как в терминале (для подписи)."""
    return shlex.join(model.exec_split(command))


def icon_image(icon: str, size: int = 32) -> Gtk.Image:
    if icon and icon.startswith("/"):
        img = Gtk.Image.new_from_file(icon)
    else:
        img = Gtk.Image(icon_name=icon or "application-x-executable")
    img.set_pixel_size(size)
    return img


def custom_command(text: str) -> str:
    """Команда, как её пишет человек (синтаксис оболочки) → Exec. Ошибка кавычек → ValueError."""
    args = shlex.split(text)
    if not args:
        raise ValueError("пустая команда")
    return model.exec_quote(args)


class EntryRow:
    """Строка записи: переключатель в заголовке, внутри — где, скрыто, задержка, «Убрать»."""

    def __init__(self, win: "Window", e: model.Entry):
        self.win, self.e = win, e
        self.loading = True
        self.row = Adw.ExpanderRow(title=GLib.markup_escape_text(e.name),
                                   subtitle=GLib.markup_escape_text(shown(e.command)))
        self.row.add_prefix(icon_image(e.icon))
        self.switch = Gtk.Switch(active=e.enabled, valign=Gtk.Align.CENTER)
        self.switch.connect("notify::active", self.changed)
        self.row.add_suffix(self.switch)

        self.where = Adw.ComboRow(title="Где запускать", model=Gtk.StringList.new([t for _, t in WHERE]))
        self.where.set_selected([k for k, _ in WHERE].index(e.where))
        self.where.connect("notify::selected", self.changed)
        self.hidden = Adw.SwitchRow(title="Запускать скрытым", subtitle="Hyprland — в фон, KDE — свёрнутым",
                                    active=e.hidden)
        self.hidden.connect("notify::active", self.changed)
        self.delay = Adw.SpinRow.new_with_range(0, 600, 1)
        self.delay.set_title("Задержка, с")
        self.delay.set_value(e.delay)
        self.delay.connect("notify::value", self.changed)
        for w in (self.where, self.hidden, self.delay):
            self.row.add_row(w)

        self.remove_btn = None
        if e.source == "user":
            act = Adw.ActionRow(title="Убрать из автозапуска")
            self.remove_btn = Gtk.Button(label="Убрать", valign=Gtk.Align.CENTER,
                                         css_classes=["destructive-action"])
            self.remove_btn.connect("clicked", lambda *_: win.remove(self))
            act.add_suffix(self.remove_btn)
            self.row.add_row(act)
        else:
            self.row.add_row(Adw.ActionRow(title="Системная запись", subtitle="Её можно только выключить"))
        self.loading = False

    def changed(self, *_):
        if self.loading:
            return
        self.e.enabled = self.switch.get_active()
        self.e.where = WHERE[self.where.get_selected()][0]
        self.e.hidden = self.hidden.get_active()
        self.e.delay = int(self.delay.get_value())
        self.win.save(self.e)


class AddDialog(Adw.Dialog):
    """Добавить: из установленных приложений или своей командой."""

    def __init__(self, win: "Window"):
        super().__init__(title="Добавить в автозапуск", content_width=520, content_height=600)
        self.win = win
        stack = Adw.ViewStack()
        tv = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.ViewSwitcher(stack=stack, policy=Adw.ViewSwitcherPolicy.WIDE))
        tv.add_top_bar(header)
        tv.set_content(stack)
        self.set_child(tv)

        # приложения
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=8, margin_bottom=8,
                      margin_start=12, margin_end=12)
        self.search = Gtk.SearchEntry(placeholder_text="Поиск приложения")
        self.list = Gtk.ListBox(css_classes=["boxed-list"], selection_mode=Gtk.SelectionMode.NONE)
        self.app_rows: dict[str, Adw.ActionRow] = {}
        self.apps = {a.id: a for a in model.list_apps(data_dirs())}
        for a in self.apps.values():
            r = Adw.ActionRow(title=GLib.markup_escape_text(a.name), subtitle=GLib.markup_escape_text(shown(a.command)),
                              activatable=True)
            r.add_prefix(icon_image(a.icon))
            r.connect("activated", lambda _r, a=a: self.add_app(a))
            self.list.append(r)
            self.app_rows[a.id] = r
        self.list.set_filter_func(self.filter)
        self.search.connect("search-changed", lambda *_: self.list.invalidate_filter())
        box.append(self.search)
        box.append(Gtk.ScrolledWindow(child=self.list, vexpand=True))
        stack.add_titled_with_icon(box, "apps", "Приложение", "view-app-grid-symbolic")

        # своя команда
        g = Adw.PreferencesGroup(description="Команда пишется как в терминале, например: "
                                             "sh -c 'sleep 1; notify-send привет'")
        self.name_row = Adw.EntryRow(title="Название")
        self.cmd_row = Adw.EntryRow(title="Команда")
        self.add_custom_btn = Gtk.Button(label="Добавить", css_classes=["suggested-action", "pill"],
                                         halign=Gtk.Align.CENTER, margin_top=12)
        self.add_custom_btn.connect("clicked", lambda *_: self.add_custom())
        g.add(self.name_row)
        g.add(self.cmd_row)
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=12, margin_start=12, margin_end=12)
        page.append(g)
        page.append(self.add_custom_btn)
        stack.add_titled_with_icon(page, "custom", "Своя команда", "utilities-terminal-symbolic")

    def filter(self, row):
        q = self.search.get_text().casefold().strip()
        return not q or q in (row.get_title() + " " + row.get_subtitle()).casefold()

    def add_app(self, a: model.Entry):
        if self.win.add(model.Entry(**{**a.__dict__})):
            self.close()

    def add_custom(self):
        name = self.name_row.get_text().strip()
        try:
            cmd = custom_command(self.cmd_row.get_text())
        except ValueError as err:
            self.win.toast(f"Команда: {err}")
            return
        if not name:
            name = model.exec_split(cmd)[0].rsplit("/", 1)[-1]
        if self.win.add(model.entry_from_command(name, cmd, self.win.taken())):
            self.close()


class Window(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title="Автозапуск", default_width=760, default_height=720)
        self.home = config_home()
        self.rows: dict[str, EntryRow] = {}
        self.toasts = Adw.ToastOverlay()
        tv = Adw.ToolbarView()
        header = Adw.HeaderBar(title_widget=Adw.WindowTitle(title="Автозапуск",
                                                           subtitle="что запускается при входе"))
        self.add_btn = Gtk.Button(icon_name="list-add-symbolic", tooltip_text="Добавить")
        self.add_btn.add_css_class("suggested-action")
        self.add_btn.connect("clicked", lambda *_: self.open_add_dialog())
        header.pack_start(self.add_btn)
        tv.add_top_bar(header)
        self.group = Adw.PreferencesGroup(title="При входе в систему")
        hint = Gtk.Label(label=f"Записи — {self.home / 'autostart'}; применяются при следующем входе.",
                         css_classes=["hint"], wrap=True, xalign=0, margin_top=12)
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=18, margin_bottom=18,
                       margin_start=18, margin_end=18)
        page.append(self.group)
        page.append(hint)
        tv.set_content(Gtk.ScrolledWindow(child=Adw.Clamp(maximum_size=760, child=page), vexpand=True))
        self.toasts.set_child(tv)
        self.set_content(self.toasts)
        self.reload()

    def toast(self, text: str):
        self.toasts.add_toast(Adw.Toast(title=text, timeout=3))

    def taken(self) -> set[str]:
        return set(self.rows)

    def reload(self):
        for r in self.rows.values():
            self.group.remove(r.row)
        self.rows = {}
        for e in model.load_entries(self.home, config_dirs()):
            r = EntryRow(self, e)
            self.rows[e.id] = r
            self.group.add(r.row)

    def save(self, e: model.Entry):
        try:
            model.save_entry(e, self.home)
        except OSError as err:
            self.toast(f"Не сохранено: {err}")
            return
        self.toast("Сохранено")

    def add(self, e: model.Entry) -> bool:
        if e.id in self.rows:
            self.toast(f"«{e.name}» уже в автозапуске")
            return False
        self.save(e)
        self.reload()
        if e.id in self.rows:
            self.rows[e.id].row.set_expanded(True)
        return True

    def remove(self, r: EntryRow):
        model.remove_entry(r.e, self.home)
        self.reload()
        self.toast(f"«{r.e.name}» убран")

    def open_add_dialog(self) -> AddDialog:
        d = AddDialog(self)
        d.present(self)
        return d


def make_app(on_window=None) -> Adw.Application:
    app = Adw.Application(application_id=APP_ID, flags=Gio.ApplicationFlags.NON_UNIQUE)

    def activate(app):
        css = Gtk.CssProvider()
        css.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        win = Window(app)
        win.present()
        if on_window:
            on_window(win)

    app.connect("activate", activate)
    return app


def main(argv: list[str]) -> int:
    return make_app().run(argv)
