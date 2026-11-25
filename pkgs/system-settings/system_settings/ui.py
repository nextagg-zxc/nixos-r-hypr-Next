"""«Настройка системы» (раздаваемая система): разделы слева, как «Параметры» Windows.
Система (ядро, защита процессора, виртуализация, IOMMU), Внешний вид (KDE: Windows 11/10),
Загрузка и безопасность (Secure Boot, Windows в меню загрузки, TPM2).
Всё, что меняет систему, — через root-помощник nixos-share-apply (pkexec), с журналом сборки."""
from __future__ import annotations

import datetime
import json
import os
import urllib.request
import shutil
import subprocess
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

APP_ID = "org.nixos.Settings"
KERNELS = [
    ("cachyos", "CachyOS", "Для игр: оптимизации под отзывчивость и FPS. Рекомендуем."),
    ("zen", "Zen", "Отзывчивый рабочий стол и стримы. Хороший запасной вариант."),
    ("linux", "Обычное (Linux)", "Самое стабильное, без оптимизаций. Если с другими что-то не так."),
]
CSS = """
:root { --accent-bg-color: #4c8bf5; --accent-color: #78a9ff; --accent-fg-color: #ffffff; }
.hint { color: alpha(currentColor, 0.65); font-size: 12px; }
.log { font-family: monospace; font-size: 11px; }
"""


def etc() -> str:
    return os.environ.get("NIXOS_SHARE_ETC", "/etc/nixos")


def helper_cmd() -> list[str]:
    """pkexec + помощник; для проверок — NIXOS_SETTINGS_HELPER (без pkexec)."""
    h = os.environ.get("NIXOS_SETTINGS_HELPER")
    return [h] if h else ["pkexec", "@helper@"]


def helper_direct() -> list[str]:
    """Помощник без pkexec — для чтения (список поколений), root не нужен."""
    h = os.environ.get("NIXOS_SETTINGS_HELPER")
    return [h] if h else ["@helper@"]


def channel_url() -> str:
    return os.environ.get("NIXOS_UPDATE_CHANNEL_URL", "https://channels.nixos.org/nixos-unstable/git-revision")


def check_updates() -> dict:
    """Есть ли новее nixpkgs (ветка nixos-unstable) и обновления Flathub. Без root."""
    res = {"system": None, "flatpaks": 0, "online": True}
    try:
        with open(os.path.join(etc(), "flake.lock"), encoding="utf-8") as f:
            cur = json.load(f)["nodes"]["nixpkgs"]["locked"]["rev"]
        with urllib.request.urlopen(channel_url(), timeout=10) as r:
            new = r.read().decode().strip()
        res["system"] = bool(new) and new != cur
    except (OSError, ValueError, KeyError):
        res["online"] = False
    try:
        out = subprocess.run([os.environ.get("NIXOS_STORE_FLATPAK", "flatpak"), "remote-ls", "--user", "--updates",
                              "--columns=application"], capture_output=True, text=True, timeout=60).stdout
        res["flatpaks"] = len([l for l in out.splitlines() if l.strip()])
    except (OSError, subprocess.SubprocessError):
        pass
    return res


