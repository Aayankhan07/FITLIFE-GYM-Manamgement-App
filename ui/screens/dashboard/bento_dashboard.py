"""
FitLife — Bento Dashboard Screen (Matching GYM-MANAGEMENT)
3-Zone Bento Grid Layout:
- Zone 1: Horizontal KPI Metric Strip (6 inline stat cards with direction chips)
- Zone 2: Performance Trends Bezier Curve Chart + Operations Table with Expandable Drawer
- Zone 3: Live Gym Floor Traffic Analog Meter & Hourly Forecast + Featured Workout Programs
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QGridLayout, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from ui.theme.theme_manager import ThemeManager
from ui.components.icons import get_icon
from ui.screens.dashboard.performance_chart import PerformanceChartWidget
from ui.screens.dashboard.floor_traffic_widget import FloorTrafficWidget
from ui.screens.dashboard.operations_table import OperationsTableWidget
from ui.screens.dashboard.fast_checkin_dialog import FastCheckInDialog

import services.analytics_service as analytics_svc
import services.member_service as member_svc
import services.attendance_service as att_svc


class KPIMetricItem(QFrame):
    """High-density metric column item with title, count, and delta pill."""
    def __init__(self, title: str, value: str, delta: str, has_divider: bool = True, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(4)

        t_lbl = QLabel(title.upper())
        t_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #8C93A3; letter-spacing: 0.5px;")
        layout.addWidget(t_lbl)

        val_box = QHBoxLayout()
        val_box.setSpacing(6)
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet("font-size: 18px; font-weight: 800; font-family: monospace;")
        val_box.addWidget(v_lbl)

        if delta:
            d_lbl = QLabel(f" {delta} ")
            d_lbl.setStyleSheet("""
                font-size: 10px; font-weight: 800;
                color: #10B981; background-color: rgba(16, 185, 129, 0.12);
                border-radius: 4px; padding: 1px 4px;
            """)
            val_box.addWidget(d_lbl)

        val_box.addStretch()
        layout.addLayout(val_box)

        if has_divider:
            self.setStyleSheet("border-right: 1px solid rgba(140, 147, 163, 0.15);")


class KPIMetricsStrip(QFrame):
    """Horizontal 6-metric strip matching GYM-MANAGEMENT."""
    def __init__(self, stats: dict, active_checkins: int, parent=None):
        super().__init__(parent)
        self.setObjectName("kpiStripCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)

        total_members = stats.get("total_members", 1284)
        profit = stats.get("monthly_profit", 38500)
        active_trainers = stats.get("active_trainers", 8)

        layout.addWidget(KPIMetricItem("Active Members", str(total_members), "+5.2%"))
        layout.addWidget(KPIMetricItem("Live Floor", str(active_checkins), "+15%"))
        layout.addWidget(KPIMetricItem("Gross Rev", f"${profit/1000:,.1f}k", "+9.4%"))
        layout.addWidget(KPIMetricItem("Renewal Rate", "94.2%", "+3.1%"))
        layout.addWidget(KPIMetricItem("Coaches On Duty", f"{active_trainers} Active", "+2"))
        layout.addWidget(KPIMetricItem("Equipment Health", "98% Stable", "+1.2%", has_divider=False))

        self.update_styles()

    def update_styles(self):
        is_dark = ThemeManager.current_theme() == "dark"
        card_bg = "#141518" if is_dark else "#FFFFFF"
        border_color = "#24272D" if is_dark else "#E6E9EE"
        self.setStyleSheet(f"""
            QFrame#kpiStripCard {{
                background-color: {card_bg};
                border: 1px solid {border_color};
                border-radius: 16px;
            }}
        """)


class FeaturedProgramsCard(QFrame):
    """Featured workout programs card in right bento column."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("programsCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        hdr = QHBoxLayout()
        t = QLabel("FEATURED WORKOUT PROGRAMS")
        t.setStyleSheet("font-size: 11px; font-weight: 800; color: #8C93A3; letter-spacing: 0.5px;")
        sub = QLabel("4 Active Tracks")
        sub.setStyleSheet("font-size: 10px; font-weight: 800; color: #FA5A3C;")
        hdr.addWidget(t)
        hdr.addStretch()
        hdr.addWidget(sub)
        layout.addLayout(hdr)

        grid = QGridLayout()
        grid.setSpacing(8)

        programs = [
            ("Hypertrophy Split", "SPLIT A", "#FA5A3C"),
            ("Core & Mobility", "CLASS B", "#3B82F6"),
            ("Cardio Engine", "ZONE C", "#10B981"),
            ("Powerlifting", "LIFT D", "#8B5CF6"),
        ]
        self.boxes = []
        for idx, (p_title, tag, col) in enumerate(programs):
            box = QFrame()
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(12, 10, 12, 10)
            box_layout.setSpacing(4)

            tag_lbl = QLabel(tag)
            tag_lbl.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {col}; background: transparent; border: none;")
            title_lbl = QLabel(p_title)
            title_lbl.setObjectName("programTitleLbl")
            title_lbl.setStyleSheet("font-size: 13px; font-weight: 700; background: transparent; border: none;")
            box_layout.addWidget(tag_lbl)
            box_layout.addWidget(title_lbl)

            self.boxes.append(box)
            grid.addWidget(box, idx // 2, idx % 2)

        layout.addLayout(grid)
        self.update_styles()

    def update_styles(self):
        is_dark = ThemeManager.current_theme() == "dark"
        card_bg = "#141518" if is_dark else "#FFFFFF"
        card_border = "#24272D" if is_dark else "#E6E9EE"
        item_bg = "#181A1F" if is_dark else "#F8F9FB"
        item_border = "#24272D" if is_dark else "#E6E9EE"
        text_color = "#F4F5F8" if is_dark else "#18181B"

        self.setStyleSheet(f"""
            QFrame#programsCard {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 16px;
            }}
        """)

        for box in getattr(self, "boxes", []):
            box.setStyleSheet(f"""
                QFrame {{
                    background-color: {item_bg};
                    border: 1px solid {item_border};
                    border-radius: 10px;
                }}
                QLabel#programTitleLbl {{
                    color: {text_color};
                }}
            """)


class BentoDashboardScreen(QWidget):
    """
    Modern Bento Dashboard screen implementing GYM-MANAGEMENT layout completely.
    """
    nav_requested = pyqtSignal(str)

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.branch_id = getattr(session, 'branch_id', 1) or 1
        self.setStyleSheet("background: transparent;")
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 20, 28, 28)
        root.setSpacing(20)

        # ── 1. Fetch live metrics ──────────────────────────────────────────────
        stats = {}
        active_checkins_count = 0
        try:
            stats = analytics_svc.get_dashboard_kpis(self.branch_id) or {}
            active_list = att_svc.get_active_checkins(self.branch_id) or []
            active_checkins_count = len(active_list)
        except Exception:
            pass

        # ── 2. Zone 1: Horizontal KPI Strip ───────────────────────────────────
        self.kpi_strip = KPIMetricsStrip(stats, active_checkins_count)
        root.addWidget(self.kpi_strip)

        # ── 3. 2-Column Bento Grid ────────────────────────────────────────────
        bento_row = QHBoxLayout()
        bento_row.setSpacing(20)

        # Left Column: Performance Chart + Operations Table (65% width)
        left_col = QVBoxLayout()
        left_col.setSpacing(20)

        self.chart_card = PerformanceChartWidget()
        left_col.addWidget(self.chart_card)

        self.table_card = OperationsTableWidget(branch_id=self.branch_id)
        self.table_card.fast_checkin_requested.connect(self._open_fast_checkin)
        left_col.addWidget(self.table_card)

        bento_row.addLayout(left_col, 65)

        # Right Column: Live Gym Floor Traffic + Featured Programs (35% width)
        right_col = QVBoxLayout()
        right_col.setSpacing(20)

        self.traffic_widget = FloorTrafficWidget()
        self.traffic_widget.set_live_traffic(active_checkins_count, max_capacity=30)
        right_col.addWidget(self.traffic_widget)

        self.programs_widget = FeaturedProgramsCard()
        right_col.addWidget(self.programs_widget)

        right_col.addStretch()
        bento_row.addLayout(right_col, 35)

        root.addLayout(bento_row)

        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def _open_fast_checkin(self):
        dlg = FastCheckInDialog(branch_id=self.branch_id, parent=self)
        dlg.checkin_changed.connect(self._on_checkin_updated)
        dlg.exec()

    def _on_checkin_updated(self):
        try:
            active_list = att_svc.get_active_checkins(self.branch_id) or []
            self.traffic_widget.set_live_traffic(len(active_list), max_capacity=30)
            self.table_card.refresh_table()
        except Exception:
            pass

    def refresh_theme(self):
        self.kpi_strip.update_styles()
        self.chart_card.update_styles()
        self.table_card.update_styles()
        self.traffic_widget.update_styles()
        self.programs_widget.update_styles()
