"""Resellix — clean Apple-inspired UI."""
from __future__ import annotations

COLOR_BG = "#000000"
COLOR_BG_ELEVATED = "#1c1c1e"
COLOR_GLASS = "rgba(28, 28, 30, 0.78)"
COLOR_GLASS_HI = "rgba(44, 44, 46, 0.92)"
COLOR_BORDER = "rgba(255, 255, 255, 0.08)"
COLOR_BORDER_HI = "rgba(255, 255, 255, 0.14)"

COLOR_TEXT = "#f5f5f7"
COLOR_TEXT_MUTED = "#98989d"
COLOR_ACCENT = "#0a84ff"
COLOR_ACCENT_SOFT = "rgba(10, 132, 255, 0.18)"
COLOR_GREEN = "#30d158"
COLOR_RED = "#ff453a"
COLOR_YELLOW = "#ffd60a"
COLOR_INPUT = "rgba(44, 44, 46, 0.9)"

FONT_UI = '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'


STYLESHEET = f"""
* {{
    font-family: {FONT_UI};
    color: {COLOR_TEXT};
}}

QMainWindow {{
    background-color: {COLOR_BG};
}}

QWidget {{
    background: transparent;
}}

QDialog {{
    background-color: {COLOR_BG_ELEVATED};
}}

/* Sidebar */
QFrame#Sidebar {{
    background-color: {COLOR_GLASS};
    border-right: 1px solid {COLOR_BORDER};
}}
QFrame#BrandBlock {{
    background: transparent;
    border: none;
    margin: 20px 16px 8px 16px;
}}
QLabel#BrandTitle {{
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.4px;
    color: {COLOR_TEXT};
}}
QLabel#BrandTagline {{
    font-size: 12px;
    color: {COLOR_TEXT_MUTED};
    padding-top: 2px;
}}
QPushButton#NavButton {{
    background: transparent;
    border: none;
    text-align: left;
    padding: 10px 14px;
    margin: 1px 12px;
    font-size: 13px;
    font-weight: 500;
    color: {COLOR_TEXT_MUTED};
    border-radius: 10px;
}}
QPushButton#NavButton:hover {{
    background: rgba(255, 255, 255, 0.06);
    color: {COLOR_TEXT};
}}
QPushButton#NavButton:checked {{
    background: {COLOR_ACCENT_SOFT};
    color: {COLOR_ACCENT};
    font-weight: 600;
}}
QFrame#SidebarUpdateBanner {{
    background: rgba(255, 159, 10, 0.12);
    border: 1px solid rgba(255, 159, 10, 0.35);
    border-radius: 10px;
    margin: 0 10px 6px 10px;
}}
QLabel#SidebarUpdateTitle {{
    color: #ffb340;
    font-size: 10px;
    font-weight: 600;
}}
QLabel#SidebarUpdateText {{
    color: {COLOR_TEXT_MUTED};
    font-size: 9px;
}}
QLabel#SidebarAttribution {{
    color: {COLOR_TEXT_MUTED};
    font-size: 9px;
    padding: 0 16px 6px 16px;
}}
QLabel#SidebarVersion {{
    color: {COLOR_TEXT_MUTED};
    font-size: 11px;
    padding: 0 20px 20px 20px;
}}

/* Status */
QFrame#StatusStrip {{
    background-color: {COLOR_GLASS};
    border-bottom: 1px solid {COLOR_BORDER};
}}
QLabel#StatusDot {{ color: {COLOR_GREEN}; font-size: 14px; }}
QLabel#StatusDotPaused {{ color: {COLOR_YELLOW}; font-size: 14px; }}
QLabel#StatusDotError {{ color: {COLOR_RED}; font-size: 14px; }}
QLabel#ToolbarLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 12px;
    font-weight: 500;
}}

/* Cards */
QFrame#Card, QFrame#DealCard {{
    background-color: {COLOR_GLASS_HI};
    border: 1px solid {COLOR_BORDER};
    border-radius: 14px;
}}
QFrame#DealCard:hover {{
    border-color: {COLOR_BORDER_HI};
}}
QLabel#CardTitle {{
    font-size: 11px;
    font-weight: 600;
    color: {COLOR_TEXT_MUTED};
    letter-spacing: 0.3px;
}}
QLabel#CardValue {{
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.5px;
}}
QLabel#SectionTitle {{
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.3px;
    padding: 0 0 4px 0;
}}
QLabel#HintLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 12px;
}}
QLabel#PopupTitle {{
    font-size: 13px;
    font-weight: 600;
}}

/* Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QComboBox {{
    background-color: {COLOR_INPUT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    padding: 8px 12px;
    color: {COLOR_TEXT};
    selection-background-color: {COLOR_ACCENT};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: 1px solid {COLOR_ACCENT};
}}
QComboBox QAbstractItemView {{
    background-color: {COLOR_BG_ELEVATED};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    selection-background-color: {COLOR_ACCENT_SOFT};
}}

QPushButton {{
    background-color: {COLOR_ACCENT};
    color: white;
    border: none;
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: #409cff;
}}
QPushButton:disabled {{
    background-color: rgba(72, 72, 74, 0.8);
    color: {COLOR_TEXT_MUTED};
}}
QPushButton#GhostButton, QToolButton#SizeFilterButton {{
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT};
    font-weight: 500;
}}
QPushButton#GhostButton:hover, QToolButton#SizeFilterButton:hover {{
    background-color: rgba(255, 255, 255, 0.1);
}}
QPushButton#DangerButton {{
    background-color: {COLOR_RED};
}}

QMenu#SizeFilterMenu {{
    background-color: {COLOR_BG_ELEVATED};
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
    padding: 4px;
}}
QFrame#SizeFilterPopup {{
    background-color: {COLOR_BG_ELEVATED};
}}
QCheckBox {{
    spacing: 8px;
    color: {COLOR_TEXT};
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid {COLOR_BORDER_HI};
    background: {COLOR_INPUT};
}}
QCheckBox::indicator:checked {{
    background: {COLOR_ACCENT};
    border-color: {COLOR_ACCENT};
}}

/* Table */
QTableWidget {{
    background-color: {COLOR_GLASS};
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
    gridline-color: transparent;
}}
QHeaderView::section {{
    background: transparent;
    padding: 10px 12px;
    border: none;
    border-bottom: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT_MUTED};
    font-size: 12px;
    font-weight: 600;
}}
QTableWidget::item {{
    padding: 10px 12px;
}}
QTableWidget::item:selected {{
    background-color: {COLOR_ACCENT_SOFT};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
}}
QScrollBar::handle:vertical {{
    background: rgba(255, 255, 255, 0.18);
    border-radius: 4px;
    min-height: 40px;
}}

QLabel#DealTitle {{ font-size: 14px; font-weight: 600; }}
QLabel#DealPrice {{ font-size: 18px; font-weight: 700; color: {COLOR_GREEN}; }}
QLabel#DealMeta {{ font-size: 12px; color: {COLOR_TEXT_MUTED}; }}
QLabel#DealSavings {{ font-size: 12px; color: {COLOR_YELLOW}; font-weight: 600; }}
QLabel#PhotoLabel {{
    background-color: rgba(0, 0, 0, 0.25);
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
    color: {COLOR_TEXT_MUTED};
}}

QPlainTextEdit#LogView {{
    background-color: #0d0d0f;
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
    font-family: "Cascadia Code", Consolas, monospace;
    font-size: 12px;
    padding: 12px;
}}
"""
