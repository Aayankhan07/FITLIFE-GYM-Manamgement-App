"""
FitLife — Theme Manager
Manages dark/light theme switching with full QSS stylesheets.
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase
import logging

logger = logging.getLogger(__name__)

# ─── Color Palettes ───────────────────────────────────────────────────────────
DARK_COLORS = {
    "bg_primary":       "#0A0E2A",
    "bg_secondary":     "#0D153A",
    "bg_tertiary":      "#0D1B2A",
    "accent_primary":   "#0066FF",
    "accent_secondary": "#00F5FF",
    "accent_danger":    "#FF2D78",
    "accent_warning":   "#FFB800",
    "accent_success":   "#00E676",
    "text_primary":     "#F0F4FF",
    "text_secondary":   "#9CA3AF",
    "text_muted":       "#6B7280",
    "glass_bg":         "rgba(255,255,255,0.07)",
    "glass_border":     "rgba(0,102,255,0.3)",
    "card_bg":          "rgba(255,255,255,0.05)",
    "input_bg":         "rgba(255,255,255,0.08)",
    "hover_bg":         "rgba(0,102,255,0.15)",
    "sidebar_bg":       "rgba(10,14,42,0.95)",
    "row_hover":        "rgba(0,102,255,0.1)",
    "table_header":     "rgba(0,102,255,0.2)",
}

LIGHT_COLORS = {
    "bg_primary":       "#F0F6FF",
    "bg_secondary":     "#E8F4FF",
    "bg_tertiary":      "#F3F4F6",
    "accent_primary":   "#0066FF",
    "accent_secondary": "#0891B2",
    "accent_danger":    "#DC2626",
    "accent_warning":   "#D97706",
    "accent_success":   "#16A34A",
    "text_primary":     "#1A1033",
    "text_secondary":   "#374151",
    "text_muted":       "#6B7280",
    "glass_bg":         "rgba(255,255,255,0.75)",
    "glass_border":     "rgba(0,102,255,0.2)",
    "card_bg":          "rgba(255,255,255,0.85)",
    "input_bg":         "rgba(255,255,255,0.9)",
    "hover_bg":         "rgba(0,102,255,0.08)",
    "sidebar_bg":       "rgba(240,246,255,0.97)",
    "row_hover":        "rgba(0,102,255,0.06)",
    "table_header":     "rgba(0,102,255,0.1)",
}


def _make_stylesheet(c: dict) -> str:
    return f"""
/* ── GLOBAL ─────────────────────────────────────── */
QWidget {{
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 14px;
    color: {c['text_primary']};
    background-color: transparent;
}}

QMainWindow, QDialog {{
    background-color: {c['bg_primary']};
}}

QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: transparent; width: 8px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {c['accent_primary']}; border-radius: 4px; min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent; height: 8px; margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {c['accent_primary']}; border-radius: 4px; min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── GLASS CARD ─────────────────────────────────── */
QFrame#glassCard {{
    background: {c['glass_bg']};
    border: 1px solid {c['glass_border']};
    border-radius: 16px;
}}

/* ── SIDEBAR ─────────────────────────────────────── */
QWidget#sidebar {{
    background: {c['sidebar_bg']};
    border-right: 1px solid {c['glass_border']};
}}
QPushButton#sidebarBtn {{
    background: transparent;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0px 12px 12px 0px;
    color: {c['text_secondary']};
    text-align: left;
    padding: 10px 16px;
    font-size: 14px;
}}
QPushButton#sidebarBtn:hover {{
    background: {c['hover_bg']};
    color: {c['text_primary']};
    border-left: 3px solid {c['accent_primary']};
}}
QPushButton#sidebarBtn[active="true"] {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {c['accent_primary']}, stop:1 rgba(0,102,255,0.4));
    color: {c['text_primary']};
    border-left: 3px solid {c['accent_secondary']};
}}
QPushButton#sidebarBtn[collapsed="true"] {{
    text-align: center;
    padding: 10px 0px;
    border-radius: 12px;
    border-left: none;
}}
QPushButton#sidebarBtn[collapsed="true"]:hover {{
    border-left: none;
}}
QPushButton#sidebarBtn[collapsed="true"][active="true"] {{
    border-left: none;
}}

/* ── TOPBAR ──────────────────────────────────────── */
QWidget#topbar {{
    background: {c['glass_bg']};
    border-bottom: 1px solid {c['glass_border']};
}}

/* ── KPI CARD ────────────────────────────────────── */
QFrame#kpiCard {{
    background: {c['card_bg']};
    border: 1px solid {c['glass_border']};
    border-radius: 16px;
}}

