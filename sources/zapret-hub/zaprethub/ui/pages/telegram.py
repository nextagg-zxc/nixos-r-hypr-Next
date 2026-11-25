import os
import time

from PySide6.QtGui import QBrush, QColor, QGuiApplication
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QHeaderView,
                               QInputDialog, QLineEdit, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
                               QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget)

from ... import mtproto, tgws
from .. import icons, worker
from ..theme import C
from ..widgets import Card, HelpButton, HintRow, label, row, scrolled

STALE_AFTER = 6 * 3600


class TelegramPage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        v = QVBoxLayout(self)
        v.setContentsMargins(40, 30, 40, 26)
        v.setSpacing(12)
        v.addWidget(label("Telegram", "h1"))
        v.addWidget(label("Два способа ускорить Telegram: свой локальный прокси от Flowseal (самый надёжный) "
                          "или готовый сервер MTProto из открытых списков.", "lead"))
        tabs = QTabWidget()
        self.ws = WsTab(win)
        self.servers = ServersTab(win)
        tabs.addTab(scrolled(self.ws), "TG WS Proxy")
        tabs.addTab(self.servers, "Серверы MTProto")
        v.addWidget(tabs, 1)

    def on_show(self):
        self.ws.refresh()
        self.servers.on_show()


# ---------------------------------------------------------------- TG WS Proxy

