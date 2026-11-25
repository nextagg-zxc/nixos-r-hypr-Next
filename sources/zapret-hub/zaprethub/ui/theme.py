"""Colors, font and the Qt stylesheet. Night-ink surfaces; teal means "the
network is open", violet is the second accent from the icon."""

import os

from PySide6.QtGui import QColor, QFontDatabase, QPalette

ASSETS = os.path.join(os.path.dirname(__file__), "assets")

C = {
    "bg": "#121827",
    "side": "#0e1420",
    "surface": "#1a2236",
    "raised": "#232d45",
    "line": "#2c3754",
    "text": "#e6eaf4",
    "muted": "#97a1bb",
    "faint": "#5f6987",
    "teal": "#3ccfb0",
    "violet": "#8b7cf6",
    "amber": "#f0b35a",
    "coral": "#ee6b6b",
}
LEVEL_COLOR = {"ok": C["teal"], "warn": C["amber"], "error": C["coral"]}
FAMILY = "Manrope"


def load_fonts():
    global FAMILY
    fams = []
    for w in ("Regular", "SemiBold", "Bold", "ExtraBold"):
        fid = QFontDatabase.addApplicationFont(os.path.join(ASSETS, f"Manrope-{w}.ttf"))
        if fid >= 0:
            fams += QFontDatabase.applicationFontFamilies(fid)
    FAMILY = "Manrope" if "Manrope" in fams else ""
    return FAMILY


def palette():
    p = QPalette()
    for role, key in ((QPalette.Window, "bg"), (QPalette.Base, "surface"), (QPalette.AlternateBase, "raised"),
                      (QPalette.Button, "raised"), (QPalette.ToolTipBase, "raised")):
        p.setColor(role, QColor(C[key]))
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText, QPalette.ToolTipText):
        p.setColor(role, QColor(C["text"]))
    p.setColor(QPalette.PlaceholderText, QColor(C["faint"]))
    p.setColor(QPalette.Highlight, QColor(C["violet"]))
    p.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    return p


