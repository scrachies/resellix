"""Resellix — 2026 glass UI with depth and readable controls."""
from __future__ import annotations

ACCENT = "#6366f1"
ACCENT_HOVER = "#818cf8"
ACCENT_DARK = "#4f46e5"

COLOR_BG = "#e4eaf4"
COLOR_SURFACE = "#ffffff"
COLOR_GLASS = "rgba(255, 255, 255, 0.72)"
COLOR_GLASS_SOLID = "rgba(255, 255, 255, 0.88)"

COLOR_BORDER = "rgba(15, 23, 42, 0.07)"
COLOR_BORDER_HI = "rgba(15, 23, 42, 0.12)"
COLOR_TEXT = "#0f172a"
COLOR_TEXT_MUTED = "#64748b"
COLOR_SUCCESS = "#059669"

FONT_UI = '"Segoe UI", "Inter", -apple-system, BlinkMacSystemFont, sans-serif'
FONT_MONO = '"Cascadia Code", "Consolas", monospace'

R_CARD = "18px"
R_BTN = "12px"
R_NAV = "11px"
R_CHIP = "9px"

SIDEBAR_GRADIENT = """
    qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #4a5d85, stop:0.4 #364a6e, stop:1 #1e2a42)
"""
SIDEBAR_SHINE = """
    qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 rgba(255,255,255,0.2), stop:0.12 rgba(255,255,255,0.06), stop:1 transparent)
"""
NAV_ACTIVE = """
    qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 rgba(255,255,255,0.26), stop:1 rgba(255,255,255,0.1))
"""
NAV_HOVER = """
    qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 rgba(255,255,255,0.12), stop:1 rgba(255,255,255,0.04))
"""

