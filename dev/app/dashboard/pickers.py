"""Clickable size and category pickers for snipe targets."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from categories import SNIPE_CATEGORIES
from platforms import ALL_PLATFORMS, PLATFORM_LABELS

# (facet_key, label) — same keys as listing_utils size matching
STANDARD_SIZES: list[tuple[str, str]] = [
    ("letter:xxs", "XXS"),
    ("letter:xs", "XS"),
    ("letter:s", "S"),
    ("letter:m", "M"),
    ("letter:l", "L"),
    ("letter:xl", "XL"),
    ("letter:xxl", "XXL"),
    ("letter:2xl", "2XL"),
    ("letter:3xl", "3XL"),
    ("num:28", "28"),
    ("num:30", "30"),
    ("num:32", "32"),
    ("num:34", "34"),
    ("num:36", "36"),
    ("num:38", "38"),
    ("num:40", "40"),
    ("num:42", "42"),
    ("num:44", "44"),
    ("num:46", "46"),
    ("waist:28", "W28"),
    ("waist:30", "W30"),
    ("waist:32", "W32"),
    ("waist:34", "W34"),
    ("waist:36", "W36"),
]


class _ChipGrid(QWidget):
    """Grid of checkboxes with clear / select helpers."""

    selection_changed = pyqtSignal()

    def __init__(
        self,
        options: list[tuple[str, str]],
        all_label: str = "Any",
        columns: int = 6,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._options = options
        self._columns = columns
        self._boxes: dict[str, QCheckBox] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        head = QHBoxLayout()
        self._summary = QLabel(all_label)
        self._summary.setObjectName("HintLabel")
        head.addWidget(self._summary)
        head.addStretch(1)
        btn_clear = QPushButton("Clear")
        btn_clear.setObjectName("GhostButton")
        btn_clear.setFixedHeight(26)
        btn_clear.clicked.connect(self._clear)
        head.addWidget(btn_clear)
        root.addLayout(head)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMaximumHeight(88)
        host = QWidget()
        grid = QGridLayout(host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)
        for i, (key, label) in enumerate(options):
            cb = QCheckBox(label)
            cb.stateChanged.connect(self._changed)
            self._boxes[key] = cb
            grid.addWidget(cb, i // columns, i % columns)
        scroll.setWidget(host)
        root.addWidget(scroll)

    def _changed(self) -> None:
        self._update_summary()
        self.selection_changed.emit()

    def _clear(self) -> None:
        for cb in self._boxes.values():
            cb.blockSignals(True)
            cb.setChecked(False)
            cb.blockSignals(False)
        self._update_summary()
        self.selection_changed.emit()

    def _update_summary(self) -> None:
        n = len(self.selected_keys())
        if n == 0:
            self._summary.setText("Any (no filter)")
        elif n <= 4:
            labels = [self._boxes[k].text() for k in self.selected_keys()]
            self._summary.setText(", ".join(labels))
        else:
            self._summary.setText(f"{n} selected")

    def selected_keys(self) -> set[str]:
        return {k for k, cb in self._boxes.items() if cb.isChecked()}

    def set_selected_keys(self, keys: set[str]) -> None:
        for k, cb in self._boxes.items():
            cb.blockSignals(True)
            cb.setChecked(k in keys)
            cb.blockSignals(False)
        self._update_summary()


class SizePickerWidget(_ChipGrid):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(STANDARD_SIZES, all_label="Pick sizes below", columns=7, parent=parent)

    def selected_size_labels(self) -> list[str]:
        return [self._boxes[k].text() for k in self.selected_keys()]


class SizeFilterWidget(QWidget):
    """All sizes, only selected, or exclude selected."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        row = QHBoxLayout()
        self._mode = QComboBox()
        self._mode.addItems(
            ["All sizes (no filter)", "Only these sizes", "Exclude these sizes"]
        )
        self._mode.setMinimumWidth(200)
        self._mode.currentIndexChanged.connect(self._on_mode_changed)
        row.addWidget(self._mode)
        row.addStretch(1)
        root.addLayout(row)

        self._picker = SizePickerWidget()
        self._picker.setEnabled(False)
        root.addWidget(self._picker)

    def _on_mode_changed(self) -> None:
        all_sizes = self._mode.currentIndex() == 0
        self._picker.setEnabled(not all_sizes)
        if all_sizes:
            self._picker._clear()

    def size_mode(self) -> str:
        idx = self._mode.currentIndex()
        if idx == 1:
            return "include"
        if idx == 2:
            return "exclude"
        return "any"

    def selected_keys(self) -> set[str]:
        if self.size_mode() == "any":
            return set()
        return self._picker.selected_keys()

    def reset(self) -> None:
        self._mode.setCurrentIndex(0)
        self._picker._clear()
        self._picker.setEnabled(False)


class PlatformPickerWidget(QWidget):
    """Per-target or global sniper platforms (Vinted / Kleinanzeigen / eBay)."""

    selection_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._boxes: dict[str, QCheckBox] = {}
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        self._summary = QLabel("All platforms")
        self._summary.setObjectName("HintLabel")
        root.addWidget(self._summary)
        for p in ALL_PLATFORMS:
            cb = QCheckBox(PLATFORM_LABELS[p])
            cb.setChecked(True)
            cb.stateChanged.connect(self._changed)
            self._boxes[p] = cb
            root.addWidget(cb)
        root.addStretch(1)

    def _changed(self) -> None:
        keys = [p for p, cb in self._boxes.items() if cb.isChecked()]
        if not keys:
            self._summary.setText("None selected")
        elif len(keys) == len(ALL_PLATFORMS):
            self._summary.setText("All platforms")
        else:
            self._summary.setText(", ".join(PLATFORM_LABELS[k] for k in keys))
        self.selection_changed.emit()

    def selected_platforms(self) -> list[str]:
        keys = [p for p, cb in self._boxes.items() if cb.isChecked()]
        return sorted(keys) if keys else list(ALL_PLATFORMS)

    def set_platforms(self, platforms: list[str]) -> None:
        want = set(platforms) if platforms else set(ALL_PLATFORMS)
        for p, cb in self._boxes.items():
            cb.blockSignals(True)
            cb.setChecked(p in want)
            cb.blockSignals(False)
        self._changed()

    def reset_all(self) -> None:
        self.set_platforms(list(ALL_PLATFORMS))


class CategoryPickerWidget(_ChipGrid):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(SNIPE_CATEGORIES, all_label="Everything", columns=4, parent=parent)
        if "all" in self._boxes:
            self._boxes["all"].setChecked(True)

    def _changed(self) -> None:
        sender = self.sender()
        all_cb = self._boxes.get("all")
        if sender is all_cb and all_cb and all_cb.isChecked():
            for k, cb in self._boxes.items():
                if k != "all":
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
        elif sender and sender is not all_cb and sender.isChecked() and all_cb:
            all_cb.blockSignals(True)
            all_cb.setChecked(False)
            all_cb.blockSignals(False)
        self._update_summary()
        self.selection_changed.emit()

    def _update_summary(self) -> None:
        all_cb = self._boxes.get("all")
        if all_cb and all_cb.isChecked() and len(self.selected_keys()) <= 1:
            self._summary.setText("Everything")
            return
        super()._update_summary()

    def reset_to_all(self) -> None:
        self._clear()
        if "all" in self._boxes:
            self._boxes["all"].setChecked(True)

    def selected_categories(self) -> list[str]:
        keys = self.selected_keys()
        if not keys or "all" in keys:
            return ["all"]
        return sorted(keys)