/* ── INPUTS ──────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
    background: {c['input_bg']};
    border: 1px solid {c['glass_border']};
    border-radius: 10px;
    padding: 8px 14px;
    color: {c['text_primary']};
    selection-background-color: {c['accent_primary']};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1.5px solid {c['accent_primary']};
}}
QLineEdit[error="true"] {{
    border: 1.5px solid {c['accent_danger']};
}}

QDateEdit {{
    background: {c['input_bg']};
    border: 1px solid {c['glass_border']};
    border-radius: 10px;
    padding: 8px 14px;
    color: {c['text_primary']};
}}
QDateEdit:focus {{ border: 1.5px solid {c['accent_primary']}; }}
QDateEdit::drop-down {{
    border: none;
    width: 24px;
}}
QCalendarWidget {{
    background: {c['bg_secondary']};
    color: {c['text_primary']};
    border: 1px solid {c['glass_border']};
    border-radius: 12px;
}}
QCalendarWidget QToolButton {{
    background: {c['accent_primary']};
    color: {c['text_primary']};
    border-radius: 6px;
    padding: 4px 8px;
}}
QCalendarWidget QAbstractItemView {{
    background: {c['bg_secondary']};
    color: {c['text_primary']};
    selection-background-color: {c['accent_primary']};
    gridline-color: {c['glass_border']};
}}

QComboBox {{
    background: {c['input_bg']};
    border: 1px solid {c['glass_border']};
    border-radius: 10px;
    padding: 8px 14px;
    color: {c['text_primary']};
    min-width: 100px;
}}
QComboBox:focus {{ border: 1.5px solid {c['accent_primary']}; }}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {c['text_secondary']};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background: {c['bg_secondary']};
    border: 1px solid {c['glass_border']};
    border-radius: 10px;
    color: {c['text_primary']};
    selection-background-color: {c['accent_primary']};
    padding: 4px;
}}

/* ── BUTTONS ─────────────────────────────────────── */
/* Base catch-all — ensures button text is ALWAYS visible */
QPushButton {{
    color: {c['text_primary']};
    font-size: 13px;
    font-weight: 600;
    border: 1px solid {c['glass_border']};
    border-radius: 8px;
    padding: 6px 14px;
    min-height: 26px;
    background: rgba(255,255,255,0.08);
}}
QPushButton:hover {{
    background: {c['hover_bg']};
    color: {c['text_primary']};
}}
QPushButton:disabled {{
    color: {c['text_muted']};
    background: rgba(255,255,255,0.03);
}}

QPushButton#btnPrimary {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {c['accent_primary']}, stop:1 #1D4ED8);
    border: none;
    border-radius: 10px;
    color: #FFFFFF;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton#btnPrimary:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #3B82F6, stop:1 {c['accent_primary']});
}}
QPushButton#btnPrimary:pressed {{ padding: 11px 23px 9px 25px; }}
QPushButton#btnPrimary:disabled {{
    background: {c['text_muted']}; color: {c['text_secondary']};
}}

QPushButton#btnSecondary {{
    background: transparent;
    border: 1.5px solid {c['accent_primary']};
    border-radius: 10px;
    color: {c['accent_primary']};
    padding: 9px 22px;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton#btnSecondary:hover {{
    background: {c['hover_bg']};
    color: {c['text_primary']};
}}

QPushButton#btnDanger {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {c['accent_danger']}, stop:1 #B91C4C);
    border: none;
    border-radius: 10px;
    color: #FFFFFF;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton#btnDanger:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #FF4D8D, stop:1 {c['accent_danger']});
}}

QPushButton#btnSuccess {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {c['accent_success']}, stop:1 #00A854);
    border: none;
    border-radius: 10px;
    color: #0A0E2A;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton#btnWarning {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {c['accent_warning']}, stop:1 #D97706);
    border: none; border-radius: 10px;
    color: #0A0E2A; padding: 10px 24px;
    font-size: 14px; font-weight: bold;
}}
QPushButton#btnIcon {{
    background: transparent; border: none;
    border-radius: 8px; padding: 6px;
    color: {c['text_secondary']};
}}
QPushButton#btnIcon:hover {{
    background: {c['hover_bg']};
    color: {c['accent_primary']};
}}

/* ── ACTION BUTTONS (table rows) ──────────────────── */
/* Base — ensures text is always white unless overridden */
QPushButton[class="btn-view"] {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #0097B2, stop:1 #00D4E8);
    color: #001A1F;
    border: none; border-radius: 6px;
    font-size: 11px; font-weight: 600;
    padding: 3px 10px; min-height: 26px;
}}
QPushButton[class="btn-view"]:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #00B8D9, stop:1 #00F5FF);
}}
QPushButton[class="btn-edit"] {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #0066FF, stop:1 #1D4ED8);
    color: #FFFFFF;
    border: none; border-radius: 6px;
    font-size: 11px; font-weight: 600;
    padding: 3px 10px; min-height: 26px;
}}
QPushButton[class="btn-edit"]:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #3B82F6, stop:1 #0066FF);
}}
QPushButton[class="btn-delete"] {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #FF2D78, stop:1 #C0155A);
    color: #FFFFFF;
    border: none; border-radius: 6px;
    font-size: 11px; font-weight: 600;
    padding: 3px 10px; min-height: 26px;
}}
QPushButton[class="btn-delete"]:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #FF5294, stop:1 #FF2D78);
}}
QPushButton[class="btn-add"] {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #00E676, stop:1 #00B248);
    color: #001F0D;
    border: none; border-radius: 10px;
    font-size: 13px; font-weight: 600;
    padding: 8px 20px; min-width: 120px;
}}
QPushButton[class="btn-add"]:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #33FF99, stop:1 #00E676);
}}

