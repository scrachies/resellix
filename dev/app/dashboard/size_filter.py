"""Multi-select size filter (popup)."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from listing_utils import size_options_from_rows


class SizeFilterBar(QWidget):
    """Select multiple sizes; empty selection shows all."""

    selection_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._selected: set[str] = set()
        self._checkboxes: dict[str, QCheckBox] = {}

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        self.btn = QToolButton()
        self.btn.setObjectName("SizeFilterButton")
        self.btn.setText("All sizes")
        self.btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        lay.addWidget(self.btn)

        self._popup = QFrame()
        self._popup.setObjectName("SizeFilterPopup")
        pop_lay = QVBoxLayout(self._popup)
        pop_lay.setContentsMargins(12, 12, 12, 12)
        pop_lay.setSpacing(8)

        head = QHBoxLayout()
        title = QLabel("Sizes")
        title.setObjectName("PopupTitle")
        head.addWidget(title)
        head.addStretch(1)
        btn_clear = QPushButton("Clear")
        btn_clear.setObjectName("GhostButton")
        btn_clear.setFixedHeight(28)
        btn_clear.clicked.connect(self._clear_all)
        btn_all = QPushButton("All")
        btn_all.setObjectName("GhostButton")
        btn_all.setFixedHeight(28)
        btn_all.clicked.connect(self._select_all)
        head.addWidget(btn_clear)
        head.addWidget(btn_all)
        pop_lay.addLayout(head)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMaximumHeight(220)
        scroll.setMinimumWidth(260)
        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(6)
        scroll.setWidget(self._grid_host)
        pop_lay.addWidget(scroll)

        menu = QMenu(self)
        menu.setObjectName("SizeFilterMenu")
        wa = QWidgetAction(menu)
        wa.setDefaultWidget(self._popup)
        menu.addAction(wa)
        self.btn.setMenu(menu)
        self._update_button_label()

    def selected_keys(self) -> set[str]:
        return set(self._selected)

    def set_rows(self, rows: list[dict]) -> None:
        prev = set(self._selected)
        options = size_options_from_rows(rows)

        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._checkboxes.clear()

        col_count = 3
        for i, (key, label) in enumerate(options):
            cb = QCheckBox(label)
            cb.setChecked(key in prev)
            cb.stateChanged.connect(lambda _s, k=key: self._on_toggle(k))
            self._checkboxes[key] = cb
            self._grid.addWidget(cb, i // col_count, i % col_count)

        if not options:
            empty = QLabel("No sizes in results")
            empty.setObjectName("HintLabel")
            self._grid.addWidget(empty, 0, 0)

        self._sync_selected_from_ui()
        self._update_button_label()

    def _on_toggle(self, _key: str) -> None:
        self._sync_selected_from_ui()
        self._update_button_label()
        self.selection_changed.emit()

    def _sync_selected_from_ui(self) -> None:
        self._selected = {k for k, cb in self._checkboxes.items() if cb.isChecked()}

    def _clear_all(self) -> None:
        for cb in self._checkboxes.values():
            cb.blockSignals(True)
            cb.setChecked(False)
            cb.blockSignals(False)
        self._selected.clear()
        self._update_button_label()
        self.selection_changed.emit()

    def _select_all(self) -> None:
        for cb in self._checkboxes.values():
            cb.blockSignals(True)
            cb.setChecked(True)
            cb.blockSignals(False)
        self._sync_selected_from_ui()
        self._update_button_label()
        self.selection_changed.emit()

    def _update_button_label(self) -> None:
        if not self._selected:
            self.btn.setText("All sizes")
            return
        labels = []
        for key in sorted(self._selected):
            cb = self._checkboxes.get(key)
            labels.append(cb.text() if cb else key)
        if len(labels) <= 3:
            self.btn.setText(", ".join(labels))
        else:
            self.btn.setText(f"{len(labels)} sizes")