STYLESHEET = f"""
* {{
    font-family: {FONT_UI};
    color: {COLOR_TEXT};
    font-size: 13px;
}}

QMainWindow {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #e8edf6, stop:0.5 #e2e8f2, stop:1 #dce4f0);
}}

QWidget#ContentPage {{
    background: transparent;
}}

/* —— Sidebar —— */
QFrame#Sidebar {{
    background: {SIDEBAR_GRADIENT};
    border: none;
    border-right: 1px solid rgba(255,255,255,0.12);
}}
QFrame#BrandBlock {{
    background: {SIDEBAR_SHINE};
    border-bottom: 1px solid rgba(255,255,255,0.1);
}}
QLabel#BrandTitle {{ font-size: 22px; font-weight: 700; color: #fff; letter-spacing: -0.5px; }}
QLabel#BrandTagline {{ font-size: 12px; color: rgba(255,255,255,0.55); }}
QLabel#SidebarTier {{ font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.9); padding-top: 8px; }}
QPushButton#NavButton {{
    background: transparent; border: 1px solid transparent;
    text-align: left; padding: 12px 16px; margin: 2px 0;
    color: rgba(255,255,255,0.62); border-radius: {R_NAV}; font-weight: 500;
}}
QPushButton#NavButton:hover {{
    background: {NAV_HOVER}; color: #fff; border-color: rgba(255,255,255,0.14);
}}
QPushButton#NavButton:checked {{
    background: {NAV_ACTIVE}; color: #fff; font-weight: 600;
    border: 1px solid rgba(255,255,255,0.3);
}}
QLabel#SidebarAttribution {{ color: rgba(255,255,255,0.35); font-size: 9px; }}
QLabel#SidebarVersion {{ color: rgba(255,255,255,0.3); font-size: 10px; }}

/* —— Glass panels (shadow via QGraphicsDropShadowEffect in code) —— */
QFrame#GlassCard, QFrame#Card, QFrame#StatCard, QFrame#DealCard {{
    background-color: {COLOR_GLASS_SOLID};
    border: 1px solid rgba(255, 255, 255, 0.65);
    border-radius: {R_CARD};
}}
QFrame#StatusStrip {{
    background-color: {COLOR_GLASS_SOLID};
    border-bottom: 1px solid {COLOR_BORDER};
    min-height: 64px;
}}

QScrollArea#GlassScroll {{
    background: transparent;
    border: none;
}}

/* —— Typography —— */
QLabel#SectionTitle {{
    font-size: 24px; font-weight: 700; letter-spacing: -0.5px; color: {COLOR_TEXT};
}}
QLabel#PageSubtitle {{ font-size: 14px; color: {COLOR_TEXT_MUTED}; line-height: 1.45; }}
QLabel#CardSectionTitle {{
    font-size: 13px; font-weight: 700; color: {COLOR_TEXT};
    padding: 4px 0 8px 0;
    border-bottom: 1px solid {COLOR_BORDER};
    margin-bottom: 4px;
}}
QLabel#FormLabel {{
    font-size: 12px; font-weight: 600; color: {COLOR_TEXT_MUTED};
    padding: 0 0 4px 0;
}}
QLabel#CardTitle {{ font-size: 11px; font-weight: 700; color: {COLOR_TEXT_MUTED}; letter-spacing: 0.5px; }}
QLabel#CardValue {{ font-size: 30px; font-weight: 700; color: {COLOR_TEXT}; min-height: 36px; }}
QLabel#HintLabel, QLabel#ProgressLabel, QLabel#ToolbarLabel {{
    color: {COLOR_TEXT_MUTED}; font-size: 12px;
}}
QLabel#ToolbarLabel {{ font-weight: 600; min-width: 0; padding: 0 4px; }}

QLabel#StatusDot {{ background: {COLOR_SUCCESS}; border-radius: 5px; min-width:9px; max-width:9px; min-height:9px; max-height:9px; }}
QLabel#StatusDotPaused {{ background: #d97706; border-radius: 5px; min-width:9px; max-width:9px; min-height:9px; max-height:9px; }}
QLabel#StatusDotError {{ background: #94a3b8; border-radius: 5px; min-width:9px; max-width:9px; min-height:9px; max-height:9px; }}

/* —— Inputs —— */
QLineEdit, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QComboBox {{
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER_HI};
    border-radius: {R_BTN};
    padding: 11px 14px;
    min-height: 22px;
    font-size: 13px;
    color: {COLOR_TEXT};
}}
QSpinBox, QDoubleSpinBox {{ min-width: 120px; min-height: 40px; }}
QComboBox {{ min-height: 40px; padding-right: 28px; }}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {{
    border: 2px solid {ACCENT};
    background: #fff;
}}
QComboBox QAbstractItemView {{
    background: #fff; border: 1px solid {COLOR_BORDER}; border-radius: {R_BTN};
    padding: 6px; selection-background-color: rgba(99,102,241,0.15);
}}

/* —— Buttons (readable, tall, floating look) —— */
QPushButton {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {ACCENT_HOVER}, stop:1 {ACCENT});
    color: #ffffff;
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: {R_BTN};
    padding: 12px 20px;
    min-height: 22px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #a5b4fc, stop:1 {ACCENT_HOVER});
}}
QPushButton:pressed {{
    background: {ACCENT_DARK};
    padding-top: 13px; padding-bottom: 11px;
}}
QPushButton:disabled {{ background: #e2e8f0; color: #94a3b8; border-color: #e2e8f0; }}

QPushButton#PrimaryButton {{
    min-height: 42px;
    padding: 12px 24px;
    font-size: 14px;
}}
QPushButton#GhostButton {{
    background: {COLOR_SURFACE};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER_HI};
    font-weight: 600;
    min-height: 40px;
}}
QPushButton#GhostButton:hover {{
    background: #f8fafc;
    border-color: {ACCENT};
    color: {ACCENT_DARK};
}}
QPushButton#DangerButton {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #f87171, stop:1 #dc2626);
    border: 1px solid rgba(255,255,255,0.2);
}}

QPushButton#FilterChip {{
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER_HI};
    color: {COLOR_TEXT_MUTED};
    font-weight: 600;
    padding: 8px 14px;
    min-height: 18px;
    border-radius: {R_CHIP};
}}
QPushButton#FilterChip:hover {{ border-color: {ACCENT}; color: {COLOR_TEXT}; }}
QPushButton#FilterChip:checked {{
    background: rgba(99,102,241,0.12);
    border: 2px solid {ACCENT};
    color: {ACCENT_DARK};
}}

/* —— Checkboxes as chips —— */
QCheckBox#ChipCheck {{
    spacing: 8px;
    padding: 8px 12px;
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {R_CHIP};
    color: {COLOR_TEXT};
    font-weight: 500;
}}
QCheckBox#ChipCheck:hover {{
    border-color: {ACCENT};
    background: #f8fafc;
}}
QCheckBox#ChipCheck::indicator {{
    width: 16px; height: 16px;
    border-radius: 4px;
    border: 2px solid {COLOR_BORDER_HI};
    background: #fff;
}}
QCheckBox#ChipCheck::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QCheckBox {{
    spacing: 10px;
    padding: 6px 4px;
    color: {COLOR_TEXT};
}}
QCheckBox::indicator {{
    width: 20px; height: 20px;
    border-radius: 6px;
    border: 2px solid {COLOR_BORDER_HI};
    background: #fff;
}}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}

/* —— Tables —— */
QTableWidget {{
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {R_CARD};
    gridline-color: {COLOR_BORDER};
    alternate-background-color: #f8fafc;
}}
QHeaderView::section {{
    background: #f1f5f9;
    padding: 14px 16px;
    border: none;
    border-bottom: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT_MUTED};
    font-size: 11px;
    font-weight: 700;
}}
QTableWidget::item {{ padding: 14px 16px; }}
QTableWidget::item:selected {{ background: rgba(99,102,241,0.12); color: {COLOR_TEXT}; }}

QScrollBar:vertical {{
    background: transparent; width: 10px; margin: 6px 2px;
}}
QScrollBar::handle:vertical {{
    background: rgba(15,23,42,0.2); border-radius: 5px; min-height: 48px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QLabel#DealTitle {{ font-size: 15px; font-weight: 600; }}
QLabel#DealPrice {{ font-size: 20px; font-weight: 700; color: {COLOR_TEXT}; }}
QLabel#DealMeta {{ font-size: 12px; color: {COLOR_TEXT_MUTED}; }}
QLabel#PhotoLabel {{
    background: #f1f5f9; border: 1px solid {COLOR_BORDER}; border-radius: {R_BTN};
}}
QPlainTextEdit#LogView {{
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {R_CARD};
    font-family: {FONT_MONO};
    padding: 14px;
}}
QMenu#SizeFilterMenu, QFrame#SizeFilterPopup {{
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {R_CARD};
}}
"""
