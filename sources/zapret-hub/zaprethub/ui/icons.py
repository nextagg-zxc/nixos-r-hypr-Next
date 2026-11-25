"""Small stroke icons drawn from inline SVG paths (24x24 grid), tinted per use."""

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

PATHS = {
    "power": '<path d="M12 3v8"/><path d="M6.4 6.8a8 8 0 1 0 11.2 0"/>',
    "sliders": '<path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/>',
    "send": '<path d="M21 3 3 10.5l7 2.5 2.5 7z"/><path d="m21 3-11 10"/>',
    "list": '<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/>'
            '<circle cx="4.5" cy="18" r="1"/>',
    "refresh": '<path d="M20 11a8 8 0 0 0-14.6-4.5L4 8"/><path d="M4 3v5h5"/><path d="M4 13a8 8 0 0 0 14.6 4.5L20 16"/>'
               '<path d="M20 21v-5h-5"/>',
    "pulse": '<path d="M3 12h4l3-7 4 14 3-7h4"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    "warn": '<path d="M12 3 2.5 20h19z"/><path d="M12 10v4M12 17.5v.01"/>',
    "error": '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6M15 9l-6 6"/>',
    "star": '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    "copy": '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "bolt": '<path d="M13 3 5 14h6l-1 7 8-11h-6z"/>',
    "shield": '<path d="M12 3 19 6v6c0 4.4-3 8-7 9-4-1-7-4.6-7-9V6z"/>',
}


def svg(name, color, width=2.0):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">{PATHS[name]}</svg>')


def pixmap(name, color, size=20, width=2.0, ratio=2.0):
    pm = QPixmap(int(size * ratio), int(size * ratio))
    pm.fill(Qt.transparent)
    r = QSvgRenderer(QByteArray(svg(name, color, width).encode()))
    p = QPainter(pm)
    r.render(p, QRectF(0, 0, pm.width(), pm.height()))
    p.end()
    pm.setDevicePixelRatio(ratio)
    return pm


def icon(name, color, size=20):
    return QIcon(pixmap(name, color, size))
