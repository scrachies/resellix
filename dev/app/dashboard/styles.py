"""Resellix — dark glassmorphism (cyan → purple accents)."""
from __future__ import annotations

# Accent gradients (mockup style)
GRAD_PRIMARY = """
    qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #22d3ee, stop:0.4 #6366f1, stop:0.75 #a78bfa, stop:1 #e879f9)
"""
GRAD_PRIMARY_HOVER = """
    qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #67e8f9, stop:0.4 #818cf8, stop:0.75 #c4b5fd, stop:1 #f0abfc)
"""
GRAD_STOP = """
    qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #fb7185, stop:0.45 #f472b6, stop:1 #c026d3)
"""
GRAD_NAV_ACTIVE = """
    qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 rgba(6,182,212,0.95), stop:0.5 rgba(139,92,246,0.95), stop:1 rgba(217,70,239,0.95))
"""
GRAD_DANGER = """
    qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #fb7185, stop:1 #ef4444)
"""

COLOR_TEXT = "#f8fafc"
COLOR_TEXT_MUTED = "rgba(248, 250, 252, 0.58)"
COLOR_CYAN = "#22d3ee"
COLOR_GREEN = "#34d399"

FONT_UI = '"Segoe UI", "Inter", -apple-system, BlinkMacSystemFont, sans-serif'
FONT_MONO = '"Cascadia Code", "JetBrains Mono", Consolas, monospace'

R_CARD = "22px"
R_BTN = "999px"
R_NAV = "14px"
R_CHIP = "999px"
R_INPUT = "14px"

# App background — soft purple / teal / pink wash
BG_MAIN = """
    qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #0f0a1f,
        stop:0.28 #1e1b4b,
        stop:0.55 #312e81,
        stop:0.82 #4c1d95,
        stop:1 #701a4b)
"""

# Frosted glass surfaces (layered — top highlight like reference mockups)
GLASS_PANEL = """
    qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 rgba(255, 255, 255, 0.14),
        stop:0.12 rgba(255, 255, 255, 0.09),
        stop:1 rgba(255, 255, 255, 0.04))
"""
GLASS_PANEL_HI = """
    qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 rgba(255, 255, 255, 0.18),
        stop:0.15 rgba(255, 255, 255, 0.11),
        stop:1 rgba(255, 255, 255, 0.05))
"""
GLASS_BORDER = "rgba(255, 255, 255, 0.28)"
GLASS_BORDER_TOP = "rgba(255, 255, 255, 0.42)"
GLASS_BORDER_SOFT = "rgba(255, 255, 255, 0.14)"

