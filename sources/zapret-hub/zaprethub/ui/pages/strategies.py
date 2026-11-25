import threading

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView, QProgressBar,
                               QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .. import icons
from ..theme import C
from ..widgets import Card, HelpButton, label, row

GAME = [("off", "Выключен"), ("tcp", "TCP"), ("udp", "UDP (голос Discord, игры)"), ("all", "TCP и UDP")]
IPSET = [("none", "Выключен"), ("loaded", "По списку Flowseal"), ("any", "Все адреса")]
GAME_HELP = ("Нужен, если не работают игры или голосовые каналы Discord.\n"
             "Пропускает через обход все порты выше 1024. Включай, только если что-то не работает:\n"
             "иногда это мешает другим программам.")
IPSET_HELP = ("Какие IP-адреса обходить, кроме сайтов из списков.\n"
              "• Выключен — только сайты из списков (лучше всего для начала).\n"
              "• По списку Flowseal — плюс адреса из списка Flowseal: помогает играм и сайтам за Cloudflare.\n"
              "• Все адреса — обход для всего подряд, может ломать другие сайты.")


class StrategiesPage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.cancel = threading.Event()
        self.items = {}
        v = QVBoxLayout(self)
        v.setContentsMargins(40, 30, 40, 26)
        v.setSpacing(14)
        v.addWidget(label("Стратегии", "h1"))
        v.addWidget(label("Стратегия — это способ обойти блокировку. Разным провайдерам подходят разные, "
                          "поэтому проще всего запустить тест: он проверит каждую и подскажет лучшую.", "lead"))

        self.test_all = QPushButton("Подобрать лучшую")
        self.test_all.setObjectName("primary")
        self.test_all.setToolTip("Проверит все стратегии на Discord, YouTube, Google и Cloudflare (3–5 минут).\n"
                                 "На время теста обход выключится, потом включится снова.")
        self.test_all.clicked.connect(lambda: self.start_tests(None))
        self.test_sel = QPushButton("Проверить выбранные")
        self.test_sel.clicked.connect(lambda: self.start_tests(self.selected()))
        self.stop_btn = QPushButton("Остановить тест")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.clicked.connect(self.cancel.set)
        self.stop_btn.hide()
        self.best_btn = QPushButton("Включить лучшую")
        self.best_btn.clicked.connect(self.apply_best)
        v.addWidget(row(self.test_all, self.test_sel, self.stop_btn, None, self.best_btn))

        self.progress = QProgressBar()
        self.progress.setFixedHeight(8)
        self.progress.hide()
        self.progress_text = label("", "muted")
        self.progress_text.hide()
        v.addWidget(self.progress)
        v.addWidget(self.progress_text)

        body = QHBoxLayout()
        body.setSpacing(18)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Стратегия", "Проверки", "Задержка"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tree.itemDoubleClicked.connect(lambda it, _c: self.use(it.data(0, Qt.UserRole)))
        left = QVBoxLayout()
        left.addWidget(self.tree, 1)
        self.use_btn = QPushButton("Включить выбранную")
        self.use_btn.clicked.connect(lambda: self.use((self.selected() or [None])[0]))
        self.use_btn.setToolTip("Двойной щелчок по строке делает то же самое")
        left.addWidget(row(self.use_btn, None))
        body.addLayout(left, 3)

        card = Card()
        card.lay.addWidget(label("Настройки", "h2"))
        self.game = QComboBox()
        for k, t in GAME:
            self.game.addItem(t, k)
        self.game.activated.connect(lambda _i: self._changed("game_filter", self.game.currentData()))
        self.ipset = QComboBox()
        for k, t in IPSET:
            self.ipset.addItem(t, k)
        self.ipset.activated.connect(lambda _i: self._changed("ipset", self.ipset.currentData()))
        card.lay.addWidget(row(label("Игровой фильтр", wrap=False), HelpButton(GAME_HELP), None))
        card.lay.addWidget(self.game)
        card.lay.addSpacing(4)
        card.lay.addWidget(row(label("IPSet", wrap=False), HelpButton(IPSET_HELP), None))
        card.lay.addWidget(self.ipset)
        card.lay.addSpacing(8)
        card.lay.addWidget(label("Свои стратегии можно положить файлом .txt в папку strategies рядом с данными "
                                 "программы — они появятся в списке с пометкой «своя».", "small"))
        card.lay.addStretch(1)
        side = QWidget()
        side.setLayout(QVBoxLayout())
        side.layout().setContentsMargins(0, 0, 0, 0)
        side.layout().addWidget(card)
        side.setFixedWidth(320)
        body.addWidget(side, 2)
        v.addLayout(body, 1)

        win.status_changed.connect(self.refresh)
        win.busy_changed.connect(self._busy)
        self.refresh(win.status)

    # ------------------------------------------------------------ view
    def on_show(self):
        self.refresh(self.win.status)

    def refresh(self, st):
        be = self.win.backend
        results = be.results()
        best = be.recommended()
        cur_sel = set(self.selected())
        self.tree.clear()
        self.items = {}
        bold = QFont()
        bold.setBold(True)
        for name, kind in be.strategies():
            it = QTreeWidgetItem([name + ("  (своя)" if kind == "custom" else ""), "", ""])
            it.setData(0, Qt.UserRole, name)
            r = results.get(name)
            if r:
                self._set_result(it, r)
            if name == best:
                it.setIcon(0, icons.icon("star", C["amber"], 16))
                it.setToolTip(0, "Рекомендуем: лучше всех прошла последний тест")
            if name == st.strategy:
                it.setFont(0, bold)
                it.setForeground(0, QBrush(QColor(C["teal"])))
                it.setToolTip(0, "Эта стратегия сейчас выбрана" + (" и работает" if st.running else ""))
            self.tree.addTopLevelItem(it)
            self.items[name] = it
            if name in cur_sel:
                it.setSelected(True)
        self._sync_combo(self.game, st.game_filter)
        self._sync_combo(self.ipset, st.ipset)
        self.best_btn.setVisible(bool(best) and best != st.strategy)
        self.best_btn.setText(f"Включить лучшую: {best}" if best else "Включить лучшую")
        self._busy(self.win.busy)

    def _sync_combo(self, combo, value):
        i = combo.findData(value)
        if i >= 0:
            combo.setCurrentIndex(i)

    def _set_result(self, it, r):
        if r.get("error"):
            it.setText(1, "не запустилась")
            it.setForeground(1, QBrush(QColor(C["coral"])))
            it.setToolTip(1, r["error"])
            it.setText(2, "")
            return
        ok, total = r.get("ok", 0), r.get("total", 0)
        it.setText(1, f"{ok} из {total}")
        share = ok / total if total else 0
        color = C["teal"] if share >= 0.9 else (C["amber"] if share >= 0.5 else C["coral"])
        it.setForeground(1, QBrush(QColor(color)))
        it.setText(2, f"{r['ping']} мс" if r.get("ping") else "—")

    def result_text(self, name):
        it = self.items.get(name)
        return f"{name}: {it.text(1)}" if it else ""

    def selected(self):
        return [it.data(0, Qt.UserRole) for it in self.tree.selectedItems()]

    def _busy(self, busy):
        testing = busy and self.stop_btn.isVisible()
        for w in (self.test_all, self.test_sel, self.best_btn, self.use_btn, self.game, self.ipset):
            w.setEnabled(not busy)
        self.test_sel.setEnabled(not busy and bool(self.tree.selectedItems()) or False)
        self.stop_btn.setEnabled(testing)

    # ------------------------------------------------------------ actions
    def use(self, name):
        if name:
            self.win.apply_state({"strategy": name}, f"Включаю «{name}»")

    def apply_best(self):
        best = self.win.backend.recommended()
        if best:
            self.use(best)

    def _changed(self, key, value):
        if getattr(self.win.status, key) != value:
            self.win.apply_state({key: value})

    def start_tests(self, names):
        if not self.win.status.installed:
            self.win.fail(RuntimeError("Сначала включи обход на Главной — программа скачает стратегии."), "Тест")
            return
        names = names or [n for n, _ in self.win.backend.strategies()]
        self.cancel.clear()
        self.stop_btn.show()
        self.progress.setRange(0, len(names))
        self.progress.setValue(0)
        self.progress.show()
        self.progress_text.setText("Готовлю тест…")
        self.progress_text.show()
        for n in names:
            if n in self.items:
                self.items[n].setText(1, "в очереди")
                self.items[n].setForeground(1, QBrush(QColor(C["faint"])))
                self.items[n].setText(2, "")

        def done(_res):
            self.stop_btn.hide()
            self.progress.hide()
            self.refresh(self.win.status)

        def failed(e):
            done(None)
            self.progress_text.setText(f"Тест не удался: {e}")
            self.win.fail(e, "Тест стратегий")

        w = self.win.task("Тестирую стратегии",
                          lambda log, emit: self.win.backend.run_tests(names, emit, self.cancel),
                          done=done, on_event=self.on_event, failed=failed)
        if w is None:
            done(None)
        else:
            self.stop_btn.setEnabled(True)

    def on_event(self, e):
        t = e.get("type")
        it = self.items.get(e.get("name") or e.get("strategy"))
        if t == "strategy":
            self.progress.setValue(e["index"])
            self.progress_text.setText(f"Проверяю «{e['name']}» ({e['index'] + 1} из {e['total']})…")
            if it:
                it.setText(1, "проверяю…")
                it.setForeground(1, QBrush(QColor(C["violet"])))
                self.tree.scrollToItem(it)
        elif t in ("strategy_done", "strategy_error") and it:
            self._set_result(it, e)
            self.progress.setValue(self.progress.value() + 1)
        elif t == "done":
            best = e.get("best")
            self.progress_text.setText(("Тест остановлен. " if e.get("cancelled") else "Тест закончен. ")
                                       + (f"Лучше всех: «{best}» — нажми «Включить лучшую»." if best else
                                          "Ни одна стратегия не прошла — открой «Диагностику»."))
            self.progress_text.show()
        elif t == "log":
            self.win.log(e.get("text", ""))