class WsTab(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.busy = False
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 14, 0, 0)
        v.setSpacing(12)

        status = Card()
        self.state = label("", "h2")
        self.detail = label("", "muted")
        status.lay.addWidget(self.state)
        status.lay.addWidget(self.detail)
        self.install_btn = QPushButton()
        self.install_btn.clicked.connect(self.install)
        self.run_btn = QPushButton()
        self.run_btn.clicked.connect(self.toggle)
        self.connect_btn = QPushButton("Подключить в Telegram")
        self.connect_btn.setObjectName("primary")
        self.connect_btn.setIcon(icons.icon("send", "#062a23"))
        self.connect_btn.setToolTip("Откроет Telegram Desktop и предложит включить этот прокси")
        self.connect_btn.clicked.connect(self.connect_tg)
        self.copy_btn = QPushButton("Скопировать ссылку")
        self.copy_btn.setIcon(icons.icon("copy", C["muted"]))
        self.copy_btn.setToolTip("Ссылку можно отправить себе на телефон, если он в той же сети")
        self.copy_btn.clicked.connect(lambda: self._copy(tgws.proxy_url(tgws.load_config())))
        status.lay.addWidget(row(self.connect_btn, self.run_btn, self.copy_btn, None, self.install_btn))
        self.auto = QCheckBox("Запускать вместе с компьютером")
        self.auto.toggled.connect(self._auto)
        status.lay.addWidget(row(self.auto, HelpButton(
            "Прокси запустится сам при входе в систему и будет ждать Telegram в трее."), None))
        v.addWidget(status)

        v.addWidget(HintRow("tip", "Как это работает",
                            "TG WS Proxy принимает соединения Telegram на этом компьютере и отправляет их через "
                            "WebSocket — так их не замечает блокировка. Telegram при этом работает как обычно.\n"
                            "Если после подключения Telegram висит на «Соединение…», открой в нём Настройки → "
                            "Продвинутые → Тип соединения и выключи «Использовать IPv6»."))

        sett = Card()
        sett.lay.addWidget(label("Настройки прокси", "h2"))
        form = QFormLayout()
        form.setSpacing(10)
        self.port = QSpinBox()
        self.port.setRange(1024, 65535)
        self.secret = QLineEdit()
        self.secret.setMaxLength(32)
        regen = QPushButton("Новый")
        regen.setToolTip("Сгенерировать новый ключ. Потом нужно заново нажать «Подключить в Telegram».")
        regen.clicked.connect(lambda: self.secret.setText(os.urandom(16).hex()))
        self.dc = QPlainTextEdit()
        self.dc.setFixedHeight(70)
        form.addRow(row(label("Порт", wrap=False), HelpButton("Порт на этом компьютере. Меняй, только если "
                                                             "1443 занят другой программой."), None), self.port)
        form.addRow(row(label("Ключ (secret)", wrap=False), None), row(self.secret, regen))
        form.addRow(row(label("Адреса DC", wrap=False), HelpButton(
            "Через какие адреса Telegram ходить к серверам (формат DC:IP, по одному в строке).\n"
            "Обычно менять не нужно."), None), self.dc)
        sett.lay.addLayout(form)
        photo = QPushButton("Не грузятся фото и видео")
        photo.setToolTip("Добавит адрес для 4-го дата-центра Telegram, где хранится много медиа")
        photo.clicked.connect(self.photo_fix)
        save = QPushButton("Сохранить")
        save.clicked.connect(self.save)
        sett.lay.addWidget(row(photo, None, save))
        v.addWidget(sett)
        v.addStretch(1)
        self.refresh()

    def _copy(self, text):
        QGuiApplication.clipboard().setText(text)
        self.win.statusBar().showMessage("Ссылка скопирована", 3000)

    def refresh(self):
        inst = tgws.is_installed()
        running = inst and tgws.is_running()
        ver = tgws.installed_version()
        if not inst:
            self.state.setText("TG WS Proxy не установлен")
            self.detail.setText("Нажми «Установить» — скачаем последнюю версию с GitHub Flowseal (~20–55 МБ) "
                                "и проверим контрольную сумму.")
        elif running:
            self.state.setText("Прокси работает")
            self.detail.setText("Нажми «Подключить в Telegram», если ещё не подключал. Версия " + (ver or "?"))
        else:
            self.state.setText("Прокси остановлен")
            self.detail.setText("Запусти его, затем подключи в Telegram. Версия " + (ver or "?"))
        self.install_btn.setText("Обновить" if inst else "Установить")
        self.install_btn.setObjectName("" if inst else "primary")
        self.install_btn.style().polish(self.install_btn)
        self.run_btn.setText("Остановить" if running else "Запустить")
        self.run_btn.setVisible(inst)
        self.connect_btn.setEnabled(inst)
        self.copy_btn.setEnabled(inst)
        self.auto.blockSignals(True)
        self.auto.setChecked(inst and tgws.autostart_enabled())
        self.auto.setEnabled(inst)
        self.auto.blockSignals(False)
        cfg = tgws.load_config()
        self.port.setValue(int(cfg.get("port", 1443)))
        self.secret.setText(str(cfg.get("secret", "")))
        self.dc.setPlainText("\n".join(cfg.get("dc_ip", [])))
        for w in (self.install_btn, self.run_btn):
            w.setEnabled(not self.busy)

    def _job(self, title, fn):
        self.busy = True
        self.refresh()
        self.win.statusBar().showMessage(title + "…")

        def done(_r):
            self.busy = False
            self.refresh()
            self.win.statusBar().showMessage(title + ": готово", 4000)

        def bad(e):
            self.busy = False
            self.refresh()
            self.win.fail(e, title)
        worker.start(lambda log, emit: fn(), done, bad)

    def install(self):
        self._job("Скачиваю TG WS Proxy", lambda: tgws.install())

    def toggle(self):
        if tgws.is_running():
            self._job("Останавливаю прокси", tgws.stop)
        else:
            def go():
                tgws.ensure_config()
                tgws.start()
                time.sleep(1.5)
            self._job("Запускаю прокси", go)

    def connect_tg(self):
        cfg = tgws.ensure_config()
        if not tgws.is_running():
            tgws.start()
        tgws.open_tg_url(tgws.proxy_url(cfg))
        self.win.statusBar().showMessage("Открываю Telegram — нажми там «Подключить прокси»", 6000)

    def _auto(self, on):
        try:
            tgws.set_autostart(on)
        except OSError as e:
            self.win.fail(e, "Автозапуск TG WS Proxy")

    def photo_fix(self):
        lines = [l for l in self.dc.toPlainText().split() if l]
        for d in tgws.PHOTO_FIX_DC:
            if d not in lines:
                lines.append(d)
        self.dc.setPlainText("\n".join(lines))
        self.save()

    def save(self):
        try:
            dcs = tgws.parse_dc_lines(self.dc.toPlainText())
        except ValueError as e:
            return self.win.fail(e, "Настройки прокси")
        secret = self.secret.text().strip().lower()
        if len(secret) != 32 or any(c not in "0123456789abcdef" for c in secret):
            return self.win.fail(RuntimeError("Ключ должен состоять из 32 символов 0–9 и a–f. "
                                              "Нажми «Новый», чтобы получить правильный."), "Настройки прокси")
        cfg = tgws.load_config()
        changed = cfg.get("secret") != secret or int(cfg.get("port", 1443)) != self.port.value()
        cfg.update(port=self.port.value(), secret=secret, dc_ip=dcs)
        tgws.save_config(cfg)
        if tgws.is_running():
            self._job("Перезапускаю прокси", lambda: (tgws.stop(), time.sleep(1), tgws.start()))
        msg = "Сохранено" + (" — нажми «Подключить в Telegram» ещё раз, ссылка изменилась" if changed else "")
        self.win.statusBar().showMessage(msg, 6000)