SIDEBAR_GLASS = """
    qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 rgba(255,255,255,0.16),
        stop:0.45 rgba(255,255,255,0.07),
        stop:1 rgba(0,0,0,0.22))
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
    font-size: 22px;
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
    padding-top: 6px;
}}

QPushButton#NavButton {{
    background: transparent;
    border: 1px solid transparent;
    text-align: left;
    padding: 11px 16px;
    margin: 2px 0;
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
    border: 1px solid {GLASS_BORDER_TOP};
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
    background: rgba(0, 0, 0, 0.28);
    border: 1px solid {GLASS_BORDER_SOFT};
    border-top: 1px solid {GLASS_BORDER_TOP};
    border-radius: {R_NAV};
}}
QLabel#SidebarUpdateTitle {{ color: {COLOR_CYAN}; font-weight: 600; font-size: 11px; }}
QLabel#SidebarUpdateText {{ color: {COLOR_TEXT_MUTED}; font-size: 10px; }}

/* ═══ Top status bar ═══ */
QFrame#StatusStrip {{
    background: {GLASS_PANEL_HI};
    border: none;
    border-bottom: 1px solid {GLASS_BORDER_SOFT};
    min-height: 56px;
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
    padding: 0 4px;
}}

/* ═══ Glass cards ═══ */
QFrame#GlassCard, QFrame#StatCard, QFrame#DealCard, QFrame#ToolbarGlass {{
    background: {GLASS_PANEL};
    border: 1px solid {GLASS_BORDER_SOFT};
    border-top: 1px solid {GLASS_BORDER_TOP};
    border-radius: {R_CARD};
}}

QFrame#DealCard:hover, QFrame#ToolbarGlass:hover {{
    background: {GLASS_PANEL_HI};
    border-color: {GLASS_BORDER};
}}

QLabel#SectionTitle {{
    font-size: 24px;
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
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
    min-height: 34px;
}}

QLabel#HintLabel, QLabel#ProgressLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 12px;
    line-height: 1.45;
}}

/* ═══ Inputs (frosted on glass) ═══ */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: rgba(15, 12, 35, 0.55);
    border: 1px solid {GLASS_BORDER_SOFT};
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: {R_INPUT};
    padding: 10px 14px;
    min-height: 20px;
    color: {COLOR_TEXT};
    font-size: 13px;
    selection-background-color: rgba(139, 92, 246, 0.45);
}}

QPlainTextEdit {{
    background: rgba(12, 14, 28, 0.72);
    border: 1px solid {GLASS_BORDER_SOFT};
    border-top: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: {R_CARD};
    padding: 16px;
    color: #e2e8f0;
    font-family: {FONT_MONO};
    font-size: 12px;
    selection-background-color: rgba(139, 92, 246, 0.4);
}}

QPlainTextEdit#LogView {{
    background: rgba(8, 10, 22, 0.78);
    border: 1px solid {GLASS_BORDER_SOFT};
    color: #cbd5e1;
}}

QSpinBox, QDoubleSpinBox {{
    min-width: 100px;
    min-height: 40px;
}}

QComboBox {{
    min-height: 40px;
    padding-right: 28px;
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid rgba(139, 92, 246, 0.75);
    background: rgba(20, 16, 48, 0.72);
}}

QComboBox::drop-down {{
    border: none;
    width: 28px;
}}

QComboBox QAbstractItemView {{
    background: #1e1b4b;
    color: {COLOR_TEXT};
    border: 1px solid {GLASS_BORDER};
    border-radius: {R_INPUT};
    selection-background-color: rgba(139, 92, 246, 0.35);
    padding: 4px;
}}

/* ═══ Buttons — pill gradient + glass secondary ═══ */
QPushButton {{
    background: {GRAD_PRIMARY};
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-radius: {R_BTN};
    padding: 11px 24px;
    min-height: 22px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton:hover {{
    background: {GRAD_PRIMARY_HOVER};
    border: 1px solid rgba(255, 255, 255, 0.5);
}}

QPushButton:pressed {{
    padding-top: 12px;
    padding-bottom: 10px;
}}

QPushButton:disabled {{
    background: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.32);
    border-color: rgba(255, 255, 255, 0.08);
}}

QPushButton#PrimaryButton {{
    background: {GRAD_PRIMARY};
    min-height: 42px;
    min-width: 120px;
    padding: 12px 28px;
    font-size: 14px;
    font-weight: 700;
    border: 1px solid rgba(255, 255, 255, 0.4);
}}

QPushButton#PrimaryButton:hover {{
    background: {GRAD_PRIMARY_HOVER};
}}

QPushButton#StopButton {{
    background: {GRAD_STOP};
    min-height: 42px;
    min-width: 120px;
    padding: 12px 28px;
    font-size: 14px;
    font-weight: 700;
    border: 1px solid rgba(255, 255, 255, 0.38);
}}

QPushButton#GhostButton {{
    background: rgba(255, 255, 255, 0.1);
    color: #ffffff;
    border: 1px solid {GLASS_BORDER};
    border-top: 1px solid {GLASS_BORDER_TOP};
    font-weight: 600;
    min-height: 40px;
    padding: 10px 22px;
}}

QPushButton#GhostButton:hover {{
    background: rgba(255, 255, 255, 0.16);
    border-color: rgba(255, 255, 255, 0.38);
}}

QPushButton#DangerButton {{
    background: {GRAD_DANGER};
    min-height: 34px;
    padding: 8px 18px;
    font-size: 12px;
}}

QPushButton#FilterChip {{
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid {GLASS_BORDER_SOFT};
    border-top: 1px solid rgba(255, 255, 255, 0.16);
    color: {COLOR_TEXT_MUTED};
    font-weight: 600;
    padding: 8px 16px;
    border-radius: {R_CHIP};
    min-height: 18px;
}}

QPushButton#FilterChip:hover {{
    background: rgba(255, 255, 255, 0.12);
    color: #ffffff;
}}

QPushButton#FilterChip:checked {{
    background: {GRAD_NAV_ACTIVE};
    border: 1px solid {GLASS_BORDER_TOP};
    color: #ffffff;
}}

/* ═══ Checkboxes ═══ */
QCheckBox#ChipCheck {{
    spacing: 8px;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid {GLASS_BORDER_SOFT};
    border-top: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: {R_CHIP};
    color: {COLOR_TEXT};
}}

QCheckBox#ChipCheck:hover {{
    background: rgba(255, 255, 255, 0.11);
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
    background: rgba(0, 0, 0, 0.22);
    border: 1px solid {GLASS_BORDER_SOFT};
    border-top: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: {R_CARD};
    gridline-color: rgba(255, 255, 255, 0.06);
    color: {COLOR_TEXT};
    alternate-background-color: rgba(255, 255, 255, 0.04);
}}

QHeaderView::section {{
    background: rgba(255, 255, 255, 0.08);
    color: {COLOR_TEXT_MUTED};
    padding: 12px 14px;
    border: none;
    border-bottom: 1px solid {GLASS_BORDER_SOFT};
    font-size: 11px;
    font-weight: 700;
}}

QTableWidget::item {{
    padding: 12px 14px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}}

QTableWidget::item:selected {{
    background: rgba(139, 92, 246, 0.28);
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
    background: rgba(255, 255, 255, 0.22);
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
