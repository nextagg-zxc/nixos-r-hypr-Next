from PySide6.QtWidgets import QGridLayout, QMessageBox, QPushButton, QVBoxLayout, QWidget

from ... import VERSION, config, tgws, updates
from .. import worker
from ..widgets import Card, HelpButton, label, row, scrolled


class UpdatesPage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        body = QWidget()
        outer.addWidget(scrolled(body))
        v = QVBoxLayout(body)
        v.setContentsMargins(40, 30, 40, 26)
        v.setSpacing(14)
        v.addWidget(label("Обновления", "h1"))
        v.addWidget(label("Когда провайдер меняет блокировку, Flowseal выпускает новые стратегии. Программа "
                          "проверяет это при каждом запуске и предложит обновиться.", "lead"))

        card = Card()
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        for c, h in enumerate(["", "Установлено", "Последняя"]):
            grid.addWidget(label(h, "small"), 0, c)
        self.cells = {}
        names = [("flowseal", "Стратегии Flowseal"), ("tgws", "TG WS Proxy"), ("app", "Zapret Hub")]
        if not config.IS_WINDOWS:
            names.insert(1, ("zapret", "zapret (nfqws)"))
        for r, (k, title) in enumerate(names, start=1):
            grid.addWidget(label(title, wrap=False), r, 0)
            self.cells[k] = (label("—", "muted", wrap=False), label("—", "muted", wrap=False))
            grid.addWidget(self.cells[k][0], r, 1)
            grid.addWidget(self.cells[k][1], r, 2)
        grid.setColumnStretch(3, 1)
        card.lay.addLayout(grid)
        self.check_btn = QPushButton("Проверить")
        self.check_btn.clicked.connect(self.check)
        self.update_btn = QPushButton("Обновить стратегии")
        self.update_btn.setObjectName("primary")
        self.update_btn.clicked.connect(win.update_flowseal)
        card.lay.addWidget(row(self.check_btn, self.update_btn, None))
        v.addWidget(card)

        extra = Card()
        extra.lay.addWidget(label("Дополнительно", "h2"))
        ipset = QPushButton("Обновить список IP (IPSet)")
        ipset.clicked.connect(lambda: win.task("Обновляю IPSet", lambda log, emit: win.backend.ipset_update(log)))
        extra.lay.addWidget(row(ipset, HelpButton("Свежий список IP-адресов от Flowseal. Нужен, только если "
                                                  "в «Стратегиях» IPSet стоит «По списку Flowseal»."), None))
        hosts = QPushButton("Добавить hosts от Flowseal")
        hosts.clicked.connect(lambda: win.task("Обновляю hosts", lambda log, emit: win.backend.hosts("update", log)))
        unhosts = QPushButton("Убрать")
        unhosts.clicked.connect(lambda: win.task("Убираю записи hosts",
                                                 lambda log, emit: win.backend.hosts("remove", log)))
        extra.lay.addWidget(row(hosts, unhosts, HelpButton(
            "Flowseal ведёт файл hosts с адресами для сервисов, которые блокируют по DNS.\n"
            "Программа добавит их отдельным блоком и сможет так же аккуратно убрать. Старый hosts сохранится "
            "рядом с расширением .zapret-hub.bak."), None))
        remove = QPushButton("Удалить zapret и все настройки")
        remove.setObjectName("danger")
        remove.clicked.connect(self.uninstall)
        extra.lay.addWidget(row(remove, None))
        v.addWidget(extra)
        v.addStretch(1)
        win.status_changed.connect(lambda st: self.fill())
        win.remote_changed.connect(lambda r: self.fill())
        self.latest_tg = None
        self.fill()

    def on_show(self):
        self.fill()

    def fill(self):
        vs = self.win.status.versions
        rv = self.win.remote_version
        self.cells["flowseal"][0].setText(vs.get("flowseal") or "не установлено")
        self.cells["flowseal"][1].setText(rv or "—")
        if "zapret" in self.cells:
            self.cells["zapret"][0].setText(vs.get("zapret") or "не установлено")
            self.cells["zapret"][1].setText("обновится вместе со стратегиями")
        self.cells["tgws"][0].setText(tgws.installed_version() or "не установлен")
        self.cells["tgws"][1].setText(self.latest_tg or "—")
        self.cells["app"][0].setText(VERSION)
        self.cells["app"][1].setText("")
        avail = self.win.update_available()
        self.update_btn.setText("Обновить стратегии" if avail else "Переустановить стратегии")
        self.update_btn.setObjectName("primary" if avail else "")
        self.update_btn.style().polish(self.update_btn)

    def check(self):
        self.check_btn.setEnabled(False)

        def tg_done(tag):
            self.latest_tg = tag
            self.fill()
            installed = tgws.installed_version()
            if installed and updates.version_gt(tag, installed):
                self.win.statusBar().showMessage(f"Вышел TG WS Proxy {tag} — обнови его во вкладке Telegram", 8000)

        worker.start(lambda log, emit: tgws.latest_release()[0], tg_done, lambda e: None)
        self.win.check_remote(lambda v: (self.check_btn.setEnabled(True), self.fill(),
                                         self.win.statusBar().showMessage(
                                             "Стратегии свежие" if v and not self.win.update_available()
                                             else ("Есть обновление стратегий" if v else "Проверка не удалась"),
                                             5000)))

    def uninstall(self):
        r = QMessageBox.question(self, "Удалить zapret",
                                 "Выключить обход и удалить скачанные стратегии, списки и настройки?\n"
                                 "Саму программу потом можно просто удалить.")
        if r == QMessageBox.Yes:
            self.win.task("Удаляю zapret", lambda log, emit: self.win.backend.uninstall(log))