# ---------------------------------------------------------------- public MTProto

COLS = ["", "Сервер", "Порт", "Тип", "Пинг", "Источник"]


class ServersTab(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.store = mtproto.Store()
        self.loading = False
        self.shown = []
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 14, 0, 0)
        v.setSpacing(10)
        self.best = HintRow("tip", "Список ещё не загружен", "Нажми «Обновить список».")
        self.best_box = QVBoxLayout()
        self.best_box.addWidget(self.best)
        v.addLayout(self.best_box)

        self.refresh_btn = QPushButton("Обновить список")
        self.refresh_btn.setIcon(icons.icon("refresh", C["muted"]))
        self.refresh_btn.setToolTip("Скачать свежие списки и проверить, какие серверы отвечают (около 20 секунд)")
        self.refresh_btn.clicked.connect(lambda: self.reload(download=True))
        self.check_btn = QPushButton("Проверить ещё раз")
        self.check_btn.clicked.connect(lambda: self.reload(download=False))
        self.alive_only = QCheckBox("Только рабочие")
        self.alive_only.setChecked(True)
        self.alive_only.toggled.connect(self.fill)
        self.fav_only = QCheckBox("Избранные")
        self.fav_only.toggled.connect(self.fill)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по адресу или источнику")
        self.search.textChanged.connect(self.fill)
        v.addWidget(row(self.refresh_btn, self.check_btn, 8, self.alive_only, self.fav_only, None, self.search))
        self.progress = QProgressBar()
        self.progress.setFixedHeight(8)
        self.progress.hide()
        v.addWidget(self.progress)

        self.table = QTableWidget(0, len(COLS))
        self.table.setHorizontalHeaderLabels(COLS)
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        for c in (0, 2, 3, 4, 5):
            hh.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.table.cellDoubleClicked.connect(lambda r, c: self.connect_selected())
        v.addWidget(self.table, 1)

        conn = QPushButton("Подключить")
        conn.setObjectName("primary")
        conn.setIcon(icons.icon("send", "#062a23"))
        conn.setToolTip("Откроет Telegram и предложит включить выбранный сервер")
        conn.clicked.connect(self.connect_selected)
        copy = QPushButton("Скопировать")
        copy.clicked.connect(self.copy_selected)
        fav = QPushButton("В избранное")
        fav.setIcon(icons.icon("star", C["amber"]))
        fav.clicked.connect(self.fav_selected)
        add = QPushButton("Добавить свой")
        add.setIcon(icons.icon("plus", C["muted"]))
        add.clicked.connect(self.add_custom)
        src = QPushButton("Источники")
        src.setObjectName("link")
        src.clicked.connect(self.edit_sources)
        v.addWidget(row(conn, copy, fav, None, add, src))
        v.addWidget(label("Публичные серверы держат незнакомые люди: они видят, к каким серверам Telegram ты "
                          "подключаешься, но не читают переписку. Для надёжности лучше TG WS Proxy.", "small"))
        self._first = True

    def on_show(self):
        if self._first:
            self._first = False
            self.fill()
            stale = not self.store.updated or time.time() - self.store.updated > STALE_AFTER
            if stale:
                self.reload(download=True)

    def reload(self, download=True):
        if self.loading:
            return
        self.loading = True
        for b in (self.refresh_btn, self.check_btn):
            b.setEnabled(False)
        self.progress.setRange(0, 0)
        self.progress.show()
        sources = list(self.store.sources)
        current = self.store.all()

        def fn(log, emit):
            errors = []
            if download:
                proxies, errors = mtproto.fetch_all(sources)
                if not proxies:
                    raise RuntimeError("Не удалось скачать ни один список:\n" + "\n".join(errors))
            else:
                proxies = [p for p in current if p.source != "Свой"]
            custom = [mtproto.Proxy(p.server, p.port, p.secret, p.source) for p in self.store.custom]
            checked = mtproto.check_all(custom + proxies,
                                        on_progress=lambda d, t: emit({"done": d, "total": t}))
            return checked, errors

        def progress(e):
            self.progress.setRange(0, e["total"])
            self.progress.setValue(e["done"])

        def done(res):
            checked, errors = res
            keys = {p.key for p in self.store.custom}
            self.store.custom = [p for p in checked if p.key in keys]
            self.store.set_list([p for p in checked if p.key not in keys])
            try:
                self.store.save()
            except OSError:
                pass
            self._end()
            if errors:
                self.win.log("Списки MTProto: " + "; ".join(errors))

        def bad(e):
            self._end()
            self.win.fail(e, "Список серверов")
        worker.start(fn, done, bad, on_event=progress)

    def _end(self):
        self.loading = False
        for b in (self.refresh_btn, self.check_btn):
            b.setEnabled(True)
        self.progress.hide()
        self.fill()

    def visible(self):
        q = self.search.text().strip().lower()
        out = []
        for p in sorted(self.store.all(), key=mtproto.sort_key):
            if self.alive_only.isChecked() and p.alive is False:
                continue
            if self.fav_only.isChecked() and p.key not in self.store.favorites:
                continue
            if q and q not in p.server.lower() and q not in p.source.lower():
                continue
            out.append(p)
        return out

    def fill(self):
        self.shown = self.visible()
        self.table.setRowCount(len(self.shown))
        star = icons.icon("star", C["amber"], 14)
        for r, p in enumerate(self.shown):
            cells = ["", p.server, str(p.port), p.kind,
                     (f"{p.ping:.0f} мс" if p.ping is not None else ("нет ответа" if p.alive is False else "—")),
                     p.source]
            for c, text in enumerate(cells):
                it = QTableWidgetItem(text)
                if c == 0 and p.key in self.store.favorites:
                    it.setIcon(star)
                if c == 4:
                    color = C["faint"] if p.ping is None else (C["teal"] if p.ping < 120 else
                                                               (C["amber"] if p.ping < 300 else C["coral"]))
                    it.setForeground(QBrush(QColor(color)))
                if c == 3:
                    it.setToolTip({"Fake TLS": "Маскируется под обычный HTTPS — лучше всего проходит блокировки",
                                   "Secure": "Шифрованный трафик со случайным размером пакетов",
                                   "Обычный": "Самый простой тип — блокируется чаще других"}[p.kind])
                self.table.setItem(r, c, it)
        alive = [p for p in self.store.all() if p.alive]
        clear_box(self.best_box)
        if alive:
            # the RU list is checked from Russia; then Fake TLS, then speed
            b = min(alive, key=lambda p: ("Россия" not in p.source, p.kind != "Fake TLS", p.ping))
            when = time.strftime("%H:%M", time.localtime(self.store.updated)) if self.store.updated else "?"
            self.best_box.addWidget(HintRow("ok", f"Рекомендуем: {b.server} ({b.ping:.0f} мс, {b.kind})",
                                            f"Рабочих серверов: {len(alive)} из {len(self.store.all())}, "
                                            f"проверено в {when}. Сначала советуем серверы из списка для России.",
                                            "Подключить", lambda: self._open(b)))
        elif self.store.all():
            self.best_box.addWidget(HintRow("warn", "Ни один сервер не ответил",
                                            "Проверь интернет или нажми «Обновить список» позже.",
                                            "Обновить", lambda: self.reload(True)))
        else:
            self.best_box.addWidget(HintRow("tip", "Список ещё не загружен",
                                            "Скачаем серверы из открытых списков и проверим, какие работают.",
                                            "Обновить список", lambda: self.reload(True)))

    def selected(self):
        r = self.table.currentRow()
        return self.shown[r] if 0 <= r < len(self.shown) else None

    def _open(self, p):
        tgws.open_tg_url(p.tg_url())
        self.win.statusBar().showMessage(f"Открываю Telegram с сервером {p.server} — нажми там «Подключить»", 6000)

    def connect_selected(self):
        p = self.selected()
        if p:
            self._open(p)
        else:
            self.win.statusBar().showMessage("Выбери сервер в таблице", 3000)

    def copy_selected(self):
        p = self.selected()
        if p:
            QGuiApplication.clipboard().setText(p.tg_url().replace("tg://", "https://t.me/"))
            self.win.statusBar().showMessage("Ссылка скопирована — её можно открыть и на телефоне", 4000)

    def fav_selected(self):
        p = self.selected()
        if p:
            self.store.toggle_favorite(p.key)
            self.store.save()
            self.fill()

    def add_custom(self):
        text, ok = QInputDialog.getText(self, "Свой сервер", "Вставь ссылку tg://proxy?… или https://t.me/proxy?…")
        if ok and text.strip():
            if self.store.add_custom(text.strip()):
                self.store.save()
                self.fill()
            else:
                QMessageBox.warning(self, "Свой сервер", "Это не похоже на ссылку MTProto-прокси.")

    def edit_sources(self):
        d = QDialog(self)
        d.setWindowTitle("Источники списков")
        lay = QVBoxLayout(d)
        lay.addWidget(label("Адреса текстовых списков с ссылками tg://proxy или t.me/proxy, по одному в строке. "
                            "Формат строки: Название | https://адрес", "muted"))
        ed = QPlainTextEdit("\n".join(f"{s['name']} | {s['url']}" for s in self.store.sources))
        ed.setMinimumSize(620, 200)
        lay.addWidget(ed)
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults)
        lay.addWidget(bb)
        bb.accepted.connect(d.accept)
        bb.rejected.connect(d.reject)
        from ... import config
        bb.button(QDialogButtonBox.RestoreDefaults).clicked.connect(
            lambda: ed.setPlainText("\n".join(f"{s['name']} | {s['url']}" for s in config.MTPROTO_SOURCES)))
        if d.exec() != QDialog.Accepted:
            return
        srcs = []
        for line in ed.toPlainText().splitlines():
            name, _, u = line.rpartition("|")
            u = u.strip()
            if u.startswith(("https://", "http://")):
                srcs.append({"name": name.strip() or u, "url": u})
        if srcs:
            self.store.sources = srcs
            self.store.save()
            self.reload(True)


def clear_box(box):
    while box.count():
        w = box.takeAt(0).widget()
        if w:
            w.deleteLater()

