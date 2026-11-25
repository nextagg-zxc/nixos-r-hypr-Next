"""Tray icon: quick on/off while the window is open or hidden."""

import os

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from .theme import ASSETS


def setup(win):
    if not QSystemTrayIcon.isSystemTrayAvailable():
        return None
    tray = QSystemTrayIcon(QIcon(os.path.join(ASSETS, "icon.svg")), win)
    menu = QMenu()
    show = QAction("Открыть Zapret Hub", menu)
    show.triggered.connect(lambda: (win.showNormal(), win.raise_(), win.activateWindow()))
    toggle = QAction("Включить обход", menu)
    toggle.triggered.connect(win.power_toggle)
    hide = QAction("Сворачивать в трей при закрытии", menu, checkable=True)
    hide.setChecked(bool(win.settings.get("close_to_tray")))

    def set_hide(on):
        win.settings["close_to_tray"] = on
    hide.toggled.connect(set_hide)
    quit_ = QAction("Выйти", menu)
    quit_.triggered.connect(lambda: (win.settings.update(close_to_tray=False), win.close()))
    for a in (show, toggle):
        menu.addAction(a)
    menu.addSeparator()
    menu.addAction(hide)
    menu.addAction(quit_)
    tray.setContextMenu(menu)
    tray.activated.connect(lambda r: show.trigger() if r == QSystemTrayIcon.Trigger else None)

    def on_status(st):
        toggle.setText("Выключить обход" if st.running else "Включить обход")
        toggle.setEnabled(not win.busy)
        tray.setToolTip("Zapret Hub — обход " + ("работает" if st.running else "выключен"))
    win.status_changed.connect(on_status)
    win.busy_changed.connect(lambda b: on_status(win.status))
    on_status(win.status)
    tray.show()
    win.tray = tray
    return tray
