"""Resellix — light glass UI theme."""
from __future__ import annotations

# Light glass palette
COLOR_BG = "#e8edf5"
COLOR_BG_ALT = "#dfe6f2"
COLOR_GLASS = "rgba(255, 255, 255, 0.78)"
COLOR_GLASS_HI = "rgba(255, 255, 255, 0.92)"
COLOR_GLASS_SIDEBAR = "rgba(255, 255, 255, 0.65)"
COLOR_BORDER = "rgba(15, 23, 42, 0.08)"
COLOR_BORDER_HI = "rgba(15, 23, 42, 0.14)"
COLOR_SHADOW = "rgba(79, 110, 247, 0.12)"

COLOR_TEXT = "#0f172a"
COLOR_TEXT_MUTED = "#64748b"
COLOR_ACCENT = "#4f6ef7"
COLOR_ACCENT_HOVER = "#6b84ff"
COLOR_ACCENT_SOFT = "rgba(79, 110, 247, 0.14)"
COLOR_GREEN = "#10b981"
COLOR_RED = "#ef4444"
COLOR_YELLOW = "#f59e0b"
COLOR_INPUT = "rgba(255, 255, 255, 0.95)"

FONT_UI = '"Segoe UI", "Inter", -apple-system, BlinkMacSystemFont, sans-serif'
FONT_MONO = '"Cascadia Code", "Consolas", monospace'

CONTENT_MARGIN = "32px"
CARD_RADIUS = "16px"
BTN_RADIUS = "12px"

