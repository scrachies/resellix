"""Reusable glass panels, shadows, and form helpers."""
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
    blur: float = 32,
    offset_y: float = 8,
    alpha: int = 52,
) -> QGraphicsDropShadowEffect:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, offset_y)
    effect.setColor(QColor(15, 23, 42, alpha))
    widget.setGraphicsEffect(effect)
    return effect


class GlassCard(QFrame):
    """Floating glass panel with soft shadow."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("GlassCard")
        drop_shadow(self, blur=36, offset_y=10, alpha=58)


class GlassScroll(QScrollArea):
    """Scroll area styled for content pages."""

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
    lay.setContentsMargins(0, 0, 0, 4)
    lay.setSpacing(4)
    t = QLabel(title)
    t.setObjectName("SectionTitle")
    lay.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setObjectName("PageSubtitle")
        s.setWordWrap(True)
        lay.addWidget(s)
    return w


def filter_bar_card() -> GlassCard:
    return GlassCard()
