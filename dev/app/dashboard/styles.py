"""Resellix — glossy sidebar + clean neutral workspace."""
from __future__ import annotations

# —— One accent family (indigo) ——
ACCENT = "#6366f1"
ACCENT_HOVER = "#818cf8"
ACCENT_GLOW = "rgba(99, 102, 241, 0.35)"

# —— Workspace (neutral, no rainbow) ——
COLOR_BG = "#eef1f6"
COLOR_SURFACE = "#ffffff"
COLOR_BORDER = "rgba(20, 28, 45, 0.08)"
COLOR_BORDER_HI = "rgba(20, 28, 45, 0.12)"

COLOR_TEXT = "#141c2b"
COLOR_TEXT_MUTED = "#6b778c"
COLOR_SUCCESS = "#059669"

FONT_UI = '"Segoe UI", "Inter", -apple-system, BlinkMacSystemFont, sans-serif'
FONT_MONO = '"Cascadia Code", "Consolas", monospace'

CARD_RADIUS = "14px"
BTN_RADIUS = "10px"
NAV_RADIUS = "11px"

# Glossy sidebar: single hue, top highlight → deep base
SIDEBAR_GRADIENT = """
    qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #3d4f72,
        stop:0.35 #2f3d5c,
        stop:1 #1a2438
    )
"""
SIDEBAR_SHINE = """
    qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 0.16),
        stop:0.08 rgba(255, 255, 255, 0.06),
        stop:1 rgba(255, 255, 255, 0)
    )
"""
NAV_ACTIVE_GRADIENT = """
    qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(255, 255, 255, 0.22),
        stop:1 rgba(255, 255, 255, 0.08)
    )
"""
NAV_HOVER_GRADIENT = """
    qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 0.1),
        stop:1 rgba(255, 255, 255, 0.03)
    )
"""

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
    background-color: {COLOR_BG};
}}

QDialog {{
    background-color: {COLOR_SURFACE};
}}

/* ═══════════════ SIDEBAR (glossy, 1 palette) ═══════════════ */
QFrame#Sidebar {{
    background: {SIDEBAR_GRADIENT};
    border: none;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}}

QFrame#BrandBlock {{
    background: {SIDEBAR_SHINE};
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}}

QFrame#SidebarNav {{
    background: transparent;
    border: none;
}}

QFrame#SidebarFooter {{
    background: transparent;
    border: none;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
}}

QFrame#Sidebar QLabel {{
    background: transparent;
    color: rgba(255, 255, 255, 0.72);
}}

QLabel#BrandTitle {{
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: #ffffff;
}}

QLabel#BrandTagline {{
    font-size: 12px;
    color: rgba(255, 255, 255, 0.55);
    padding-top: 2px;
}}

QLabel#SidebarTier {{
    font-size: 11px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.88);
    padding-top: 8px;
}}

QPushButton#NavButton {{
    background: transparent;
    border: 1px solid transparent;
    text-align: left;
    padding: 11px 14px;
    margin: 2px 0;
    font-size: 13px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.62);
    border-radius: {NAV_RADIUS};
}}

QPushButton#NavButton:hover {{
    background: {NAV_HOVER_GRADIENT};
    color: rgba(255, 255, 255, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.12);
}}

QPushButton#NavButton:checked {{
    background: {NAV_ACTIVE_GRADIENT};
    color: #ffffff;
    font-weight: 600;
    border: 1px solid rgba(255, 255, 255, 0.28);
}}

QPushButton#NavButton:pressed {{
    background: rgba(0, 0, 0, 0.15);
    padding-top: 12px;
    padding-bottom: 10px;
}}

QFrame#SidebarUpdateBanner {{
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: {NAV_RADIUS};
    margin: 8px 0;
}}
QLabel#SidebarUpdateTitle {{
    color: rgba(255, 255, 255, 0.92);
    font-size: 11px;
    font-weight: 600;
}}
QLabel#SidebarUpdateText {{
    color: rgba(255, 255, 255, 0.55);
    font-size: 10px;
}}

QLabel#SidebarAttribution {{
    color: rgba(255, 255, 255, 0.38);
    font-size: 9px;
    line-height: 1.4;
}}

QLabel#SidebarVersion {{
    color: rgba(255, 255, 255, 0.32);
    font-size: 10px;
}}

/* ═══════════════ TOP BAR + CONTENT ═══════════════ */
QFrame#StatusStrip {{
    background-color: {COLOR_SURFACE};
    border-bottom: 1px solid {COLOR_BORDER};
    min-height: 58px;
}}

QLabel#StatusDot {{
    background-color: {COLOR_SUCCESS};
    border: 1px solid rgba(255, 255, 255, 0.5);
}}
QLabel#StatusDotPaused {{
    background-color: #d97706;
    border: 1px solid rgba(255, 255, 255, 0.4);
}}
QLabel#StatusDotError {{
    background-color: #94a3b8;
}}

QLabel#StatusDot, QLabel#StatusDotPaused, QLabel#StatusDotError {{
    min-width: 9px;
    max-width: 9px;
    min-height: 9px;
    max-height: 9px;
    border-radius: 5px;
}}