STYLESHEET = f"""
* {{
    font-family: {FONT_UI};
    color: {COLOR_TEXT};
    font-size: 13px;
}}

QMainWindow {{
    background-color: {COLOR_BG};
}}

QWidget {{
    background: transparent;
}}

QWidget#ContentPage {{
    background-color: transparent;
}}

QDialog {{
    background-color: {COLOR_GLASS_HI};
}}

/* —— Sidebar —— */
QFrame#Sidebar {{
    background-color: {COLOR_GLASS_SIDEBAR};
    border-right: 1px solid {COLOR_BORDER};
}}
QFrame#BrandBlock {{
    background: transparent;
    border: none;
}}
QLabel#BrandTitle {{
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.6px;
    color: {COLOR_TEXT};
}}
QLabel#BrandTagline {{
    font-size: 12px;
    color: {COLOR_TEXT_MUTED};
    padding-top: 2px;
}}
QLabel#SidebarTier {{
    color: {COLOR_ACCENT};
    font-size: 11px;
    font-weight: 600;
    padding-top: 6px;
}}
QPushButton#NavButton {{
    background: transparent;
    border: none;
    text-align: left;
    padding: 12px 16px;
    margin: 2px 14px;
    font-size: 13px;
    font-weight: 500;
    color: {COLOR_TEXT_MUTED};
    border-radius: {BTN_RADIUS};
}}
QPushButton#NavButton:hover {{
    background: rgba(79, 110, 247, 0.08);
    color: {COLOR_TEXT};
}}
QPushButton#NavButton:checked {{
    background: {COLOR_ACCENT_SOFT};
    color: {COLOR_ACCENT};
    font-weight: 600;
    border: 1px solid rgba(79, 110, 247, 0.22);
}}
QPushButton#NavButton:pressed {{
    background: rgba(79, 110, 247, 0.2);
}}

QFrame#SidebarUpdateBanner {{
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-radius: {BTN_RADIUS};
    margin: 0 12px 8px 12px;
}}
QLabel#SidebarUpdateTitle {{
    color: #b45309;
    font-size: 11px;
    font-weight: 600;
}}
QLabel#SidebarUpdateText {{
    color: {COLOR_TEXT_MUTED};
    font-size: 10px;
    line-height: 1.35;
}}
QLabel#SidebarAttribution {{
    color: {COLOR_TEXT_MUTED};
    font-size: 9px;
    padding: 0 18px 6px 18px;
    line-height: 1.35;
}}
QLabel#SidebarVersion {{
    color: {COLOR_TEXT_MUTED};
    font-size: 11px;
    padding: 0 18px 22px 18px;
}}

/* —— Status strip —— */
QFrame#StatusStrip {{
    background-color: {COLOR_GLASS};
    border-bottom: 1px solid {COLOR_BORDER};
    min-height: 60px;
}}
QLabel#StatusDot, QLabel#StatusDotPaused, QLabel#StatusDotError {{
    min-width: 10px;
    max-width: 10px;
    min-height: 10px;
    max-height: 10px;
    border-radius: 5px;
    margin-right: 4px;
}}
QLabel#StatusDot {{ background-color: {COLOR_GREEN}; }}
QLabel#StatusDotPaused {{ background-color: {COLOR_YELLOW}; }}
QLabel#StatusDotError {{ background-color: #94a3b8; }}
QLabel#ToolbarLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 12px;
    font-weight: 500;
    padding: 0 6px;
    min-width: 88px;
}}

/* —— Cards & typography —— */
QFrame#Card, QFrame#DealCard, QFrame#StatCard {{
    background-color: {COLOR_GLASS_HI};
    border: 1px solid {COLOR_BORDER};
    border-radius: {CARD_RADIUS};
}}
QFrame#DealCard:hover {{
    border-color: {COLOR_BORDER_HI};
    background-color: rgba(255, 255, 255, 0.98);
}}
QLabel#CardTitle {{
    font-size: 11px;
    font-weight: 600;
    color: {COLOR_TEXT_MUTED};
    letter-spacing: 0.4px;
}}
QLabel#CardValue {{
    font-size: 32px;
    font-weight: 700;
    letter-spacing: -0.8px;
    color: {COLOR_TEXT};
    min-height: 38px;
}}
QLabel#SectionTitle {{
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.4px;
    padding: 0 0 8px 0;
    color: {COLOR_TEXT};
}}
QLabel#PageSubtitle {{
    font-size: 13px;
    color: {COLOR_TEXT_MUTED};
    padding-bottom: 12px;
}}
QLabel#HintLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 12px;
    line-height: 1.4;
}}
QLabel#ProgressLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 13px;
    font-weight: 500;
    padding: 8px 0;
}}

/* —— Inputs —— */
QLineEdit, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QComboBox {{
    background-color: {COLOR_INPUT};
    border: 1px solid {COLOR_BORDER};
    border-radius: {BTN_RADIUS};
    padding: 10px 14px;
    min-height: 20px;
    color: {COLOR_TEXT};
    selection-background-color: {COLOR_ACCENT_SOFT};
    selection-color: {COLOR_TEXT};
}}
QSpinBox, QDoubleSpinBox {{
    min-width: 108px;
    padding-right: 8px;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: 1px solid {COLOR_ACCENT};
    background-color: #ffffff;
}}
QComboBox::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox QAbstractItemView {{
    background-color: #ffffff;
    border: 1px solid {COLOR_BORDER};
    border-radius: {BTN_RADIUS};
    padding: 4px;
    selection-background-color: {COLOR_ACCENT_SOFT};
}}

/* —— Buttons —— */
QPushButton {{
    background-color: {COLOR_ACCENT};
    color: #ffffff;
    border: none;
    border-radius: {BTN_RADIUS};
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 600;
    min-height: 20px;
}}
QPushButton:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}
QPushButton:pressed {{
    background-color: #3d5ce6;
    padding-top: 11px;
    padding-bottom: 9px;
}}
QPushButton:disabled {{
    background-color: #cbd5e1;
    color: #94a3b8;
}}
QPushButton#PrimaryButton {{
    background-color: {COLOR_ACCENT};
    padding: 11px 22px;
}}
QPushButton#GhostButton, QToolButton#SizeFilterButton {{
    background-color: rgba(255, 255, 255, 0.55);
    border: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT};
    font-weight: 500;
}}
QPushButton#GhostButton:hover, QToolButton#SizeFilterButton:hover {{
    background-color: #ffffff;
    border-color: {COLOR_BORDER_HI};
}}
QPushButton#GhostButton:pressed {{
    background-color: {COLOR_ACCENT_SOFT};
}}
QPushButton#DangerButton {{
    background-color: {COLOR_RED};
}}
QPushButton#DangerButton:hover {{
    background-color: #f87171;
}}

QMenu#SizeFilterMenu {{
    background-color: #ffffff;
    border: 1px solid {COLOR_BORDER};
    border-radius: {CARD_RADIUS};
    padding: 6px;
}}
QFrame#SizeFilterPopup {{
    background-color: #ffffff;
}}
QCheckBox {{
    spacing: 10px;
    color: {COLOR_TEXT};
    font-size: 13px;
    padding: 4px 2px;
}}
QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 6px;
    border: 1px solid {COLOR_BORDER_HI};
    background: {COLOR_INPUT};
}}
QCheckBox::indicator:checked {{
    background: {COLOR_ACCENT};
    border-color: {COLOR_ACCENT};
}}

/* —— Tables —— */
QTableWidget {{
    background-color: {COLOR_GLASS_HI};
    border: 1px solid {COLOR_BORDER};
    border-radius: {CARD_RADIUS};
    gridline-color: {COLOR_BORDER};
    alternate-background-color: rgba(248, 250, 252, 0.9);
}}
QHeaderView::section {{
    background: rgba(248, 250, 252, 0.95);
    padding: 12px 14px;
    border: none;
    border-bottom: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT_MUTED};
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}}
QTableWidget::item {{
    padding: 12px 14px;
    border-bottom: 1px solid {COLOR_BORDER};
}}
QTableWidget::item:selected {{
    background-color: {COLOR_ACCENT_SOFT};
    color: {COLOR_TEXT};
}}

QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: rgba(15, 23, 42, 0.18);
    border-radius: 5px;
    min-height: 48px;
}}
QScrollBar::handle:vertical:hover {{
    background: rgba(15, 23, 42, 0.28);
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* —— Deal cards —— */
QLabel#DealTitle {{ font-size: 15px; font-weight: 600; line-height: 1.3; }}
QLabel#DealPrice {{ font-size: 20px; font-weight: 700; color: {COLOR_GREEN}; }}
QLabel#DealMeta {{ font-size: 12px; color: {COLOR_TEXT_MUTED}; line-height: 1.35; }}
QLabel#DealSavings {{ font-size: 12px; color: #b45309; font-weight: 600; }}
QLabel#PhotoLabel {{
    background-color: {COLOR_BG_ALT};
    border: 1px solid {COLOR_BORDER};
    border-radius: {BTN_RADIUS};
    color: {COLOR_TEXT_MUTED};
    font-size: 11px;
}}

QPlainTextEdit#LogView {{
    background-color: #f8fafc;
    border: 1px solid {COLOR_BORDER};
    border-radius: {CARD_RADIUS};
    font-family: {FONT_MONO};
    font-size: 12px;
    padding: 14px;
    line-height: 1.45;
}}

QMessageBox {{
    background-color: {COLOR_GLASS_HI};
}}
"""
