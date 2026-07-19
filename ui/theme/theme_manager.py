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
    "bg_primary":            "#0B0F19",
    "bg_secondary":          "#152033",
    "bg_tertiary":           "#1E293B",
    "accent_primary":        "#3B82F6",
    "accent_primary_hover":  "#60A5FA",
    "accent_secondary":      "#06B6D4",
    "accent_secondary_hover": "#22D3EE",
    "accent_danger":         "#F43F5E",
    "accent_danger_hover":   "#FB7185",
    "accent_warning":        "#F59E0B",
    "accent_warning_hover":  "#FBBF24",
    "accent_success":        "#10B981",
    "accent_success_hover":  "#34D399",
    "text_primary":          "#F8FAFC",
    "text_secondary":        "#94A3B8",
    "text_muted":            "#64748B",
    "glass_bg":              "rgba(21, 32, 51, 0.75)",
    "glass_border":          "rgba(59, 130, 246, 0.2)",
    "card_bg":               "rgba(21, 32, 51, 0.65)",
    "input_bg":              "rgba(15, 23, 42, 0.6)",
    "hover_bg":              "rgba(59, 130, 246, 0.12)",
    "sidebar_bg":            "#0D1527",
    "row_hover":             "rgba(59, 130, 246, 0.08)",
    "table_header":          "rgba(59, 130, 246, 0.15)",
}

LIGHT_COLORS = {
    "bg_primary":            "#F8FAFC",
    "bg_secondary":          "#FFFFFF",
    "bg_tertiary":           "#F1F5F9",
    "accent_primary":        "#2563EB",
    "accent_primary_hover":  "#1D4ED8",
    "accent_secondary":      "#0891B2",
    "accent_secondary_hover": "#0E7490",
    "accent_danger":         "#DC2626",
    "accent_danger_hover":   "#B91C4C",
    "accent_warning":        "#D97706",
    "accent_warning_hover":  "#B45309",
    "accent_success":        "#16A34A",
    "accent_success_hover":  "#15803D",
    "text_primary":          "#0F172A",
    "text_secondary":        "#475569",
    "text_muted":            "#94A3B8",
    "glass_bg":              "rgba(255, 255, 255, 0.85)",
    "glass_border":          "rgba(37, 99, 235, 0.15)",
    "card_bg":               "#FFFFFF",
    "input_bg":              "#FFFFFF",
    "hover_bg":              "rgba(37, 99, 235, 0.08)",
    "sidebar_bg":            "#FFFFFF",
    "row_hover":             "rgba(37, 99, 235, 0.04)",
    "table_header":          "rgba(37, 99, 235, 0.08)",
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
    background: transparent; width: 6px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {c['accent_primary']}; border-radius: 3px; min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent; height: 6px; margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {c['accent_primary']}; border-radius: 3px; min-width: 30px;
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
    border-left: 4px solid transparent;
    border-radius: 10px;
    color: {c['text_secondary']};
    text-align: left;
    padding: 10px 16px;
    font-size: 14px;
    margin: 2px 8px;
}}
QPushButton#sidebarBtn:hover {{
    background: {c['hover_bg']};
    color: {c['text_primary']};
}}
QPushButton#sidebarBtn[active="true"] {{
    background: {c['hover_bg']};
    color: {c['accent_primary']};
    border-left: 4px solid {c['accent_primary']};
    font-weight: bold;
}}
QPushButton#sidebarBtn[collapsed="true"] {{
    text-align: center;
    padding: 10px 0px;
    border-radius: 10px;
    border-left: none;
    margin: 4px;
}}
QPushButton#sidebarBtn[collapsed="true"]:hover {{
    border-left: none;
}}
QPushButton#sidebarBtn[collapsed="true"][active="true"] {{
    border-left: none;
    background: {c['hover_bg']};
}}

/* Logo Text inside Sidebar */
QLabel#sidebarLogoText {{
    font-size: 22px;
    font-weight: bold;
    color: {c['accent_primary']};
    letter-spacing: 1px;
}}

/* User Info Frame inside Sidebar */
QFrame#userFrame {{
    background: {c['hover_bg']};
    border: 1px solid {c['glass_border']};
    border-radius: 12px;
}}
QLabel#userNameLbl {{
    font-weight: bold;
    font-size: 13px;
    color: {c['text_primary']};
}}
QLabel#userRoleLbl {{
    font-size: 11px;
    color: {c['accent_primary']};
    font-weight: 600;
}}

