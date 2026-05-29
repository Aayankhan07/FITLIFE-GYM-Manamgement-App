"""
FitLife — Member Profile View
Tabbed profile: Info / Attendance / Payments / Workout / Diet / Progress
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ui.components.glass_card import GlassCard, KPICard, StatusBadge
from ui.components.confirm_dialog import ConfirmDialog, InfoDialog
import services.member_service as member_svc
import services.membership_service as membership_svc


class MemberProfile(QWidget):
    """Full member profile with tabs."""

    go_back  = pyqtSignal()
    go_edit  = pyqtSignal(int)  # member_id
    assigned_plan = pyqtSignal()

    def __init__(self, session, member_id: int, parent=None):
        super().__init__(parent)
        self._session = session
        self._member_id = member_id
        self._member = None
        self.setStyleSheet("background: transparent;")
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")

        container = QWidget()
        container.setStyleSheet("background:transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(28, 24, 28, 28)
        main.setSpacing(20)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        back_btn = QPushButton("← Back to Members")
        back_btn.setObjectName("btnSecondary")
        back_btn.setFixedHeight(36)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.go_back.emit)
        hdr.addWidget(back_btn)
        hdr.addStretch()

        self.edit_btn = QPushButton("✏️  Edit Member")
        self.edit_btn.setObjectName("btnPrimary")
        self.edit_btn.setFixedHeight(36)
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.clicked.connect(lambda: self.go_edit.emit(self._member_id))
        hdr.addWidget(self.edit_btn)
        main.addLayout(hdr)

        # ── Member Header Card ────────────────────────────────────────────────
        self.header_card = QFrame()
        self.header_card.setObjectName("glassCard")
        self.header_card.setStyleSheet("""
            QFrame#glassCard {
                background: rgba(124,58,237,0.1);
                border: 1px solid rgba(124,58,237,0.4);
                border-radius: 16px;
            }
        """)
        hc_layout = QHBoxLayout(self.header_card)
        hc_layout.setContentsMargins(24, 20, 24, 20)
        hc_layout.setSpacing(24)

        # Avatar
        self.avatar_lbl = QLabel("👤")
        self.avatar_lbl.setStyleSheet("font-size:64px;")
        self.avatar_lbl.setFixedWidth(80)
        hc_layout.addWidget(self.avatar_lbl)

        # Name/role block
        info_col = QVBoxLayout()
        info_col.setSpacing(4)
        self.name_lbl = QLabel("Loading...")
        self.name_lbl.setStyleSheet("font-size:22px; font-weight:900; color:#F0F4FF;")
        self.sub_lbl  = QLabel("")
        self.sub_lbl.setStyleSheet("font-size:14px; color:#9CA3AF;")
        self.status_badge = StatusBadge("Active")
        info_col.addWidget(self.name_lbl)
        info_col.addWidget(self.sub_lbl)
        info_col.addWidget(self.status_badge)
        hc_layout.addLayout(info_col)
        hc_layout.addStretch()

        # KPIs on the right
        kpi_row = QHBoxLayout()
        self.kpi_bmi    = KPICard("BMI",     "—", "⚖️",  "", "#00F5FF")
        self.kpi_expiry = KPICard("Expires", "—", "📅",  "", "#FFB800")
        self.kpi_plan   = KPICard("Plan",    "—", "💳",  "", "#7C3AED")
        for k in [self.kpi_bmi, self.kpi_expiry, self.kpi_plan]:
            k.setFixedWidth(160)
            kpi_row.addWidget(k)
        hc_layout.addLayout(kpi_row)
        main.addWidget(self.header_card)

        # ── Tabs ──────────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(124,58,237,0.2);
                border-radius: 12px;
            }
            QTabBar::tab {
                background:transparent; color:#9CA3AF;
                padding:10px 20px; border:none;
                border-bottom:2px solid transparent;
            }
            QTabBar::tab:selected { color:#7C3AED; border-bottom:2px solid #7C3AED; font-weight:bold; }
            QTabBar::tab:hover    { color:#F0F4FF; background:rgba(124,58,237,0.1); border-radius:8px 8px 0 0; }
        """)

        self.tabs.addTab(self._build_info_tab(),       "📋 Info")
        self.tabs.addTab(self._build_attendance_tab(), "📅 Attendance")
        self.tabs.addTab(self._build_payments_tab(),   "💰 Payments")
        self.tabs.addTab(self._build_membership_tab(), "💳 Membership")
        main.addWidget(self.tabs)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _build_info_tab(self):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        grid = QGridLayout(w)
        grid.setContentsMargins(24, 20, 24, 20)
        grid.setSpacing(12)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        def field_row(label, attr_name, row, col=0):
            lbl = QLabel(label)
            lbl.setStyleSheet("color:#6B7280; font-size:13px;")
            val = QLabel("—")
            val.setStyleSheet("color:#F0F4FF; font-size:14px;")
            val.setObjectName(attr_name)
            grid.addWidget(lbl, row, col)
            grid.addWidget(val, row, col + 1)
            return val

        self.fi_phone    = field_row("Phone",            "fi_phone",    0)
        self.fi_email    = field_row("Email",            "fi_email",    0, 2)
        self.fi_cnic     = field_row("CNIC",             "fi_cnic",     1)
        self.fi_dob      = field_row("Date of Birth",    "fi_dob",      1, 2)
        self.fi_addr     = field_row("Address",          "fi_addr",     2)
        self.fi_emerg    = field_row("Emergency Contact","fi_emerg",    2, 2)
        self.fi_goal     = field_row("Fitness Goal",     "fi_goal",     3)
        self.fi_branch   = field_row("Branch",           "fi_branch",   3, 2)
        self.fi_trainer  = field_row("Trainer",          "fi_trainer",  4)
        self.fi_join     = field_row("Join Date",        "fi_join",     4, 2)
        self.fi_weight   = field_row("Weight",           "fi_weight",   5)
        self.fi_height   = field_row("Height",           "fi_height",   5, 2)
        self.fi_health   = field_row("Health Conditions","fi_health",   6)
        return w

    def _build_attendance_tab(self):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        self.attend_table = self._make_table(["Date", "Check In", "Check Out", "Status", "Notes"])
        lay.addWidget(self.attend_table)
        return w

    def _build_payments_tab(self):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        self.pay_table = self._make_table(["Date", "Amount", "Method", "Status", "Invoice #", "Notes"])
        lay.addWidget(self.pay_table)
        return w

    def _build_membership_tab(self):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)

        self.mem_hist_table = self._make_table(["Plan", "Price", "Start Date", "End Date", "Status"])
        lay.addWidget(QLabel("Membership History"))
        lay.addWidget(self.mem_hist_table)
        return w

    def _make_table(self, cols: list) -> QTableWidget:
        t = QTableWidget()
        t.setColumnCount(len(cols))
        t.setHorizontalHeaderLabels(cols)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.verticalHeader().setVisible(False)
        t.horizontalHeader().setStretchLastSection(True)
        t.setStyleSheet("""
            QTableWidget { background:transparent; border:none; color:#F0F4FF; }
            QTableWidget::item { padding:8px; border-bottom:1px solid rgba(124,58,237,0.15); }
            QHeaderView::section { background:rgba(124,58,237,0.2); color:#00F5FF;
                padding:10px; border:none; font-weight:bold; }
        """)
        return t

    # ── Data Loading ──────────────────────────────────────────────────────────
    def _load_data(self):
        m = member_svc.get_member_by_id(self._member_id)
        if not m:
            return
        self._member = m

        # Header card
        self.name_lbl.setText(m[1])
        self.sub_lbl.setText(f"Branch: {m[23] or '—'}  |  Trainer: {m[24] or '—'}")
        self.status_badge.set_status(m[16])

        bmi_val = f"{m[13]}" if m[13] else "—"
        self.kpi_bmi.set_value(bmi_val)
        self.kpi_expiry.set_value(str(m[15]) if m[15] else "—")
        self.kpi_plan.set_value(m[25] or "—")

        # Info tab
        self.fi_phone.setText(m[4] or "—")
        self.fi_email.setText(m[5] or "—")
        self.fi_cnic.setText(m[2] or "—")
        self.fi_dob.setText(str(m[3]) if m[3] else "—")
        self.fi_addr.setText(m[7] or "—")
        self.fi_emerg.setText(m[6] or "—")
        self.fi_goal.setText(m[9] or "—")
        self.fi_branch.setText(m[23] or "—")
        self.fi_trainer.setText(m[24] or "—")
        self.fi_join.setText(str(m[14]) if m[14] else "—")
        self.fi_weight.setText(f"{m[11]} kg" if m[11] else "—")
        self.fi_height.setText(f"{m[12]} cm" if m[12] else "—")
        self.fi_health.setText(m[10] or "—")

        # Attendance
        attend = member_svc.get_member_attendance_history(self._member_id)
        self.attend_table.setRowCount(0)
        for row in attend:
            r = self.attend_table.rowCount()
            self.attend_table.insertRow(r)
            self.attend_table.setItem(r, 0, QTableWidgetItem(str(row[0])))
            self.attend_table.setItem(r, 1, QTableWidgetItem(str(row[1]) if row[1] else "—"))
            self.attend_table.setItem(r, 2, QTableWidgetItem(str(row[2]) if row[2] else "—"))
            badge = StatusBadge(row[3])
            self.attend_table.setCellWidget(r, 3, badge)
            self.attend_table.setItem(r, 4, QTableWidgetItem(row[4] or ""))

        # Payments
        pays = member_svc.get_member_payment_history(self._member_id)
        self.pay_table.setRowCount(0)
        for row in pays:
            r = self.pay_table.rowCount()
            self.pay_table.insertRow(r)
            self.pay_table.setItem(r, 0, QTableWidgetItem(str(row[0])))
            self.pay_table.setItem(r, 1, QTableWidgetItem(f"Rs. {row[1]:,.0f}"))
            self.pay_table.setItem(r, 2, QTableWidgetItem(row[2]))
            badge = StatusBadge(row[3])
            self.pay_table.setCellWidget(r, 3, badge)
            self.pay_table.setItem(r, 4, QTableWidgetItem(row[4] or ""))
            self.pay_table.setItem(r, 5, QTableWidgetItem(row[5] or ""))

        # Membership history
        mem_hist = membership_svc.get_membership_history(self._member_id)
        self.mem_hist_table.setRowCount(0)
        for row in mem_hist:
            r = self.mem_hist_table.rowCount()
            self.mem_hist_table.insertRow(r)
            self.mem_hist_table.setItem(r, 0, QTableWidgetItem(row[1]))
            self.mem_hist_table.setItem(r, 1, QTableWidgetItem(f"Rs. {row[2]:,.0f}"))
            self.mem_hist_table.setItem(r, 2, QTableWidgetItem(str(row[3])))
            self.mem_hist_table.setItem(r, 3, QTableWidgetItem(str(row[4])))
            badge = StatusBadge(row[5])
            self.mem_hist_table.setCellWidget(r, 4, badge)
