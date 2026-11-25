from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QPushButton, QScrollArea, QVBoxLayout, QWidget

from ... import config
from ...backend.base import CONFLICTS
from ..widgets import HelpButton, HintRow, PowerRing, clear, label, row


class HomePage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)
        body = QWidget()
        body.setObjectName("page")
        scroll.setWidget(body)
        v = QVBoxLayout(body)
        v.setContentsMargins(40, 30, 40, 30)
        v.setSpacing(14)

        self.banners = QVBoxLayout()
        self.banners.setSpacing(10)
        v.addLayout(self.banners)

        hero = QHBoxLayout()
        hero.setSpacing(34)
        self.power = PowerRing()
        self.power.clicked.connect(win.power_toggle)
        hero.addWidget(self.power, 0, Qt.AlignVCenter)
        text = QVBoxLayout()
        text.setSpacing(8)
        text.addStretch(1)
        self.title = label("", "statusTitle")
        self.sub = label("", "lead")
        text.addWidget(self.title)
        text.addWidget(self.sub)
        self.autostart = QCheckBox("Включать обход вместе с компьютером")
        self.autostart.toggled.connect(self._autostart)
        text.addSpacing(6)
        text.addWidget(row(self.autostart, HelpButton(
            "Если включено, обход заработает сам после перезагрузки — даже если эту программу не открывать.\n"
            "Выключишь обход кнопкой — после перезагрузки он тоже останется выключенным."), None))
        text.addStretch(1)
        hero.addLayout(text, 1)
        v.addLayout(hero)

        v.addSpacing(10)
        v.addWidget(label("Подсказки", "h2"))
        self.hints = QVBoxLayout()
        self.hints.setSpacing(10)
        v.addLayout(self.hints)
        v.addStretch(1)

        win.status_changed.connect(self.on_status)
        win.busy_changed.connect(lambda b: self.on_status(win.status))
        win.remote_changed.connect(lambda v: self.on_status(win.status))

    def _autostart(self, on):
        if self._syncing or on == self.win.status.autostart:
            return
        self.win.task("Сохраняю автозапуск", lambda log, emit: self.win.backend.set_autostart(on, log))

    _syncing = False

    def on_status(self, st):
        win = self.win
        if win.busy:
            self.power.set_state("busy")
            self.title.setText("Минутку…")
            self.sub.setText(win.task_title)
        elif not st.installed:
            self.power.set_state("absent")
            self.title.setText("Ещё не установлено")
            size = "около 2 МБ" if config.IS_WINDOWS else "около 10 МБ"
            self.sub.setText(f"Нажми на кнопку: программа скачает zapret и стратегии Flowseal ({size}) "
                             "и сразу включит обход.")
        elif st.running:
            self.power.set_state("on")
            self.title.setText("Обход работает")
            self.sub.setText(f"Discord и YouTube должны открываться.\nСтратегия: {st.strategy}")
        else:
            self.power.set_state("off")
            self.title.setText("Обход выключен")
            self.sub.setText(f"Нажми на кнопку, чтобы включить.\nСтратегия: {st.strategy}")
        self.power.setToolTip("Выключить обход" if st.running else "Включить обход")
        self._syncing = True
        self.autostart.setChecked(st.autostart)
        self.autostart.setEnabled(st.installed and not win.busy)
        self._syncing = False
        self._banners(st)
        self._hints(st)

    def _banners(self, st):
        clear(self.banners)
        if self.win.update_available():
            b = QFrame()
            b.setObjectName("banner")
            h = QHBoxLayout(b)
            h.setContentsMargins(18, 12, 14, 12)
            h.addWidget(label(f"Вышли новые стратегии Flowseal {self.win.remote_version} "
                              f"(у тебя {st.versions.get('flowseal')}). Обновление займёт полминуты."), 1)
            btn = QPushButton("Обновить")
            btn.setObjectName("primary")
            btn.setEnabled(not self.win.busy)
            btn.clicked.connect(self.win.update_flowseal)
            h.addWidget(btn)
            self.banners.addWidget(b)

    def _hints(self, st):
        win, be = self.win, self.win.backend
        clear(self.hints)
        add = self.hints.addWidget
        for cid in st.conflicts:
            title, detail, fix = CONFLICTS[cid]
            add(HintRow("error", title, detail, fix, lambda _=False, c=cid: win.task(
                "Убираю конфликт", lambda log, emit: be.fix(c, log))))
        if not st.installed:
            add(HintRow("tip", "Что делает эта программа",
                        "Обманывает блокировку провайдера (DPI), чтобы работали Discord и YouTube. "
                        "Это не VPN: трафик идёт напрямую, скорость не падает."))
            return
        results = be.results()
        best = be.recommended()
        if not results:
            add(HintRow("tip", "Не знаешь, какую стратегию выбрать?",
                        "Тест по очереди проверит все стратегии на Discord, YouTube и Google и подскажет лучшую. "
                        "Займёт 3–5 минут, на это время обход выключится.",
                        "Подобрать стратегию", self._run_all_tests))
        elif best and best != st.strategy:
            r = results[best]
            add(HintRow("tip", f"Лучше всего у тебя работает «{best}»",
                        f"По последнему тесту: {r['ok']} из {r['total']} проверок"
                        + (f", задержка {r['ping']} мс." if r.get("ping") else "."),
                        "Включить её", lambda: win.apply_state({"strategy": best}, f"Включаю «{best}»")))
        elif best == st.strategy:
            add(HintRow("ok", "Стратегия подобрана", f"«{best}» лучше всех прошла последний тест."))
        if st.running:
            add(HintRow("tip", "Discord не подключается к голосовому чату?",
                        "Включи игровой фильтр «UDP» в разделе «Стратегии» и полностью перезапусти Discord "
                        "(правой кнопкой по значку в трее → Выйти).",
                        "К настройкам", lambda: win.show_page("strategies")))
            add(HintRow("tip", "YouTube всё равно тормозит?",
                        "Попробуй соседнюю стратегию или запусти тест — у разных провайдеров работают разные.",
                        "К стратегиям", lambda: win.show_page("strategies")))
        add(HintRow("tip", "Telegram не грузит фото или тормозит?",
                    "Включи TG WS Proxy от Flowseal или выбери быстрый сервер MTProto из списка.",
                    "Открыть", lambda: win.show_page("telegram")))

    def _run_all_tests(self):
        self.win.show_page("strategies")
        self.win.pages["strategies"].start_tests(None)
