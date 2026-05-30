from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

COLORS = {
    "offline": QColor(95, 100, 110),
    "idle": QColor(0, 178, 255),
    "printing": QColor(0, 255, 140),
    "warn": QColor(255, 191, 64),
    "alert": QColor(255, 69, 86),
}


def make_icon(level: str = "idle") -> QIcon:
    color = COLORS.get(level, COLORS["idle"])
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(color)
    p.setPen(QPen(QColor(10, 16, 20), 3))
    p.drawEllipse(7, 7, 50, 50)
    p.setBrush(QColor(10, 16, 20))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(20, 22, 24, 14, 4, 4)
    p.setBrush(color.lighter(145))
    p.drawEllipse(24, 27, 5, 5)
    p.drawEllipse(35, 27, 5, 5)
    p.end()
    return QIcon(pix)