def stylesheet():
    f = f'"{FAMILY}", ' if FAMILY else ""
    CHECK = os.path.join(ASSETS, "check.svg").replace("\\", "/")
    return f"""
* {{ font-family: {f}"Segoe UI Variable", "Segoe UI", "Noto Sans", sans-serif; font-size: 14px; color: {C['text']}; }}
QMainWindow, QWidget#page {{ background: {C['bg']}; }}
QToolTip {{ background: {C['raised']}; color: {C['text']}; border: 1px solid {C['line']}; padding: 8px 10px;
            border-radius: 8px; font-size: 13px; }}

QWidget#side {{ background: {C['side']}; }}
QLabel#brand {{ font-size: 19px; font-weight: 800; }}
QLabel#brandSub {{ color: {C['faint']}; font-size: 12px; }}
QPushButton#nav {{ text-align: left; padding: 11px 14px; border: none; border-radius: 10px; color: {C['muted']};
                   font-size: 14px; font-weight: 600; background: transparent; }}
QPushButton#nav:hover {{ background: {C['surface']}; color: {C['text']}; }}
QPushButton#nav:checked {{ background: {C['raised']}; color: {C['text']}; }}

QLabel#h1 {{ font-size: 26px; font-weight: 800; }}
QLabel#h2 {{ font-size: 17px; font-weight: 700; }}
QLabel#lead {{ color: {C['muted']}; font-size: 14px; }}
QLabel#muted {{ color: {C['muted']}; }}
QLabel#small {{ color: {C['faint']}; font-size: 12px; }}
QLabel#statusTitle {{ font-size: 30px; font-weight: 800; }}

QFrame#card {{ background: {C['surface']}; border: 1px solid {C['line']}; border-radius: 14px; }}
QFrame#hint {{ background: {C['surface']}; border-radius: 12px; border-left: 3px solid {C['violet']}; }}
QFrame#hint[level="warn"] {{ border-left-color: {C['amber']}; }}
QFrame#hint[level="error"] {{ border-left-color: {C['coral']}; }}
QFrame#hint[level="ok"] {{ border-left-color: {C['teal']}; }}
QFrame#banner {{ background: {C['raised']}; border-radius: 12px; border: 1px solid {C['violet']}; }}

QPushButton {{ background: {C['raised']}; border: 1px solid {C['line']}; border-radius: 9px; padding: 8px 16px;
               font-weight: 600; }}
QPushButton:hover {{ border-color: {C['violet']}; }}
QPushButton:pressed {{ background: {C['line']}; }}
QPushButton:disabled {{ color: {C['faint']}; border-color: {C['raised']}; }}
QPushButton#primary {{ background: {C['teal']}; color: #062a23; border: none; }}
QPushButton#primary:hover {{ background: #5fdcc2; }}
QPushButton#primary:disabled {{ background: {C['line']}; color: {C['faint']}; }}
QPushButton#danger {{ color: {C['coral']}; }}
QPushButton#link {{ background: transparent; border: none; color: {C['violet']}; padding: 4px 6px; }}
QPushButton#link:hover {{ color: #b0a5ff; }}
QToolButton#help {{ background: transparent; border: 1px solid {C['line']}; border-radius: 10px; color: {C['muted']};
                    font-weight: 700; font-size: 12px; min-width: 20px; max-width: 20px; min-height: 20px; max-height: 20px; }}
QToolButton#help:hover {{ border-color: {C['violet']}; color: {C['text']}; }}

QComboBox, QLineEdit, QSpinBox, QPlainTextEdit {{ background: {C['bg']}; border: 1px solid {C['line']};
               border-radius: 9px; padding: 7px 10px; selection-background-color: {C['violet']}; }}
QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QPlainTextEdit:focus {{ border-color: {C['violet']}; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox QAbstractItemView {{ background: {C['raised']}; border: 1px solid {C['line']}; padding: 4px;
                               selection-background-color: {C['line']}; }}
QPlainTextEdit {{ font-family: "Cascadia Mono", "JetBrains Mono", "DejaVu Sans Mono", monospace; font-size: 13px; }}

QCheckBox {{ spacing: 10px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px; border: 1px solid {C['faint']};
                        background: {C['bg']}; }}
QCheckBox::indicator:checked {{ background: {C['teal']}; border-color: {C['teal']}; image: url({CHECK}); }}
QCheckBox:disabled {{ color: {C['faint']}; }}
QSpinBox::up-button, QSpinBox::down-button {{ width: 0; border: none; }}

QTreeWidget, QTableWidget {{ background: {C['surface']}; border: 1px solid {C['line']}; border-radius: 12px;
                             alternate-background-color: #1d2640; gridline-color: transparent; outline: none; }}
QTreeWidget::item, QTableWidget::item {{ padding: 6px 4px; }}
QTreeWidget::item:selected, QTableWidget::item:selected {{ background: {C['raised']}; color: {C['text']}; }}
QHeaderView::section {{ background: {C['surface']}; color: {C['faint']}; border: none; padding: 8px 6px;
                        font-weight: 600; font-size: 12px; }}

QTabWidget::pane {{ border: none; }}
QTabBar::tab {{ background: transparent; color: {C['muted']}; padding: 9px 16px; margin-right: 6px;
                border-bottom: 2px solid transparent; font-weight: 700; }}
QTabBar::tab:selected {{ color: {C['text']}; border-bottom-color: {C['teal']}; }}

QProgressBar {{ background: {C['bg']}; border: none; border-radius: 4px; height: 8px; text-align: center;
                color: transparent; }}
QProgressBar::chunk {{ border-radius: 4px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                       stop:0 {C['teal']}, stop:1 {C['violet']}); }}

QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {C['line']}; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QStatusBar {{ background: {C['side']}; color: {C['muted']}; }}
QMenu {{ background: {C['raised']}; border: 1px solid {C['line']}; padding: 6px; border-radius: 10px; }}
QMenu::item {{ padding: 7px 18px; border-radius: 6px; }}
QMenu::item:selected {{ background: {C['line']}; }}
QMessageBox {{ background: {C['bg']}; }}
"""


_translators = []


def install_translations(app):
    """Russian texts for Qt's own buttons (Да/Нет/Отмена). Bundled .qm first:
    distro PySide6 often comes without Qt translations."""
    from PySide6.QtCore import QLibraryInfo, QTranslator
    for d in (ASSETS, QLibraryInfo.path(QLibraryInfo.TranslationsPath)):
        t = QTranslator(app)
        if t.load("qtbase_ru", d):
            app.installTranslator(t)
            _translators.append(t)
            return True
    return False


def apply(app):
    install_translations(app)
    app.setStyle("Fusion")
    load_fonts()
    app.setPalette(palette())
    app.setStyleSheet(stylesheet())
