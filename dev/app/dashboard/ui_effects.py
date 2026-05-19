"""Light UI polish: page fades and button press feedback."""
from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QObject, QPropertyAnimation, pyqtProperty
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QPushButton, QStackedWidget, QWidget


class _OpacityDriver(QObject):
    def __init__(self, effect: QGraphicsOpacityEffect) -> None:
        super().__init__()
        self._effect = effect

    def get_opacity(self) -> float:
        return float(self._effect.opacity())

    def set_opacity(self, value: float) -> None:
        self._effect.setOpacity(max(0.0, min(1.0, value)))

    opacity = pyqtProperty(float, get_opacity, set_opacity)


def fade_in_widget(widget: QWidget, *, duration_ms: int = 220) -> QPropertyAnimation:
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(0.0)
    widget.setGraphicsEffect(effect)
    driver = _OpacityDriver(effect)
    anim = QPropertyAnimation(driver, b"opacity", widget)
    anim.setDuration(duration_ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.finished.connect(lambda: widget.setGraphicsEffect(None))
    anim.start()
    widget._fade_anim = anim  # keep reference
    return anim


def switch_stack_page(stack: QStackedWidget, index: int, *, duration_ms: int = 200) -> None:
    if index < 0 or index >= stack.count():
        return
    if stack.currentIndex() == index:
        return
    stack.setCurrentIndex(index)
    fade_in_widget(stack.currentWidget(), duration_ms=duration_ms)


class ButtonPressFilter(QObject):
    """Subtle press feedback on buttons."""

    def eventFilter(self, obj: QObject, event) -> bool:  # type: ignore[override]
        if isinstance(obj, QPushButton):
            from PyQt6.QtCore import QEvent

            if event.type() == QEvent.Type.MouseButtonPress:
                obj.setProperty("_pressed", True)
            elif event.type() == QEvent.Type.MouseButtonRelease:
                obj.setProperty("_pressed", False)
        return super().eventFilter(obj, event)


def install_button_press_effect(root: QWidget) -> ButtonPressFilter:
    filt = ButtonPressFilter(root)
    for btn in root.findChildren(QPushButton):
        btn.installEventFilter(filt)
    return filt
