"""Resellix — dark glassmorphism (cyan → purple accents)."""
from __future__ import annotations

# Accent gradients (mockup style)
GRAD_PRIMARY = """
    qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #22d3ee, stop:0.45 #818cf8, stop:1 #c084fc)
"""
GRAD_STOP = """
    qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #f472b6, stop:0.5 #e879f9, stop:1 #a855f7)
"""
GRAD_NAV_ACTIVE = """
    qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #06b6d4, stop:0.5 #8b5cf6, stop:1 #d946ef)
"""
GRAD_DANGER = """
    qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #fb7185, stop:1 #ef4444)
"""

COLOR_TEXT = "#f1f5f9"
COLOR_TEXT_MUTED = "rgba(241, 245, 249, 0.55)"
COLOR_CYAN = "#22d3ee"
COLOR_GREEN = "#34d399"

FONT_UI = '"Segoe UI", "Inter", -apple-system, BlinkMacSystemFont, sans-serif'
FONT_MONO = '"Cascadia Code", "JetBrains Mono", Consolas, monospace'

R_CARD = "20px"
R_BTN = "14px"
R_NAV = "14px"
R_CHIP = "10px"
R_INPUT = "12px"

# App background — soft purple / teal / pink wash
BG_MAIN = """
    qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #1e1b4b,
        stop:0.35 #312e81,
        stop:0.65 #4c1d95,
        stop:1 #831843)
"""

# Frosted glass surfaces
GLASS_PANEL = "rgba(255, 255, 255, 0.08)"
GLASS_PANEL_HI = "rgba(255, 255, 255, 0.12)"
GLASS_BORDER = "rgba(255, 255, 255, 0.22)"
GLASS_BORDER_SOFT = "rgba(255, 255, 255, 0.12)"

SIDEBAR_GLASS = """
    qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 rgba(255,255,255,0.14),
        stop:0.5 rgba(255,255,255,0.06),
        stop:1 rgba(0,0,0,0.15))
"""