/* ── TOPBAR ──────────────────────────────────────── */
QWidget#topbar {{
    background: {c['glass_bg']};
    border-bottom: 1px solid {c['glass_border']};
}}
QLabel#topbarPageTitle {{
    font-size: 20px;
    font-weight: 800;
    color: {c['text_primary']};
    letter-spacing: 0.5px;
}}
QLineEdit#topbarSearch {{
    background: {c['input_bg']};
    border: 1px solid {c['glass_border']};
    border-radius: 18px;
    padding: 0 16px;
    color: {c['text_primary']};
    font-size: 14px;
}}
QLineEdit#topbarSearch:focus {{
    border: 1.5px solid {c['accent_primary']};
}}
QLabel#topbarUserLbl {{
    color: {c['text_primary']};
    font-size: 14px;
    font-weight: 600;
}}
QLabel#topbarRoleLbl {{
    color: {c['accent_primary']};
    font-size: 12px;
    font-weight: 600;
}}

/* ── KPI CARD ────────────────────────────────────── */
QFrame#kpiCard {{
    background-color: {c['card_bg']};
    border: 1px solid {c['glass_border']};
    border-radius: 16px;
}}

QFrame#kpiCard[accent="primary"] {{ border-top: 3px solid {c['accent_primary']}; }}
QFrame#kpiCard[accent="secondary"] {{ border-top: 3px solid {c['accent_secondary']}; }}
QFrame#kpiCard[accent="success"] {{ border-top: 3px solid {c['accent_success']}; }}
QFrame#kpiCard[accent="warning"] {{ border-top: 3px solid {c['accent_warning']}; }}
QFrame#kpiCard[accent="danger"] {{ border-top: 3px solid {c['accent_danger']}; }}

/* KPI Icon Badge */
QLabel#kpiIconBadge {{
    font-size: 16px;
    border-radius: 18px;
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
}}

QFrame#kpiCard[accent="primary"] QLabel#kpiIconBadge {{
    background-color: rgba(59, 130, 246, 0.15);
}}
QFrame#kpiCard[accent="secondary"] QLabel#kpiIconBadge {{
    background-color: rgba(6, 182, 212, 0.15);
}}
QFrame#kpiCard[accent="success"] QLabel#kpiIconBadge {{
    background-color: rgba(16, 185, 129, 0.15);
}}
QFrame#kpiCard[accent="warning"] QLabel#kpiIconBadge {{
    background-color: rgba(245, 158, 11, 0.15);
}}
QFrame#kpiCard[accent="danger"] QLabel#kpiIconBadge {{
    background-color: rgba(244, 63, 94, 0.15);
}}

/* KPI Value Text */
QLabel#kpiValue {{
    font-size: 24px;
    font-weight: 800;
    color: {c['text_primary']};
}}

/* KPI Title Text */
QLabel#kpiTitle {{
    font-size: 13px;
    color: {c['text_secondary']};
    font-weight: 500;
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
    color: #FFFFFF;
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
QPushButton {{
    color: {c['text_primary']};
    font-size: 13px;
    font-weight: 600;
    border: 1px solid {c['glass_border']};
    border-radius: 8px;
    padding: 6px 14px;
    min-height: 26px;
    background: rgba(255,255,255,0.04);
}}
QPushButton:hover {{
    background: {c['hover_bg']};
    color: {c['text_primary']};
}}
QPushButton:disabled {{
    color: {c['text_muted']};
    background: rgba(255,255,255,0.01);
}}

QPushButton#btnPrimary {{
    background: {c['accent_primary']};
    border: none;
    border-radius: 10px;
    color: #FFFFFF;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton#btnPrimary:hover {{
    background: {c['accent_primary_hover']};
}}
QPushButton#btnPrimary:pressed {{ padding: 11px 23px 9px 25px; }}
QPushButton#btnPrimary:disabled {{
    background: {c['text_muted']}; color: {c['text_secondary']};
}}

