from PySide6.QtWidgets import QPlainTextEdit, QPushButton, QTabWidget, QVBoxLayout, QWidget

from ..widgets import HintRow, label, row

LISTS = [
    ("list-general-user.txt", "Обходить эти сайты",
     "Если какой-то сайт не открывается, а Discord и YouTube работают — добавь его сюда. "
     "Можно вставлять ссылки целиком, программа сама оставит домен. Поддомены включаются автоматически.",
     "rutracker.org\nexample.com"),
    ("list-exclude-user.txt", "Не трогать эти сайты",
     "Сайты, которые начали работать хуже с обходом (банки, госуслуги и т.п.). Для них обход отключится.",
     "sberbank.ru\ngosuslugi.ru"),
    ("ipset-exclude-user.txt", "Не трогать эти IP-адреса",
     "IP-адреса или подсети, которые нужно исключить. Обычно нужно только для игровых серверов, "
     "если с включённым IPSet что-то сломалось.", "192.168.0.0/16\n203.0.113.5"),
]


class ListsPage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        v = QVBoxLayout(self)
        v.setContentsMargins(40, 30, 40, 26)
        v.setSpacing(12)
        v.addWidget(label("Списки сайтов", "h1"))
        v.addWidget(label("Основные списки Discord, YouTube и Google ведёт Flowseal и обновляет вместе со "
                          "стратегиями. Здесь — твои собственные добавки, обновления их не затрут.", "lead"))
        self.tabs = QTabWidget()
        self.edits = {}
        for name, title, hint, example in LISTS:
            w = QWidget()
            lay = QVBoxLayout(w)
            lay.setContentsMargins(0, 14, 0, 0)
            lay.setSpacing(10)
            lay.addWidget(HintRow("tip", title, hint))
            ed = QPlainTextEdit()
            ed.setPlaceholderText("По одному в строке, например:\n" + example)
            lay.addWidget(ed, 1)
            save = QPushButton("Сохранить")
            save.setObjectName("primary")
            save.clicked.connect(lambda _=False, n=name: self.save(n))
            lay.addWidget(row(label("Если обход включён, он перезапустится на секунду.", "small"), None, save))
            self.tabs.addTab(w, title)
            self.edits[name] = ed
        v.addWidget(self.tabs, 1)
        self.loaded = False

    def on_show(self):
        if not self.loaded:
            self.loaded = True
            for name, ed in self.edits.items():
                ed.setPlainText(self.win.backend.read_user_list(name))

    def save(self, name):
        if not self.win.status.installed:
            return self.win.fail(RuntimeError("Сначала включи обход на Главной — программа создаст списки."),
                                 "Списки")
        text = self.edits[name].toPlainText()
        self.win.task("Сохраняю список", lambda log, emit: self.win.backend.write_list(name, text, log),
                      done=lambda r: self.edits[name].setPlainText(self.win.backend.read_user_list(name)))
