"""Glass panels, glow shadows, form helpers."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


def drop_shadow(
    widget: QWidget,
    *,
    blur: float = 40,
    offset_y: float = 12,
    alpha: int = 90,
    color: QColor | None = None,
) -> QGraphicsDropShadowEffect:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, offset_y)
    effect.setColor(color if color is not None else QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(effect)
    return effect


def glow_shadow(
    widget: QWidget,
    *,
    blur: float = 28,
    r: int = 34,
    g: int = 211,
    b: int = 238,
    alpha: int = 120,
) -> QGraphicsDropShadowEffect:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, 0)
    effect.setColor(QColor(r, g, b, alpha))
    widget.setGraphicsEffect(effect)
    return effect


class GlassCard(QFrame):
    """Frosted floating panel."""

    def __init__(self, parent: Optional[QWidget] = None, *, strong_glow: bool = False) -> None:
        super().__init__(parent)
        self.setObjectName("GlassCard")
        if strong_glow:
            glow_shadow(self, blur=32, r=139, g=92, b=246, alpha=80)
        else:
            drop_shadow(self, blur=48, offset_y=14, color=QColor(0, 0, 0, 100))


class GlassScroll(QScrollArea):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("GlassScroll")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


def form_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("FormLabel")
    return lbl


def section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("CardSectionTitle")
    return lbl


def page_header(title: str, subtitle: str = "") -> QWidget:
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 6)
    lay.setSpacing(6)
    t = QLabel(title)
    t.setObjectName("SectionTitle")
    lay.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setObjectName("PageSubtitle")
        s.setWordWrap(True)
        lay.addWidget(s)
    return w
