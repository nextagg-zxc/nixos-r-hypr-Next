"""Main window: side navigation, page stack, one background task at a time,
status polling, Flowseal update check, friendly error dialogs."""

import json
import os

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QButtonGroup, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
                               QPushButton, QStackedWidget, QVBoxLayout, QWidget)

from .. import VERSION, config, updates
from ..backend.base import CONFLICTS, ConflictError, Status
from . import icons, worker
from .theme import ASSETS, C

NAV = [("home", "Главная", "power"), ("strategies", "Стратегии", "sliders"), ("telegram", "Telegram", "send"),
       ("lists", "Списки сайтов", "list"), ("updates", "Обновления", "refresh"), ("diagnostics", "Диагностика", "pulse")]


def load_settings():
    try:
        with open(config.USER_SETTINGS, encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(d):
    os.makedirs(config.USER_DIR, exist_ok=True)
    with open(config.USER_SETTINGS, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


class MainWindow(QMainWindow):
    status_changed = Signal(object)
    remote_changed = Signal(object)
    busy_changed = Signal(bool)
    logged = Signal(str)

    def __init__(self, backend, check_updates=True):
        super().__init__()
        self.backend = backend
        self.busy = False
        self.task_title = ""
        self.status = Status()
        self.remote_version = None
        self.settings = load_settings()
        self._polling = False
        self.setWindowTitle("Zapret Hub")
        self.setWindowIcon(QIcon(os.path.join(ASSETS, "icon.svg")))
        self.setMinimumSize(980, 640)

        root = QWidget()
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        h.addWidget(self._sidebar())
        self.stack = QStackedWidget()
        h.addWidget(self.stack, 1)
        self.setCentralWidget(root)

        from .pages.diagnostics import DiagnosticsPage
        from .pages.home import HomePage
        from .pages.lists import ListsPage
        from .pages.strategies import StrategiesPage
        from .pages.telegram import TelegramPage
        from .pages.updates import UpdatesPage
        classes = {"home": HomePage, "strategies": StrategiesPage, "telegram": TelegramPage, "lists": ListsPage,
                   "updates": UpdatesPage, "diagnostics": DiagnosticsPage}
        self.pages = {}
        for key, _, _ in NAV:
            page = classes[key](self)
            page.setObjectName("page")
            self.pages[key] = page
            self.stack.addWidget(page)
        self.statusBar().showMessage(f"Zapret Hub {VERSION}")

        self.refresh_status(sync=True)
        self.timer = QTimer(self, interval=5000, timeout=self.refresh_status)
        self.timer.start()
        if check_updates:
            QTimer.singleShot(1500, self.check_remote)
        self.show_page("home")

    # ------------------------------------------------------------ layout
    def _sidebar(self):
        side = QWidget()
        side.setObjectName("side")
        side.setFixedWidth(232)
        v = QVBoxLayout(side)
        v.setContentsMargins(16, 22, 16, 16)
        v.setSpacing(4)
        brand = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(QIcon(os.path.join(ASSETS, "icon.svg")).pixmap(36, 36))
        brand.addWidget(logo)
        names = QVBoxLayout()
        names.setSpacing(0)
        t = QLabel("Zapret Hub")
        t.setObjectName("brand")
        s = QLabel("обход блокировок")
        s.setObjectName("brandSub")
        names.addWidget(t)
        names.addWidget(s)
        brand.addLayout(names, 1)
        v.addLayout(brand)
        v.addSpacing(22)
        self.nav = {}
        group = QButtonGroup(self)
        group.setExclusive(True)
        for key, text, ic in NAV:
            b = QPushButton(text)
            b.setObjectName("nav")
            b.setCheckable(True)
            b.setIcon(icons.icon(ic, C["muted"]))
            b.setIconSize(QSize(20, 20))
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, k=key: self.show_page(k))
            group.addButton(b)
            v.addWidget(b)
            self.nav[key] = b
        v.addStretch(1)
        self.side_state = QLabel("")
        self.side_state.setObjectName("small")
        self.side_state.setWordWrap(True)
        v.addWidget(self.side_state)
        return side

    def page_keys(self):
        return [k for k, _, _ in NAV]

    def show_page(self, key):
        self.stack.setCurrentWidget(self.pages[key])
        self.nav[key].setChecked(True)
        for k, b in self.nav.items():
            b.setIcon(icons.icon(dict((n, i) for n, _, i in NAV)[k], C["teal"] if k == key else C["muted"]))
        page = self.pages[key]
        if hasattr(page, "on_show"):
            page.on_show()

    # ------------------------------------------------------------ tasks
    def task(self, title, fn, done=None, on_event=None, failed=None):
        """Run fn(log, emit) in the background; one at a time."""
        if self.busy:
            self.statusBar().showMessage(f"Подожди — ещё идёт: {self.task_title}", 4000)
            return None
        self.busy, self.task_title = True, title
        self.busy_changed.emit(True)
        self.statusBar().showMessage(title + "…")
        self.log(f"— {title}")
        if self.backend.needs_admin_prompt and not self.settings.get("pw_hint"):
            self.settings["pw_hint"] = True
            self.log("Система спросит пароль: он нужен, чтобы менять сетевые правила.")

        def ok(res):
            self._finish()
            self.statusBar().showMessage(f"{title}: готово", 5000)
            if done:
                done(res)

        def bad(e):
            self._finish()
            self.log(f"Ошибка: {e}")
            if failed:
                failed(e)
            else:
                self.fail(e, title)
        return worker.start(fn, ok, bad, self.log, on_event)

    def _finish(self):
        self.busy, self.task_title = False, ""
        self.busy_changed.emit(False)
        self.refresh_status(sync=True)

    def log(self, msg):
        self.logged.emit(msg)
        if msg and not msg.startswith("—"):
            self.statusBar().showMessage(msg, 6000)

    def fail(self, e, title=""):
        if isinstance(e, ConflictError):
            return self.ask_fix_conflicts(e.ids, retry=self.power_on)
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Не получилось")
        box.setText(f"<b>{title or 'Ошибка'}</b>")
        box.setInformativeText(str(e) or type(e).__name__)
        trace = getattr(e, "trace", "")
        if trace and not isinstance(e, RuntimeError):
            box.setDetailedText(trace)
        box.exec()

    def ask_fix_conflicts(self, ids, retry=None):
        text = "\n\n".join(f"• {CONFLICTS[i][0]}\n{CONFLICTS[i][1]}" for i in ids)
        r = QMessageBox.question(self, "Мешают другие программы",
                                 f"Перед включением нужно убрать конфликты:\n\n{text}\n\nИсправить и включить обход?")
        if r != QMessageBox.Yes:
            return

        def fn(log, emit):
            for i in ids:
                self.backend.fix(i, log)
            if retry:
                self.backend.start(log)
        self.task("Убираю конфликты и включаю обход", fn)

    # ------------------------------------------------------------ status
    def refresh_status(self, sync=False):
        if sync:
            try:
                self._set_status(self.backend.status())
            except Exception as e:  # noqa: BLE001
                self.log(f"Не удалось узнать состояние: {e}")
            return
        if self._polling or self.busy:
            return
        self._polling = True

        def done(st):
            self._polling = False
            self._set_status(st)

        def bad(e):
            self._polling = False
        worker.start(lambda log, emit: self.backend.status(), done, bad)

    def _set_status(self, st):
        self.status = st
        v = st.versions.get("flowseal")
        self.side_state.setText(f"Версия {VERSION}" + (f"\nСтратегии Flowseal {v}" if v else ""))
        self.status_changed.emit(st)

    def update_available(self):
        cur = self.status.versions.get("flowseal")
        return bool(self.remote_version and cur and updates.version_gt(self.remote_version, cur))

    def check_remote(self, on_done=None):
        def done(v):
            self.remote_version = v
            self.remote_changed.emit(v)
            if on_done:
                on_done(v)

        def bad(e):
            self.log(f"Не удалось проверить обновления: {e}")
            if on_done:
                on_done(None)
        worker.start(lambda log, emit: updates.flowseal_remote_version(), done, bad)

    # ------------------------------------------------------------ actions
    def power_toggle(self):
        if self.status.running:
            self.task("Выключаю обход", lambda log, emit: self.backend.stop(log))
        else:
            self.power_on()

    def power_on(self):
        def fn(log, emit):
            if not self.backend.is_installed():
                self.backend.install(log)
            self.backend.start(log)
        self.task("Включаю обход" if self.status.installed else "Устанавливаю и включаю обход", fn)

    def apply_state(self, changes, title="Сохраняю настройки"):
        self.task(title, lambda log, emit: self.backend.set_state(changes, log))

    def update_flowseal(self):
        self.task("Обновляю стратегии Flowseal", lambda log, emit: self.backend.update(log),
                  done=lambda r: self.check_remote())

    def closeEvent(self, e):
        try:
            save_settings(self.settings)
        except OSError:
            pass
        tray = getattr(self, "tray", None)
        if tray and tray.isVisible() and self.settings.get("close_to_tray"):
            e.ignore()
            self.hide()
            return
        QApplication.instance().quit()
        super().closeEvent(e)
