"""Reusable PyQt6 widgets for the dashboard."""
from __future__ import annotations

import webbrowser
from typing import Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QCloseEvent, QFont
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
    """KPI card with roomy typography."""

    def __init__(self, title: str, value: str = "0", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setMinimumWidth(200)
        self.setMinimumHeight(112)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(8)

        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setObjectName("CardTitle")
        layout.addWidget(self.title_lbl)

        self.value_lbl = QLabel(value)
        self.value_lbl.setObjectName("CardValue")
        self.value_lbl.setWordWrap(False)
        self.value_lbl.setMinimumHeight(40)
        font = QFont()
        font.setPointSize(26)
        font.setWeight(QFont.Weight.Bold)
        self.value_lbl.setFont(font)
        layout.addWidget(self.value_lbl)
        layout.addStretch(1)

    def set_value(self, value: str) -> None:
        self.value_lbl.setText(value)


class DealCard(QFrame):
    """Listing preview card: photo on the left, info on the right."""

    PHOTO_W = 136
    PHOTO_H = 136
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
        self.setMinimumHeight(self.PHOTO_H + 32)

        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        self.photo = QLabel("Loading")
        self.photo.setObjectName("PhotoLabel")
        self.photo.setFixedSize(self.PHOTO_W, self.PHOTO_H)
        self.photo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.photo)

        info = QVBoxLayout()
        info.setSpacing(6)

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
        btns.setSpacing(10)
        open_btn = QPushButton("Open listing")
        open_btn.setObjectName("PrimaryButton")
        open_btn.clicked.connect(self._open)
        copy_btn = QPushButton("Copy link")
        copy_btn.setObjectName("GhostButton")
        copy_btn.clicked.connect(self._copy)
        btns.addWidget(open_btn)
        btns.addWidget(copy_btn)
        btns.addStretch(1)
        info.addLayout(btns)

        root.addLayout(info, 1)

        self._loader: Optional[PhotoLoader] = None
        do_load = self.load_photos if load_photo is None else load_photo
        if do_load and photo_url:
            self._loader = PhotoLoader(self)
            self._loader.loaded.connect(self._on_photo_loaded)
            self._loader.failed.connect(lambda _m: self.photo.setText("No image"))
            self._loader.fetch(photo_url)
        elif not photo_url:
            self.photo.setText("No image")

    def _on_photo_loaded(self, pix: QPixmap) -> None:
        if pix and not pix.isNull():
            scaled = pix.scaled(
                self.PHOTO_W,
                self.PHOTO_H,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.photo.setPixmap(scaled)
            self.photo.setText("")
        else:
            self.photo.setText("No image")

    def _open(self) -> None:
        if self.url:
            webbrowser.open(self.url)

    def _copy(self) -> None:
        from PyQt6.QtWidgets import QApplication

        if self.url:
            QApplication.clipboard().setText(self.url)

    def closeEvent(self, event: QCloseEvent) -> None:
        super().closeEvent(event)