/* ── TABLE ───────────────────────────────────────── */
QTableWidget {{
    background: transparent;
    gridline-color: {c['glass_border']};
    border: none;
    color: {c['text_primary']};
    selection-background-color: {c['accent_primary']};
    alternate-background-color: rgba(255,255,255,0.02);
}}
QTableWidget::item {{
    padding: 10px 12px;
    border-bottom: 1px solid {c['glass_border']};
}}
QTableWidget::item:hover {{ background: {c['row_hover']}; }}
QTableWidget::item:selected {{
    background: {c['accent_primary']};
    color: #FFFFFF;
}}
QHeaderView::section {{
    background: {c['table_header']};
    color: {c['accent_secondary']};
    padding: 12px;
    border: none;
    font-weight: bold;
    font-size: 13px;
    border-bottom: 1px solid {c['glass_border']};
}}

/* ── LABELS ──────────────────────────────────────── */
QLabel#heading1 {{
    font-size: 28px; font-weight: bold; color: {c['text_primary']};
}}
QLabel#heading2 {{
    font-size: 20px; font-weight: bold; color: {c['text_primary']};
}}
QLabel#heading3 {{
    font-size: 16px; font-weight: 600; color: {c['text_primary']};
}}
QLabel#labelMuted {{
    font-size: 13px; color: {c['text_muted']};
}}
QLabel#labelAccent {{
    font-size: 14px; color: {c['accent_primary']}; font-weight: 600;
}}
QLabel#labelError {{
    font-size: 12px; color: {c['accent_danger']};
}}

/* ── TABS ────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {c['glass_border']};
    border-radius: 12px;
    background: {c['card_bg']};
    margin-top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {c['text_secondary']};
    padding: 10px 20px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 14px;
    margin-right: 4px;
}}
QTabBar::tab:selected {{
    color: {c['accent_primary']};
    border-bottom: 2px solid {c['accent_primary']};
    font-weight: bold;
}}
QTabBar::tab:hover {{
    color: {c['text_primary']};
    background: {c['hover_bg']};
    border-radius: 8px 8px 0 0;
}}

/* ── PROGRESS BAR ─────────────────────────────────── */
QProgressBar {{
    background: {c['glass_border']};
    border-radius: 6px;
    text-align: center;
    color: {c['text_primary']};
    height: 12px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']});
    border-radius: 6px;
}}

/* ── GROUPBOX ─────────────────────────────────────── */
QGroupBox {{
    border: 1px solid {c['glass_border']};
    border-radius: 12px;
    margin-top: 16px;
    padding-top: 12px;
    color: {c['text_primary']};
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {c['accent_primary']};
    font-size: 14px;
}}

/* ── CHECKBOX / RADIO ─────────────────────────────── */
QCheckBox, QRadioButton {{
    color: {c['text_primary']};
    spacing: 8px;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px; height: 18px;
    border: 2px solid {c['glass_border']};
    background: {c['input_bg']};
}}
QCheckBox::indicator {{
    border-radius: 4px;
}}
QRadioButton::indicator {{
    border-radius: 9px;
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: {c['accent_primary']};
    border-color: {c['accent_primary']};
}}

/* ── SPLITTER ─────────────────────────────────────── */
QSplitter::handle {{
    background: {c['glass_border']};
    width: 2px; height: 2px;
}}

/* ── TOOLTIP ─────────────────────────────────────── */
QToolTip {{
    background: {c['bg_secondary']};
    color: {c['text_primary']};
    border: 1px solid {c['accent_primary']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ── MESSAGE BOX ─────────────────────────────────── */
QMessageBox {{
    background: {c['bg_secondary']};
    color: {c['text_primary']};
}}
QMessageBox QLabel {{ color: {c['text_primary']}; }}

/* ── STATUS BAR ──────────────────────────────────── */
QStatusBar {{
    background: {c['sidebar_bg']};
    color: {c['text_secondary']};
    font-size: 12px;
}}
"""


# ─── Theme Manager Class ──────────────────────────────────────────────────────
class ThemeManager:
    _current_theme: str = "dark"

    @classmethod
    def apply_theme(cls, theme: str = "dark"):
        cls._current_theme = theme
        colors = DARK_COLORS if theme == "dark" else LIGHT_COLORS
        app = QApplication.instance()
        if app:
            app.setStyleSheet(_make_stylesheet(colors))
        logger.info(f"Theme applied: {theme}")

    @classmethod
    def toggle_theme(cls) -> str:
        new_theme = "light" if cls._current_theme == "dark" else "dark"
        cls.apply_theme(new_theme)
        return new_theme

    @classmethod
    def current_theme(cls) -> str:
        return cls._current_theme

    @classmethod
    def get_colors(cls) -> dict:
        return DARK_COLORS if cls._current_theme == "dark" else LIGHT_COLORS

    @classmethod
    def color(cls, key: str) -> str:
        return cls.get_colors().get(key, "#FFFFFF")