STYLESHEET = f"""
* {{
    font-family: {FONT_UI};
    color: {COLOR_TEXT};
    font-size: 13px;
}}

QMainWindow, QWidget#AppCanvas {{
    background: {BG_MAIN};
}}

QWidget {{
    background: transparent;
}}

QWidget#ContentPage {{
    background: transparent;
}}

QDialog {{
    background-color: #1e1b4b;
    color: {COLOR_TEXT};
}}

/* ═══ Sidebar glass ═══ */
QFrame#Sidebar {{
    background: {SIDEBAR_GLASS};
    border: none;
    border-right: 1px solid {GLASS_BORDER_SOFT};
}}

QFrame#BrandBlock {{
    background: transparent;
    border-bottom: 1px solid {GLASS_BORDER_SOFT};
}}

QFrame#SidebarNav, QFrame#SidebarFooter {{
    background: transparent;
    border: none;
}}

QFrame#SidebarFooter {{
    border-top: 1px solid {GLASS_BORDER_SOFT};
}}

QLabel#BrandTitle {{
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.5px;
}}

QLabel#BrandTagline {{
    font-size: 12px;
    color: {COLOR_TEXT_MUTED};
}}

QLabel#SidebarTier {{
    font-size: 11px;
    font-weight: 600;
    color: {COLOR_CYAN};
    padding-top: 8px;
}}

QPushButton#NavButton {{
    background: transparent;
    border: 1px solid transparent;
    text-align: left;
    padding: 12px 18px;
    margin: 3px 0;
    color: {COLOR_TEXT_MUTED};
    border-radius: {R_NAV};
    font-weight: 500;
    font-size: 13px;
}}

QPushButton#NavButton:hover {{
    background: rgba(255, 255, 255, 0.1);
    color: #ffffff;
    border: 1px solid {GLASS_BORDER_SOFT};
}}

QPushButton#NavButton:checked {{
    background: {GRAD_NAV_ACTIVE};
    color: #ffffff;
    font-weight: 600;
    border: 1px solid rgba(255, 255, 255, 0.35);
}}

QPushButton#NavButton:pressed {{
    padding-top: 13px;
    padding-bottom: 11px;
}}

QLabel#SidebarAttribution {{
    color: rgba(255, 255, 255, 0.32);
    font-size: 9px;
    line-height: 1.4;
}}

QLabel#SidebarVersion {{
    color: rgba(255, 255, 255, 0.28);
    font-size: 10px;
}}

QFrame#SidebarUpdateBanner {{
    background: rgba(0, 0, 0, 0.25);
    border: 1px solid {GLASS_BORDER_SOFT};
    border-radius: {R_NAV};
}}
QLabel#SidebarUpdateTitle {{ color: {COLOR_CYAN}; font-weight: 600; font-size: 11px; }}
QLabel#SidebarUpdateText {{ color: {COLOR_TEXT_MUTED}; font-size: 10px; }}

/* ═══ Top status bar ═══ */
QFrame#StatusStrip {{
    background: {GLASS_PANEL_HI};
    border-bottom: 1px solid {GLASS_BORDER_SOFT};
    min-height: 64px;
}}

QLabel#StatusText {{
    color: #ffffff;
    font-size: 14px;
    font-weight: 600;
}}

QLabel#StatusDot {{
    background: {COLOR_GREEN};
    border: 2px solid rgba(52, 211, 153, 0.5);
    border-radius: 6px;
    min-width: 10px; max-width: 10px;
    min-height: 10px; max-height: 10px;
}}

QLabel#StatusDotPaused {{
    background: #fbbf24;
    border-radius: 6px;
    min-width: 10px; max-width: 10px;
    min-height: 10px; max-height: 10px;
}}

QLabel#StatusDotError {{
    background: #94a3b8;
    border-radius: 6px;
    min-width: 10px; max-width: 10px;
    min-height: 10px; max-height: 10px;
}}

QLabel#ToolbarLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 12px;
    font-weight: 500;
    padding: 0 6px;
}}

/* ═══ Glass cards ═══ */
QFrame#GlassCard, QFrame#StatCard, QFrame#DealCard {{
    background: {GLASS_PANEL};
    border: 1px solid {GLASS_BORDER};
    border-radius: {R_CARD};
}}

QFrame#DealCard:hover {{
    background: {GLASS_PANEL_HI};
    border-color: rgba(255, 255, 255, 0.32);
}}

QLabel#SectionTitle {{
    font-size: 26px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.5px;
}}

QLabel#PageSubtitle {{
    font-size: 14px;
    color: {COLOR_TEXT_MUTED};
    line-height: 1.5;
}}

QLabel#CardSectionTitle {{
    font-size: 14px;
    font-weight: 700;
    color: #ffffff;
    padding: 0 0 10px 0;
    border-bottom: 1px solid {GLASS_BORDER_SOFT};
}}

QLabel#FormLabel {{
    font-size: 12px;
    font-weight: 600;
    color: {COLOR_TEXT_MUTED};
    padding-bottom: 4px;
}}

QLabel#CardTitle {{
    font-size: 11px;
    font-weight: 700;
    color: {COLOR_TEXT_MUTED};
    letter-spacing: 0.6px;
}}

QLabel#CardValue {{
    font-size: 32px;
    font-weight: 700;
    color: #ffffff;
    min-height: 38px;
}}

QLabel#HintLabel, QLabel#ProgressLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 12px;
    line-height: 1.45;
}}

/* ═══ Inputs (bright on glass) ═══ */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: rgba(255, 255, 255, 0.94);
    border: 1px solid rgba(255, 255, 255, 0.4);
    border-radius: {R_INPUT};
    padding: 11px 14px;
    min-height: 22px;
    color: #0f172a;
    font-size: 13px;
    selection-background-color: #c4b5fd;
}}

QPlainTextEdit {{
    background: rgba(15, 18, 35, 0.75);
    border: 1px solid {GLASS_BORDER};
    border-radius: {R_CARD};
    padding: 16px;
    color: #e2e8f0;
    font-family: {FONT_MONO};
    font-size: 12px;
    selection-background-color: rgba(139, 92, 246, 0.4);
}}

QPlainTextEdit#LogView {{
    background: rgba(12, 14, 28, 0.82);
    border: 1px solid {GLASS_BORDER};
    color: #cbd5e1;
}}

QSpinBox, QDoubleSpinBox {{
    min-width: 120px;
    min-height: 42px;
}}

QComboBox {{
    min-height: 42px;
    padding-right: 28px;
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 2px solid #8b5cf6;
    background: #ffffff;
}}

QComboBox QAbstractItemView {{
    background: #1e1b4b;
    color: {COLOR_TEXT};
    border: 1px solid {GLASS_BORDER};
    border-radius: {R_INPUT};
    selection-background-color: rgba(139, 92, 246, 0.35);
}}

/* ═══ Buttons ═══ */
QPushButton {{
    background: {GRAD_PRIMARY};
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: {R_BTN};
    padding: 12px 22px;
    min-height: 24px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton:hover {{
    border: 1px solid rgba(255, 255, 255, 0.5);
}}

QPushButton:pressed {{
    padding-top: 13px;
    padding-bottom: 11px;
}}

QPushButton:disabled {{
    background: rgba(255, 255, 255, 0.12);
    color: rgba(255, 255, 255, 0.35);
    border-color: transparent;
}}

QPushButton#PrimaryButton {{
    background: {GRAD_PRIMARY};
    min-height: 44px;
    font-size: 14px;
}}

QPushButton#StopButton {{
    background: {GRAD_STOP};
    min-height: 44px;
    font-size: 14px;
}}

QPushButton#GhostButton {{
    background: rgba(255, 255, 255, 0.92);
    color: #1e1b4b;
    border: 1px solid rgba(255, 255, 255, 0.5);
    font-weight: 600;
    min-height: 42px;
}}

QPushButton#GhostButton:hover {{
    background: #ffffff;
}}

QPushButton#DangerButton {{
    background: {GRAD_DANGER};
    min-height: 36px;
    padding: 8px 16px;
}}

QPushButton#FilterChip {{
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid {GLASS_BORDER_SOFT};
    color: {COLOR_TEXT_MUTED};
    font-weight: 600;
    padding: 8px 14px;
    border-radius: {R_CHIP};
}}

QPushButton#FilterChip:hover {{
    background: rgba(255, 255, 255, 0.16);
    color: #ffffff;
}}

QPushButton#FilterChip:checked {{
    background: {GRAD_NAV_ACTIVE};
    border: 1px solid rgba(255, 255, 255, 0.35);
    color: #ffffff;
}}

/* ═══ Checkboxes ═══ */
QCheckBox#ChipCheck {{
    spacing: 8px;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid {GLASS_BORDER_SOFT};
    border-radius: {R_CHIP};
    color: {COLOR_TEXT};
}}

QCheckBox#ChipCheck:hover {{
    background: rgba(255, 255, 255, 0.14);
    border-color: {GLASS_BORDER};
}}

QCheckBox#ChipCheck::indicator {{
    width: 16px; height: 16px;
    border-radius: 4px;
    border: 2px solid rgba(255, 255, 255, 0.35);
    background: rgba(0, 0, 0, 0.2);
}}

QCheckBox#ChipCheck::indicator:checked {{
    background: {GRAD_NAV_ACTIVE};
    border-color: #c084fc;
}}

QCheckBox {{
    color: {COLOR_TEXT};
    spacing: 10px;
}}

QCheckBox::indicator {{
    width: 18px; height: 18px;
    border-radius: 5px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    background: rgba(0, 0, 0, 0.2);
}}

QCheckBox::indicator:checked {{
    background: #8b5cf6;
    border-color: #c084fc;
}}

/* ═══ Tables ═══ */
QTableWidget {{
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid {GLASS_BORDER_SOFT};
    border-radius: {R_CARD};
    gridline-color: rgba(255, 255, 255, 0.08);
    color: {COLOR_TEXT};
    alternate-background-color: rgba(255, 255, 255, 0.04);
}}

QHeaderView::section {{
    background: rgba(255, 255, 255, 0.08);
    color: {COLOR_TEXT_MUTED};
    padding: 14px 16px;
    border: none;
    border-bottom: 1px solid {GLASS_BORDER_SOFT};
    font-size: 11px;
    font-weight: 700;
}}

QTableWidget::item {{
    padding: 14px 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}}

QTableWidget::item:selected {{
    background: rgba(139, 92, 246, 0.25);
    color: #ffffff;
}}

/* ═══ Scrollbars ═══ */
QScrollArea#GlassScroll {{
    background: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 6px 2px;
}}

QScrollBar::handle:vertical {{
    background: rgba(255, 255, 255, 0.25);
    border-radius: 4px;
    min-height: 40px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ═══ Deal rows ═══ */
QLabel#DealTitle {{ font-size: 15px; font-weight: 600; color: #ffffff; }}
QLabel#DealPrice {{ font-size: 20px; font-weight: 700; color: {COLOR_CYAN}; }}
QLabel#DealMeta {{ font-size: 12px; color: {COLOR_TEXT_MUTED}; }}
QLabel#DealSavings {{ font-size: 12px; color: {COLOR_GREEN}; font-weight: 600; }}

QLabel#PhotoLabel {{
    background: rgba(0, 0, 0, 0.35);
    border: 1px solid {GLASS_BORDER_SOFT};
    border-radius: {R_INPUT};
    color: {COLOR_TEXT_MUTED};
}}

QMenu#SizeFilterMenu, QFrame#SizeFilterPopup {{
    background: #1e1b4b;
    border: 1px solid {GLASS_BORDER};
    border-radius: {R_CARD};
    color: {COLOR_TEXT};
}}

QMessageBox {{
    background: #312e81;
    color: {COLOR_TEXT};
}}
"""