def read_choices() -> dict:
    try:
        with open(os.path.join(etc(), "hosts", "share", "choices.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


class RunDialog(Adw.Dialog):
    """Окно выполнения: журнал помощника, итог — тост в главном окне."""

    def __init__(self, win: "Window", title: str):
        super().__init__(title=title, content_width=640, content_height=420, can_close=False)
        self.win = win
        tv = Adw.ToolbarView()
        tv.add_top_bar(Adw.HeaderBar(show_end_title_buttons=False))
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=10, margin_bottom=12,
                      margin_start=12, margin_end=12)
        self.status = Gtk.Label(label="Выполняется… это может занять несколько минут", xalign=0, wrap=True)
        self.spinner = Adw.Spinner()
        top = Gtk.Box(spacing=10)
        top.append(self.spinner)
        top.append(self.status)
        self.buf = Gtk.TextBuffer()
        view = Gtk.TextView(buffer=self.buf, editable=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR,
                            css_classes=["log"])
        self.scroll = Gtk.ScrolledWindow(child=view, vexpand=True)
        self.close_btn = Gtk.Button(label="Закрыть", sensitive=False, halign=Gtk.Align.END,
                                    css_classes=["suggested-action", "pill"])
        self.close_btn.connect("clicked", lambda *_: self.force_close())
        box.append(top)
        box.append(self.scroll)
        box.append(self.close_btn)
        tv.set_content(box)
        self.set_child(tv)
        self.events: list[dict] = []

    def append(self, line: str):
        self.buf.insert(self.buf.get_end_iter(), line + "\n")
        adj = self.scroll.get_vadjustment()
        GLib.idle_add(lambda: adj.set_value(adj.get_upper()) or False)

    def finish(self, ok: bool, msg: str):
        self.spinner.set_visible(False)
        self.status.set_label(msg)
        self.close_btn.set_sensitive(True)
        self.set_can_close(True)


class Window(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title="Настройка системы", default_width=980, default_height=700)
        self.toasts = Adw.ToastOverlay()
        self.split = Adw.NavigationSplitView(min_sidebar_width=220, max_sidebar_width=260)
        self.pages: dict[str, Adw.NavigationPage] = {}
        self.sidebar = Gtk.ListBox(css_classes=["navigation-sidebar"])
        self.sidebar.connect("row-selected", self.on_section)
        side = Adw.ToolbarView()
        side.add_top_bar(Adw.HeaderBar(title_widget=Adw.WindowTitle(title="Настройка системы")))
        side.set_content(Gtk.ScrolledWindow(child=self.sidebar))
        self.split.set_sidebar(Adw.NavigationPage(title="Разделы", child=side))
        self.toasts.set_child(self.split)
        self.set_content(self.toasts)
        self.choices = read_choices()
        self.sections = [("system", "Система", "computer-symbolic", self.build_system)]
        if shutil.which(os.environ.get("NIXOS_KDE_LOOK", "nixos-kde-look")):
            self.sections.append(("look", "Внешний вид", "preferences-desktop-appearance-symbolic", self.build_look))
        self.sections.append(("boot", "Загрузка и безопасность", "security-high-symbolic", self.build_boot))
        self.sections.append(("update", "Обновление", "software-update-available-symbolic", self.build_update))
        for key, title, icon, _ in self.sections:
            row = Gtk.ListBoxRow()
            row.key = key
            b = Gtk.Box(spacing=12, margin_top=8, margin_bottom=8, margin_start=6)
            b.append(Gtk.Image(icon_name=icon))
            b.append(Gtk.Label(label=title, xalign=0))
            row.set_child(b)
            self.sidebar.append(row)
        start = os.environ.get("NIXOS_SETTINGS_SECTION", "system")
        keys = [s[0] for s in self.sections]
        self.sidebar.select_row(self.sidebar.get_row_at_index(keys.index(start) if start in keys else 0))

    # ── общее ──
    def toast(self, text: str):
        self.toasts.add_toast(Adw.Toast(title=text, timeout=4))

    def on_section(self, _lb, row):
        if row is None:
            return
        builder = next(s[3] for s in self.sections if s[0] == row.key)
        title = next(s[1] for s in self.sections if s[0] == row.key)
        tv = Adw.ToolbarView()
        tv.add_top_bar(Adw.HeaderBar())
        page = Adw.PreferencesPage()
        builder(page)
        tv.set_content(page)
        self.current = Adw.NavigationPage(title=title, child=tv)
        self.split.set_content(self.current)
        self.split.set_show_content(True)

    def run_helper(self, args: list[str], title: str, stdin: str = "", done=None):
        """Помощник в фоне, журнал — в окне выполнения; done(ok, events) — в главном потоке."""
        dlg = RunDialog(self, title)
        dlg.present(self)

        def work():
            try:
                p = subprocess.Popen(helper_cmd() + args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, errors="replace")
                p.stdin.write(stdin)
                p.stdin.close()
                for line in p.stdout:
                    line = line.rstrip("\n")
                    if line.startswith("@@"):
                        try:
                            dlg.events.append(json.loads(line[2:]))
                        except ValueError:
                            pass
                        continue
                    GLib.idle_add(dlg.append, line)
                rc = p.wait()
            except OSError as e:
                GLib.idle_add(dlg.append, str(e))
                rc = 1
            ok = rc == 0
            msg = "Готово" if ok else ("Отменено" if rc in (126, 127) else "Не получилось — подробности в журнале")
            GLib.idle_add(dlg.finish, ok, msg)
            if done:
                GLib.idle_add(done, ok, dlg.events)
            GLib.idle_add(self.reload)

        threading.Thread(target=work, daemon=True).start()
        return dlg

    def reload(self):
        self.choices = read_choices()
        row = self.sidebar.get_selected_row()
        self.on_section(self.sidebar, row)
        return False

    # ── Система ──
    def build_system(self, page: Adw.PreferencesPage):
        c = self.choices
        sysc = c.get("system", {})
        g = Adw.PreferencesGroup(title="Ядро", description="Новое ядро заработает после перезагрузки.")
        self.kernel_rows = {}
        first = None
        cur = c.get("kernel", "cachyos")
        for key, name, desc in KERNELS:
            row = Adw.ActionRow(title=name, subtitle=desc, activatable=True)
            radio = Gtk.CheckButton(group=first, active=(key == cur), valign=Gtk.Align.CENTER)
            first = first or radio
            row.add_prefix(radio)
            row.set_activatable_widget(radio)
            self.kernel_rows[key] = radio
            g.add(row)
        page.add(g)

        g2 = Adw.PreferencesGroup(title="Возможности")
        self.sw_mitig = Adw.SwitchRow(
            title="Выключить защиту процессора",
            subtitle="В играх может прибавить несколько процентов, но вредоносный код сможет читать чужую "
                     "память. Включайте, только если понимаете риск.",
            active=bool(sysc.get("mitigationsOff", False)))
        self.sw_virt = Adw.SwitchRow(title="Виртуализация",
                                     subtitle="Виртуальные машины (Windows внутри Linux) через virt-manager.",
                                     active=bool(sysc.get("virtualization", True)))
        self.sw_iommu = Adw.SwitchRow(title="IOMMU",
                                      subtitle="Нужно, чтобы отдать видеокарту или USB виртуальной машине. "
                                               "Обычно ничего не замедляет.",
                                      active=bool(sysc.get("iommu", True)))
        for r in (self.sw_mitig, self.sw_virt, self.sw_iommu):
            g2.add(r)
        page.add(g2)

        g3 = Adw.PreferencesGroup()
        self.apply_btn = Gtk.Button(label="Применить", halign=Gtk.Align.END, css_classes=["suggested-action", "pill"])
        self.apply_btn.connect("clicked", lambda *_: self.apply_system())
        g3.add(self.apply_btn)
        page.add(g3)

    def system_patch(self) -> dict:
        kernel = next(k for k, r in self.kernel_rows.items() if r.get_active())
        return {"kernel": kernel, "system": {"mitigationsOff": self.sw_mitig.get_active(),
                                             "virtualization": self.sw_virt.get_active(),
                                             "iommu": self.sw_iommu.get_active()}}

    def apply_system(self):
        self.run_helper(["set"], "Применяю настройки системы", json.dumps(self.system_patch()),
                        done=lambda ok, _e: self.toast("Настройки применены — перезагрузите компьютер"
                                                       if ok else "Настройки не применены"))

    # ── Внешний вид (KDE) ──
    def build_look(self, page: Adw.PreferencesPage):
        g = Adw.PreferencesGroup(title="Вид рабочего стола KDE",
                                 description="Панель и «Пуск» перестроятся сразу; ярлыки на рабочем столе останутся.")
        self.look_btns = {}
        for look, title, sub in (("win11", "Как Windows 11", "Значки по центру, скругления"),
                                 ("win10", "Как Windows 10", "«Пуск» слева, прямые углы")):
            row = Adw.ActionRow(title=title, subtitle=sub)
            b = Gtk.Button(label="Выбрать", valign=Gtk.Align.CENTER)
            b.connect("clicked", lambda _b, l=look: self.apply_look(["apply", l]))
            row.add_suffix(b)
            self.look_btns[look] = b
            g.add(row)
        row = Adw.ActionRow(title="Вернуть вид Windows", subtitle="Если что-то сдвинулось или пропала панель")
        b = Gtk.Button(label="Вернуть", valign=Gtk.Align.CENTER)
        b.connect("clicked", lambda *_: self.apply_look(["reset"]))
        self.look_btns["reset"] = b
        row.add_suffix(b)
        g.add(row)
        page.add(g)

    def apply_look(self, args: list[str]):
        cmd = [os.environ.get("NIXOS_KDE_LOOK", "nixos-kde-look"), *args]

        def work():
            r = subprocess.run(cmd, capture_output=True, text=True)
            GLib.idle_add(self.toast, "Вид применён" if r.returncode == 0 else "Не получилось сменить вид")
        threading.Thread(target=work, daemon=True).start()

    # ── Загрузка и безопасность ──
    def build_boot(self, page: Adw.PreferencesPage):
        boot = self.choices.get("boot", {})
        g = Adw.PreferencesGroup(title="Secure Boot",
                                 description="Безопасная загрузка с вашими ключами и ключами Microsoft — "
                                             "Windows и игры с античитом продолжат работать.")
        state = "включена подпись загрузки" if boot.get("secureBoot") else "выключено"
        row = Adw.ActionRow(title="Состояние", subtitle=state)
        self.sb_btn = Gtk.Button(label="Настроить", valign=Gtk.Align.CENTER)
        self.sb_btn.connect("clicked", lambda *_: self.secureboot())
        row.add_suffix(self.sb_btn)
        g.add(row)
        g.add(Adw.ActionRow(title="Как это работает", subtitle=(
            "1. «Настроить» создаст ключи. 2. Если программа попросит — в BIOS включите Setup Mode "
            "(«Удалить ключи Secure Boot») и снова нажмите «Настроить». 3. В BIOS включите Secure Boot.")))
        page.add(g)

        gw = Adw.PreferencesGroup(title="Windows в меню загрузки")
        for w in boot.get("windows", []):
            r = Adw.ActionRow(title=w.get("name", "Windows"), subtitle=f"раздел EFI {w['esp']}")
            b = Gtk.Button(label="Убрать", valign=Gtk.Align.CENTER, css_classes=["destructive-action"])
            b.connect("clicked", lambda _b, esp=w["esp"]: self.set_windows(
                [x for x in boot.get("windows", []) if x["esp"] != esp]))
            r.add_suffix(b)
            gw.add(r)
        find = Adw.ActionRow(title="Найти Windows", subtitle="Поиск на дисках и добавление в меню загрузки")
        self.find_btn = Gtk.Button(label="Найти", valign=Gtk.Align.CENTER)
        self.find_btn.connect("clicked", lambda *_: self.find_windows())
        find.add_suffix(self.find_btn)
        gw.add(find)
        page.add(gw)

        gt = Adw.PreferencesGroup(title="Диск без пароля (TPM2)",
                                  description="Зашифрованный диск открывается сам, пока не меняли загрузку. "
                                              "Пароль остаётся запасным. Лучше после включения Secure Boot.")
        self.tpm_group = gt
        r = Adw.ActionRow(title="Зашифрованные диски", subtitle="Нажмите «Проверить»")
        b = Gtk.Button(label="Проверить", valign=Gtk.Align.CENTER)
        b.connect("clicked", lambda *_: self.check_status())
        r.add_suffix(b)
        gt.add(r)
        page.add(gt)

    def set_windows(self, windows: list[dict]):
        self.run_helper(["set"], "Меню загрузки", json.dumps({"boot": {"windows": windows}}),
                        done=lambda ok, _e: self.toast("Меню загрузки обновлено" if ok else "Не получилось"))

    def secureboot(self):
        def done(ok, events):
            need = [e for e in events if e.get("type") == "secureboot"]
            if need and need[-1].get("need") == "setup_mode":
                self.toast("Ключи готовы. Включите Setup Mode в BIOS и снова нажмите «Настроить»")
            elif need and need[-1].get("next") == "enable_in_bios":
                self.toast("Готово! Теперь включите Secure Boot в BIOS")
            elif ok:
                self.toast("Secure Boot настроен")
        self.run_helper(["secureboot-prepare"], "Secure Boot", done=done)

    def status(self) -> dict:
        r = subprocess.run(helper_cmd() + ["status"], capture_output=True, text=True)
        try:
            return json.loads(r.stdout)
        except ValueError:
            return {}

    def find_windows(self):
        def work():
            st = self.status()
            GLib.idle_add(self.show_found, st.get("windows", []))
        threading.Thread(target=work, daemon=True).start()

    def show_found(self, found: list[dict]):
        have = {w["esp"] for w in self.choices.get("boot", {}).get("windows", [])}
        new = [w for w in found if w["esp"] not in have]
        if not new:
            self.toast("Windows не найдена" if not found else "Windows уже в меню загрузки")
            return
        windows = self.choices.get("boot", {}).get("windows", []) + [{"name": "Windows", "esp": w["esp"]} for w in new]
        self.set_windows(windows)

    def check_status(self):
        def work():
            st = self.status()
            GLib.idle_add(self.show_tpm, st.get("luks", []))
        threading.Thread(target=work, daemon=True).start()

    def show_tpm(self, luks: list[dict]):
        if not luks:
            self.toast("Зашифрованных дисков нет — TPM2 не нужен")
            return
        for d in luks:
            r = Adw.ActionRow(title=d["device"], subtitle="привязан к TPM2" if d["tpm2"] else "открывается паролем")
            if d["tpm2"]:
                b = Gtk.Button(label="Отвязать", valign=Gtk.Align.CENTER)
                b.connect("clicked", lambda _b, dev=d["device"]: self.run_helper(["tpm2-wipe", dev], "TPM2"))
            else:
                b = Gtk.Button(label="Привязать", valign=Gtk.Align.CENTER, css_classes=["suggested-action"])
                b.connect("clicked", lambda _b, dev=d["device"]: self.ask_password(dev))
            r.add_suffix(b)
            self.tpm_group.add(r)

    def ask_password(self, dev: str):
        dlg = Adw.AlertDialog(heading="Пароль диска", body=f"Введите пароль шифрования {dev}")
        entry = Gtk.PasswordEntry(show_peek_icon=True)
        dlg.set_extra_child(entry)
        dlg.add_response("cancel", "Отмена")
        dlg.add_response("ok", "Привязать")
        dlg.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)

        def resp(_d, r):
            if r == "ok" and entry.get_text():
                self.run_helper(["tpm2-enroll", dev], "TPM2", stdin=entry.get_text() + "\n")
        dlg.connect("response", resp)
        dlg.present(self)


    # ── Обновление ──
    def build_update(self, page: Adw.PreferencesPage):
        g = Adw.PreferencesGroup(title="Обновление системы",
                                 description="Новые версии программ и системы. Если после обновления что-то "
                                             "сломалось — «Откатить» вернёт прежнюю версию.")
        self.upd_row = Adw.ActionRow(title="Проверить обновления", subtitle="Нажмите «Проверить»")
        self.check_btn = Gtk.Button(label="Проверить", valign=Gtk.Align.CENTER)
        self.check_btn.connect("clicked", lambda *_: self.check())
        self.upd_btn = Gtk.Button(label="Обновить", valign=Gtk.Align.CENTER, css_classes=["suggested-action"])
        self.upd_btn.connect("clicked", lambda *_: self.update())
        self.upd_row.add_suffix(self.check_btn)
        self.upd_row.add_suffix(self.upd_btn)
        g.add(self.upd_row)
        page.add(g)
        self.gen_group = Adw.PreferencesGroup(title="Предыдущие версии системы",
                                              description="Каждое обновление и изменение настроек сохраняет "
                                                          "версию; к любой можно вернуться.")
        page.add(self.gen_group)
        threading.Thread(target=self.load_generations, daemon=True).start()

    def check(self):
        self.upd_row.set_subtitle("Проверяю…")

        def work():
            r = check_updates()
            if not r["online"]:
                msg = "Нет интернета — проверить не удалось"
            elif r["system"] or r["flatpaks"]:
                parts = (["система"] if r["system"] else []) + ([f"программы Flathub: {r['flatpaks']}"]
                                                               if r["flatpaks"] else [])
                msg = "Есть обновления: " + ", ".join(parts)
            else:
                msg = "Всё обновлено"
            GLib.idle_add(self.upd_row.set_subtitle, msg)
        threading.Thread(target=work, daemon=True).start()

    def update(self):
        def done(ok, _e):
            if ok:
                subprocess.Popen([os.environ.get("NIXOS_STORE_FLATPAK", "flatpak"), "update", "--user", "-y",
                                  "--noninteractive"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.toast("Система обновлена — перезагрузите компьютер" if ok else "Обновление не удалось, "
                       "система осталась прежней")
        self.run_helper(["update"], "Обновление системы", done=done)

    def load_generations(self):
        try:
            gens = json.loads(subprocess.run(helper_direct() + ["generations"], capture_output=True,
                                             text=True, timeout=30).stdout)
        except (OSError, ValueError, subprocess.SubprocessError):
            gens = []
        GLib.idle_add(self.show_generations, gens)

    def show_generations(self, gens):
        self.gen_buttons = {}
        for gen in gens[:10]:
            when = datetime.datetime.fromtimestamp(gen["date"]).strftime("%d.%m.%Y %H:%M")
            row = Adw.ActionRow(title=f"Версия {gen['number']} — {when}",
                                subtitle=("сейчас работает · " if gen["current"] else "") + gen.get("version", ""))
            if not gen["current"]:
                b = Gtk.Button(label="Откатить", valign=Gtk.Align.CENTER)
                b.connect("clicked", lambda _b, n=gen["number"]: self.run_helper(
                    ["rollback", str(n)], f"Возврат к версии {n}",
                    done=lambda ok, _e: self.toast("Готово — перезагрузите компьютер" if ok else "Не получилось")))
                row.add_suffix(b)
                self.gen_buttons[gen["number"]] = b
            self.gen_group.add(row)
        return False


def make_app(on_window=None) -> Adw.Application:
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


def main(argv: list[str]) -> int:
    return make_app().run(argv)
