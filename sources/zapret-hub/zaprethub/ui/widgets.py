"""Reusable pieces: the power ring, cards, hint rows, help buttons."""

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QConicalGradient, QCursor, QPainter, QPen
from PySide6.QtWidgets import (QAbstractButton, QFrame, QHBoxLayout, QLabel, QPushButton, QToolButton, QToolTip,
                               QVBoxLayout, QWidget)

from . import icons
from .theme import C


class PowerRing(QAbstractButton):
    """The big switch. state: absent | off | on | busy."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(216, 216)
        self.state = "off"
        self.fill = 0.0      # 0 = off, 1 = full arc
        self.spin = 0.0
        self._fill_anim = QVariantAnimation(self, duration=650)
        self._fill_anim.valueChanged.connect(self._set_fill)
        self._spin_anim = QVariantAnimation(self, startValue=0.0, endValue=360.0, duration=1100, loopCount=-1)
        self._spin_anim.valueChanged.connect(self._set_spin)
        self.setFocusPolicy(Qt.StrongFocus)

    def sizeHint(self):
        return QSize(216, 216)

    def _set_fill(self, v):
        self.fill = v
        self.update()

    def _set_spin(self, v):
        self.spin = v
        self.update()

    def set_state(self, state):
        if state == self.state:
            return
        self.state = state
        if state == "busy":
            self._spin_anim.start()
        else:
            self._spin_anim.stop()
            target = 1.0 if state == "on" else 0.0
            self._fill_anim.stop()
            self._fill_anim.setStartValue(self.fill)
            self._fill_anim.setEndValue(target)
            self._fill_anim.start()
        self.setEnabled(state != "busy")
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(14, 14, -14, -14)
        c = r.center()
        # face
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(C["surface"]))
        p.drawEllipse(r.adjusted(10, 10, -10, -10))
        # track
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(C["raised"]), 12, Qt.SolidLine, Qt.RoundCap))
        p.drawEllipse(r)
        grad = QConicalGradient(c, 90 - self.spin)
        grad.setColorAt(0.0, QColor(C["teal"]))
        grad.setColorAt(0.5, QColor(C["violet"]))
        grad.setColorAt(1.0, QColor(C["teal"]))
        pen = QPen(grad, 12, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        if self.state == "busy":
            p.drawArc(r, int((90 - self.spin) * 16), int(-100 * 16))
        elif self.fill > 0.001:
            p.drawArc(r, 90 * 16, int(-360 * 16 * self.fill))
        # focus
        if self.hasFocus():
            p.setPen(QPen(QColor(C["violet"]), 1.5, Qt.DotLine))
            p.drawEllipse(r.adjusted(-10, -10, 10, 10))
        # icon
        on = self.state == "on"
        color = C["teal"] if on else (C["faint"] if self.state == "busy" else C["muted"])
        pm = icons.pixmap("power", color, 64, 2.2)
        p.drawPixmap(QPointF(c.x() - 32, c.y() - 32), pm)
        p.end()


class Card(QFrame):
    def __init__(self, parent=None, spacing=12, margins=(20, 18, 20, 18)):
        super().__init__(parent)
        self.setObjectName("card")
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(*margins)
        self.lay.setSpacing(spacing)


def label(text, name=None, wrap=True, selectable=False):
    lb = QLabel(text)
    if name:
        lb.setObjectName(name)
    lb.setWordWrap(wrap)
    if selectable:
        lb.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return lb


class HelpButton(QToolButton):
    """'?' that explains a setting in plain words; click or hover."""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setObjectName("help")
        self.setText("?")
        self.setToolTip(text)
        self.setCursor(Qt.WhatsThisCursor)
        self.clicked.connect(lambda: QToolTip.showText(QCursor.pos(), text, self))


def row(*widgets, stretch_at=None, spacing=10):
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(spacing)
    for i, x in enumerate(widgets):
        if x is None:
            h.addStretch(1)
        elif isinstance(x, int):
            h.addSpacing(x)
        else:
            h.addWidget(x)
    return w


LEVEL_ICON = {"ok": "check", "warn": "warn", "error": "error", "tip": "bolt"}


class HintRow(QFrame):
    """A recommendation: what we noticed + one action."""
    acted = Signal()

    def __init__(self, level, title, text="", action=None, callback=None, parent=None):
        super().__init__(parent)
        self.setObjectName("hint")
        self.setProperty("level", level)
        h = QHBoxLayout(self)
        h.setContentsMargins(16, 12, 14, 12)
        h.setSpacing(14)
        ic = QLabel()
        color = {"ok": C["teal"], "warn": C["amber"], "error": C["coral"]}.get(level, C["violet"])
        ic.setPixmap(icons.pixmap(LEVEL_ICON.get(level, "bolt"), color, 22))
        ic.setAlignment(Qt.AlignTop)
        h.addWidget(ic)
        v = QVBoxLayout()
        v.setSpacing(3)
        t = label(title)
        t.setStyleSheet("font-weight: 700;")
        v.addWidget(t)
        if text:
            v.addWidget(label(text, "muted"))
        h.addLayout(v, 1)
        if action and callback:
            b = QPushButton(action)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(callback)
            h.addWidget(b, 0, Qt.AlignVCenter)
            self.button = b


def scrolled(widget):
    """Wrap a page body so it scrolls instead of squeezing on small screens."""
    from PySide6.QtWidgets import QScrollArea
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.NoFrame)
    widget.setObjectName("page")
    area.setWidget(widget)
    return area


def clear(layout):
    while layout.count():
        it = layout.takeAt(0)
        if it.widget():
            it.widget().deleteLater()
        elif it.layout():
            clear(it.layout())
