import time

from PySide6.QtWidgets import QPlainTextEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget

from .. import worker
from ..widgets import HintRow, clear, label, row


class DiagnosticsPage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        v = QVBoxLayout(self)
        v.setContentsMargins(40, 30, 40, 26)
        v.setSpacing(12)
        v.addWidget(label("Диагностика", "h1"))
        v.addWidget(label("Проверка того, что обычно мешает zapret: другие обходы, VPN, антивирусы, настройки "
                          "сети. Где можно — исправим одной кнопкой.", "lead"))
        self.run_btn = QPushButton("Проверить")
        self.run_btn.setObjectName("primary")
        self.run_btn.clicked.connect(self.run)
        self.summary = label("", "muted", wrap=False)
        v.addWidget(row(self.run_btn, 10, self.summary, None))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        holder = QWidget()
        holder.setObjectName("page")
        self.list = QVBoxLayout(holder)
        self.list.setSpacing(8)
        self.list.addStretch(1)
        scroll.setWidget(holder)
        v.addWidget(scroll, 3)
        v.addWidget(label("Журнал действий", "h2"))
        self.logview = QPlainTextEdit()
        self.logview.setReadOnly(True)
        self.logview.setMaximumBlockCount(2000)
        v.addWidget(self.logview, 2)
        win.logged.connect(self.append)
        self.checked = False

    def append(self, msg):
        if msg:
            self.logview.appendPlainText(f"{time.strftime('%H:%M:%S')}  {msg}")

    def on_show(self):
        if not self.checked:
            self.run()

    def run(self):
        self.checked = True
        self.run_btn.setEnabled(False)
        self.summary.setText("Проверяю…")
        worker.start(lambda log, emit: self.win.backend.diagnostics(), self.show_checks, self._failed)

    def _failed(self, e):
        self.run_btn.setEnabled(True)
        self.summary.setText(f"Проверка не удалась: {e}")

    def show_checks(self, checks):
        self.run_btn.setEnabled(True)
        clear(self.list)
        order = {"error": 0, "warn": 1, "ok": 2}
        bad = [c for c in checks if c.level != "ok"]
        for c in sorted(checks, key=lambda c: order.get(c.level, 3)):
            cb = (lambda _=False, cid=c.id: self.fix(cid)) if c.fixable else None
            self.list.addWidget(HintRow(c.level, c.title, c.detail, c.fix_label if c.fixable else None, cb))
        self.list.addStretch(1)
        self.summary.setText("Всё в порядке" if not bad else
                             f"Нашлось: {len(bad)}. Начни сверху — красное мешает сильнее всего.")

    def fix(self, cid):
        self.win.task("Исправляю", lambda log, emit: self.win.backend.fix(cid, log), done=lambda r: self.run())