QLabel#ToolbarLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 12px;
    font-weight: 500;
    padding: 0 8px;
    min-width: 84px;
}}

QFrame#Card, QFrame#DealCard, QFrame#StatCard {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {CARD_RADIUS};
}}

QFrame#DealCard:hover {{
    border-color: {COLOR_BORDER_HI};
}}

QLabel#CardTitle {{
    font-size: 11px;
    font-weight: 600;
    color: {COLOR_TEXT_MUTED};
    letter-spacing: 0.5px;
}}

QLabel#CardValue {{
    font-size: 30px;
    font-weight: 700;
    letter-spacing: -0.6px;
    color: {COLOR_TEXT};
    min-height: 36px;
}}

QLabel#SectionTitle {{
    font-size: 21px;
    font-weight: 700;
    letter-spacing: -0.35px;
    color: {COLOR_TEXT};
    padding: 0 0 4px 0;
}}

QLabel#PageSubtitle {{
    font-size: 13px;
    color: {COLOR_TEXT_MUTED};
    padding-bottom: 10px;
}}

QLabel#HintLabel, QLabel#ProgressLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 12px;
    line-height: 1.45;
}}

/* ═══════════════ INPUTS ═══════════════ */
QLineEdit, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QComboBox {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {BTN_RADIUS};
    padding: 9px 12px;
    color: {COLOR_TEXT};
    selection-background-color: rgba(99, 102, 241, 0.2);
}}

QSpinBox, QDoubleSpinBox {{
    min-width: 108px;
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QPlainTextEdit:focus, QComboBox:focus {{
    border: 1px solid {ACCENT};
}}

QComboBox QAbstractItemView {{
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {BTN_RADIUS};
    selection-background-color: rgba(99, 102, 241, 0.15);
}}

/* ═══════════════ BUTTONS (accent only here) ═══════════════ */
QPushButton {{
    background-color: {ACCENT};
    color: #ffffff;
    border: none;
    border-radius: {BTN_RADIUS};
    padding: 9px 16px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {ACCENT_HOVER};
}}

QPushButton:pressed {{
    background-color: #4f46e5;
    padding-top: 10px;
    padding-bottom: 8px;
}}

QPushButton:disabled {{
    background-color: #e2e8f0;
    color: #94a3b8;
}}

QPushButton#PrimaryButton {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {ACCENT_HOVER},
        stop:1 {ACCENT}
    );
    border: 1px solid rgba(255, 255, 255, 0.2);
}}

QPushButton#GhostButton, QToolButton#SizeFilterButton {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT};
    font-weight: 500;
}}

QPushButton#GhostButton:hover {{
    border-color: {COLOR_BORDER_HI};
    background-color: #f8fafc;
}}

QPushButton#FilterChip {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT_MUTED};
    font-weight: 500;
    padding: 6px 12px;
    min-height: 16px;
}}

QPushButton#FilterChip:hover {{
    border-color: {COLOR_BORDER_HI};
    color: {COLOR_TEXT};
}}

QPushButton#FilterChip:checked {{
    background: rgba(99, 102, 241, 0.1);
    border-color: {ACCENT};
    color: {ACCENT};
    font-weight: 600;
}}

QPushButton#DangerButton {{
    background-color: #dc2626;
}}

/* ═══════════════ TABLE + SCROLL ═══════════════ */
QTableWidget {{
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {CARD_RADIUS};
    gridline-color: {COLOR_BORDER};
    alternate-background-color: #f8fafc;
}}

QHeaderView::section {{
    background: #f8fafc;
    padding: 11px 12px;
    border: none;
    border-bottom: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT_MUTED};
    font-size: 11px;
    font-weight: 600;
}}

QTableWidget::item {{
    padding: 11px 12px;
}}

QTableWidget::item:selected {{
    background-color: rgba(99, 102, 241, 0.12);
    color: {COLOR_TEXT};
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
}}

QScrollBar::handle:vertical {{
    background: rgba(20, 28, 45, 0.15);
    border-radius: 4px;
    min-height: 40px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid {COLOR_BORDER_HI};
    background: {COLOR_SURFACE};
}}

QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}

/* ═══════════════ DEAL CARDS ═══════════════ */
QLabel#DealTitle {{
    font-size: 14px;
    font-weight: 600;
}}

QLabel#DealPrice {{
    font-size: 19px;
    font-weight: 700;
    color: {COLOR_TEXT};
}}

QLabel#DealMeta {{
    font-size: 12px;
    color: {COLOR_TEXT_MUTED};
}}

QLabel#DealSavings {{
    font-size: 12px;
    color: {COLOR_SUCCESS};
    font-weight: 600;
}}

QLabel#PhotoLabel {{
    background: #f1f5f9;
    border: 1px solid {COLOR_BORDER};
    border-radius: {BTN_RADIUS};
    color: {COLOR_TEXT_MUTED};
}}

QPlainTextEdit#LogView {{
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {CARD_RADIUS};
    font-family: {FONT_MONO};
    font-size: 12px;
    padding: 12px;
}}

QMenu#SizeFilterMenu, QFrame#SizeFilterPopup {{
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {CARD_RADIUS};
}}

QMessageBox {{
    background: {COLOR_SURFACE};
}}
"""
