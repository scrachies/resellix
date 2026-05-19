"""Helpers for window-size–aware dashboard layout."""
from __future__ import annotations

from typing import Sequence

from PyQt6.QtWidgets import QGridLayout, QWidget


def relayout_grid_columns(
    grid: QGridLayout,
    widgets: Sequence[QWidget],
    *,
    columns: int,
    h_spacing: int | None = None,
    v_spacing: int | None = None,
) -> None:
    """Place widgets in a grid with the given column count (clears prior cells)."""
    cols = max(1, columns)
    if h_spacing is not None:
        grid.setHorizontalSpacing(h_spacing)
    if v_spacing is not None:
        grid.setVerticalSpacing(v_spacing)
    for w in widgets:
        grid.removeWidget(w)
    for i, w in enumerate(widgets):
        grid.addWidget(w, i // cols, i % cols)