QPushButton#btnSecondary {{
    background: {c['hover_bg']};
    border: 1px solid {c['glass_border']};
    border-radius: 12px;
    color: {c['accent_primary']};
    padding: 10px 24px;
    font-size: 14px;
    font-weight: 600;
}}
QPushButton#btnSecondary:hover {{
    background: {c['accent_primary']};
    color: #FFFFFF;
    border-color: {c['accent_primary']};
}}

QPushButton#btnDanger {{
    background: {c['accent_danger']};
    border: none;
    border-radius: 10px;
    color: #FFFFFF;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton#btnDanger:hover {{
    background: {c['accent_danger_hover']};
}}

QPushButton#btnSuccess {{
    background: {c['accent_success']};
    border: none;
    border-radius: 10px;
    color: #FFFFFF;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton#btnSuccess:hover {{
    background: {c['accent_success_hover']};
}}

QPushButton#btnWarning {{
    background: {c['accent_warning']};
    border: none;
    border-radius: 10px;
    color: #FFFFFF;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton#btnWarning:hover {{
    background: {c['accent_warning_hover']};
}}

QPushButton#btnIcon {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 18px;
    padding: 6px;
    color: {c['text_secondary']};
}}
QPushButton#btnIcon:hover {{
    background: {c['hover_bg']};
    border: 1px solid {c['glass_border']};
    color: {c['accent_primary']};
}}

/* Info Banner Frame */
QFrame#infoBanner {{
    background: rgba(6, 182, 212, 0.08);
    border: 1px solid rgba(6, 182, 212, 0.25);
    border-radius: 12px;
}}
QLabel#infoBannerText {{
    color: {c['accent_secondary']};
    font-size: 13px;
    font-weight: 500;
}}

/* ── ACTION BUTTONS (table rows) ──────────────────── */
QPushButton[class="btn-view"] {{
    background: {c['accent_secondary']};
    color: #FFFFFF;
    border: none; border-radius: 6px;
    font-size: 11px; font-weight: 600;
    padding: 3px 10px; min-height: 26px;
}}
QPushButton[class="btn-view"]:hover {{
    background: {c['accent_secondary_hover']};
}}
QPushButton[class="btn-edit"] {{
    background: {c['accent_primary']};
    color: #FFFFFF;
    border: none; border-radius: 6px;
    font-size: 11px; font-weight: 600;
    padding: 3px 10px; min-height: 26px;
}}
QPushButton[class="btn-edit"]:hover {{
    background: {c['accent_primary_hover']};
}}
QPushButton[class="btn-delete"] {{
    background: {c['accent_danger']};
    color: #FFFFFF;
    border: none; border-radius: 6px;
    font-size: 11px; font-weight: 600;
    padding: 3px 10px; min-height: 26px;
}}
QPushButton[class="btn-delete"]:hover {{
    background: {c['accent_danger_hover']};
}}
QPushButton[class="btn-add"] {{
    background: {c['accent_success']};
    color: #FFFFFF;
    border: none; border-radius: 10px;
    font-size: 13px; font-weight: 600;
    padding: 8px 20px; min-width: 120px;
}}
QPushButton[class="btn-add"]:hover {{
    background: {c['accent_success_hover']};
}}

/* ── TABLE ───────────────────────────────────────── */
QTableWidget {{
    background: transparent;
    gridline-color: {c['glass_border']};
    border: none;
    color: {c['text_primary']};
    selection-background-color: {c['accent_primary']};
    alternate-background-color: rgba(255,255,255,0.01);
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
    color: {c['accent_primary']};
    padding: 12px;
    border: none;
    font-weight: bold;
    font-size: 13px;
    border-bottom: 1px solid {c['glass_border']};
}}

/* ── LABELS ──────────────────────────────────────── */
QLabel#heading1 {{
    font-size: 32px; font-weight: 900; color: {c['text_primary']};
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
        colors_dict = DARK_COLORS if theme == "dark" else LIGHT_COLORS
        app = QApplication.instance()
        if app:
            app.setStyleSheet(_make_stylesheet(colors_dict))
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
    def colors(cls) -> dict:
        """Alias for get_colors to prevent crashes in dialogs."""
        return cls.get_colors()

    @classmethod
    def color(cls, key: str) -> str:
        return cls.get_colors().get(key, "#FFFFFF")
