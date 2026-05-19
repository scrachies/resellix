"""Reusable PyQt6 widgets for the dashboard."""
from __future__ import annotations

import webbrowser
from typing import Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .photo_loader import PhotoLoader


class StatCard(QFrame):
    """Small KPI card: title + big number."""

    def __init__(self, title: str, value: str = "0", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumHeight(96)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setObjectName("CardTitle")
        layout.addWidget(self.title_lbl)

        self.value_lbl = QLabel(value)
        self.value_lbl.setObjectName("CardValue")
        layout.addWidget(self.value_lbl)
        layout.addStretch(1)

    def set_value(self, value: str) -> None:
        self.value_lbl.setText(value)


class DealCard(QFrame):
    """Listing preview card: photo on the left, info on the right."""

    PHOTO_W = 130
    PHOTO_H = 130
    load_photos: bool = True

    def __init__(
        self,
        title: str,
        price_str: str,
        meta: str,
        url: str,
        photo_url: str = "",
        savings_str: str = "",
        load_photo: Optional[bool] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("DealCard")
        self.url = url
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(self.PHOTO_H + 24)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(14)

        # photo
        self.photo = QLabel("loading…")
        self.photo.setObjectName("PhotoLabel")
        self.photo.setFixedSize(self.PHOTO_W, self.PHOTO_H)
        self.photo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.photo)

        # info column
        info = QVBoxLayout()
        info.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("DealTitle")
        title_lbl.setWordWrap(True)
        info.addWidget(title_lbl)

        price_lbl = QLabel(price_str)
        price_lbl.setObjectName("DealPrice")
        info.addWidget(price_lbl)

        meta_lbl = QLabel(meta)
        meta_lbl.setObjectName("DealMeta")
        meta_lbl.setWordWrap(True)
        info.addWidget(meta_lbl)

        if savings_str:
            sv = QLabel(savings_str)
            sv.setObjectName("DealSavings")
            info.addWidget(sv)

        info.addStretch(1)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        open_btn = QPushButton("Open on Vinted")
        open_btn.clicked.connect(self._open)
        copy_btn = QPushButton("Copy link")
        copy_btn.setObjectName("GhostButton")
        copy_btn.clicked.connect(self._copy)
        btns.addWidget(open_btn)
        btns.addWidget(copy_btn)
        btns.addStretch(1)
        info.addLayout(btns)

        root.addLayout(info, 1)

        show_photo = self.load_photos if load_photo is None else load_photo
        self._loader = PhotoLoader(self)
        self._loader.loaded.connect(self._on_photo)
        self._loader.failed.connect(self._on_photo_failed)
        if show_photo and photo_url:
            self._loader.fetch(photo_url)
        else:
            self._on_photo_failed("")
        self.destroyed.connect(self._cancel_photo_load)

    def _cancel_photo_load(self, *_args) -> None:
        self._loader.cancel()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._loader.cancel()
        super().closeEvent(event)

    # ----- slots -----

    def _on_photo_failed(self, _msg: str) -> None:
        self.photo.setText("No photo")
        self.photo.setStyleSheet("color:#86868b; font-size:11px;")

    def _on_photo(self, pm: QPixmap) -> None:
        scaled = pm.scaled(
            QSize(self.PHOTO_W, self.PHOTO_H),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.photo.setPixmap(scaled)

    def _open(self) -> None:
        if self.url:
            webbrowser.open(self.url)

    def _copy(self) -> None:
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.url or "")
