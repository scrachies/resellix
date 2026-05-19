"""Clickable platform filter for dashboard feeds."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QWidget,
)

from platforms import ALL_PLATFORMS, PLATFORM_LABELS


class PlatformFilterBar(QWidget):
    """Toggle Vinted / Kleinanzeigen / eBay — none selected = show all."""

    selection_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._selected: set[str] = set()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        self._all_btn = QPushButton("All")
        self._all_btn.setObjectName("FilterChip")
        self._all_btn.setCheckable(True)
        self._all_btn.setChecked(True)
        self._all_btn.clicked.connect(self._on_all)
        lay.addWidget(self._all_btn)

        self._buttons: dict[str, QPushButton] = {}
        for key in ALL_PLATFORMS:
            btn = QPushButton(PLATFORM_LABELS.get(key, key))
            btn.setObjectName("FilterChip")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _=False, k=key: self._toggle(k))
            self._buttons[key] = btn
            lay.addWidget(btn)

    def _on_all(self) -> None:
        self._selected.clear()
        self._all_btn.setChecked(True)
        for btn in self._buttons.values():
            btn.setChecked(False)
        self.selection_changed.emit()

    def _toggle(self, key: str) -> None:
        btn = self._buttons[key]
        if btn.isChecked():
            self._selected.add(key)
        else:
            self._selected.discard(key)
        self._all_btn.setChecked(not self._selected)
        self.selection_changed.emit()

    def selected_platforms(self) -> set[str]:
        if not self._selected:
            return set()
        return set(self._selected)
