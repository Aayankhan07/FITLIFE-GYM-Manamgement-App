"""
FitLife — Members Screen
Full CRUD list view with search, filter, add/edit/delete, profile view.
Role-aware: Admin sees all branches, Manager sees their branch only.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QScrollArea, QComboBox, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ui.components.glass_card import GlassCard, KPICard, SectionHeader, StatusBadge
from ui.components.data_table import DataTable
from ui.components.confirm_dialog import ConfirmDialog, InfoDialog
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
import services.member_service as member_svc
import services.branch_service as branch_svc
from config.constants import (
    MEMBER_STATUSES, ROLE_ADMIN, ROLE_MANAGER
)


class MembersScreen(QWidget):
    """Main Members list screen with KPIs, filters, and action buttons."""

    open_add_form   = pyqtSignal()
    open_edit_form  = pyqtSignal(int)   # member_id
    open_profile    = pyqtSignal(int)   # member_id

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self._branch_id = session.branch_id if session.role == ROLE_MANAGER else None
        self._members_data = []
        self.setStyleSheet("background: transparent;")
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QWidget { border:none; background:transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self._main_layout = QVBoxLayout(container)
        self._main_layout.setContentsMargins(28, 12, 28, 20)
        self._main_layout.setSpacing(14)

        # ── Header row ────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("👥  Members Management")
        title.setStyleSheet("QWidget { font-size:26px; font-weight:900; color:#F0F4FF; }")
        hdr.addWidget(title)
        hdr.addStretch()

        self.add_btn = QPushButton("➕  Add Member")
        self.add_btn.setObjectName("btnPrimary")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self.open_add_form.emit)
        hdr.addWidget(self.add_btn)
        self._main_layout.addLayout(hdr)

        # ── KPI row ───────────────────────────────────────────────────────────
        self._kpi_row = QHBoxLayout()
        self._kpi_row.setSpacing(14)
        self._kpi_total    = KPICard("Total Members",    "—", "👥", "", "#0066FF")
        self._kpi_active   = KPICard("Active",           "—", "✅", "", "#00E676")
        self._kpi_expired  = KPICard("Expired",          "—", "⚠️","", "#FFB800")
        self._kpi_inactive = KPICard("Inactive/Suspend", "—", "❌","", "#FF2D78")
        for card in [self._kpi_total, self._kpi_active, self._kpi_expired, self._kpi_inactive]:
            self._kpi_row.addWidget(card)
        self._main_layout.addLayout(self._kpi_row)

        # ── Filter bar ────────────────────────────────────────────────────────
        filter_frame = QFrame()
        filter_frame.setObjectName("glassCard")
        filter_frame.setStyleSheet("""
            QFrame#glassCard {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(0, 102, 255, 0.25);
                border-radius: 12px;
            }
        """)
        filter_row = QHBoxLayout(filter_frame)
        filter_row.setContentsMargins(16, 12, 16, 12)
        filter_row.setSpacing(12)

        status_lbl = QLabel("Status:")
        status_lbl.setStyleSheet("QWidget { color:#9CA3AF; font-size:13px; }")
        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses", None)
        for s in MEMBER_STATUSES:
            self.status_filter.addItem(s, s)
        self.status_filter.setFixedHeight(36)
        self.status_filter.currentIndexChanged.connect(self._apply_filters)

        filter_row.addWidget(status_lbl)
        filter_row.addWidget(self.status_filter)

        # Branch filter (admin only)
        if self._session.role == ROLE_ADMIN:
            branch_lbl = QLabel("Branch:")
            branch_lbl.setStyleSheet("QWidget { color:#9CA3AF; font-size:13px; }")
            self.branch_filter = QComboBox()
            self.branch_filter.addItem("All Branches", None)
            branches = branch_svc.get_all_branches_dropdown()
            for bid, bname in branches:
                self.branch_filter.addItem(bname, bid)
            self.branch_filter.setFixedHeight(36)
            self.branch_filter.currentIndexChanged.connect(self._apply_filters)
            filter_row.addWidget(branch_lbl)
            filter_row.addWidget(self.branch_filter)

        filter_row.addStretch()

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setObjectName("btnSecondary")
        refresh_btn.setFixedHeight(36)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._load_data)
        filter_row.addWidget(refresh_btn)
        self._main_layout.addWidget(filter_frame)

        # ── Data Table ────────────────────────────────────────────────────────
        cols = ["ID", "Full Name", "CNIC", "Phone", "Branch",
                "Trainer", "Plan", "Expiry", "Status", "Actions"]
        self.table = DataTable(cols)
        self.table.row_double_clicked.connect(self._on_row_double_click)

        table_card = QFrame()
        table_card.setObjectName("glassCard")
        table_card.setStyleSheet("""
            QFrame#glassCard {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(0, 102, 255, 0.2);
                border-radius: 16px;
            }
        """)
        tc_layout = QVBoxLayout(table_card)
        tc_layout.setContentsMargins(16, 16, 16, 16)
        tc_layout.addWidget(self.table)
        self._main_layout.addWidget(table_card, 1)

        # Loading overlay
        self._overlay = LoadingOverlay(self)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── Data Loading ──────────────────────────────────────────────────────────
    def _load_data(self):
        self._overlay.show_loading("Loading members...")
        self._worker = Worker(self._fetch_members)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.error.connect(lambda e: self._overlay.hide_loading())
        self._worker.start()

    def _fetch_members(self):
        branch_id = self._branch_id
        if self._session.role == ROLE_ADMIN and hasattr(self, "branch_filter"):
            branch_id = self.branch_filter.currentData()
        stats = member_svc.get_member_stats(branch_id)
        members = member_svc.get_all_members(branch_id=branch_id)
        return {"stats": stats, "members": members}

    def _on_data_loaded(self, data):
        self._overlay.hide_loading()
        stats = data["stats"]
        self._members_data = data["members"]
        self._kpi_total.set_value(str(stats["total"]))
        self._kpi_active.set_value(str(stats["active"]))
        self._kpi_expired.set_value(str(stats["expired"]))
        self._kpi_inactive.set_value(str(stats["inactive"] + stats["suspended"]))
        self._populate_table(self._members_data)

    def _populate_table(self, members: list):
        rows = []
        for m in members:
            # m: id, full_name, cnic, phone, email, branch_name, trainer_name,
            #    plan_name, expiry_date, status, ...
            expiry = str(m[8]) if m[8] else "—"
            row = [
                m[0], m[1], m[2], m[3],
                m[5] or "—", m[6] or "—",
                m[7] or "—", expiry, m[9],
                ""   # Actions column placeholder
            ]
            rows.append(row)
        self.table.set_data(rows)
        # Inject action buttons per row
        self._inject_action_buttons(members)

    def _inject_action_buttons(self, members: list):
        """Add View / Edit / Delete buttons to each table row."""
        table_widget = self.table.table
        visible_members = members[
            self.table._current_page * self.table._page_size:
            (self.table._current_page + 1) * self.table._page_size
        ]
        for r_idx, m in enumerate(visible_members):
            member_id = m[0]
            cell = QWidget()
            btn_row = QHBoxLayout(cell)
            btn_row.setContentsMargins(4, 2, 4, 2)
            btn_row.setSpacing(4)

            view_btn = QPushButton("👁 View")
            view_btn.setFixedHeight(32)
            view_btn.setStyleSheet(
                "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #0097B2,stop:1 #00D4E8);"
                "border:none;border-radius:6px;color:#001A1F;"
                "font-size: 13px;font-weight:600;padding:0 8px;}"
                "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #00B8D9,stop:1 #00F5FF);}"
            )
            view_btn.clicked.connect(lambda _, mid=member_id: self.open_profile.emit(mid))

            edit_btn = QPushButton("✏ Edit")
            edit_btn.setFixedHeight(32)
            edit_btn.setStyleSheet(
                "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #0066FF,stop:1 #004BCC);"
                "border:none;border-radius:6px;color:#FFFFFF;"
                "font-size: 13px;font-weight:600;padding:0 8px;}"
                "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #3B82F6,stop:1 #0066FF);}"
            )
            edit_btn.clicked.connect(lambda _, mid=member_id: self.open_edit_form.emit(mid))

            del_btn = QPushButton("🗑 Del")
            del_btn.setFixedHeight(32)
            del_btn.setStyleSheet(
                "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #FF2D78,stop:1 #C0155A);"
                "border:none;border-radius:6px;color:#FFFFFF;"
                "font-size: 13px;font-weight:600;padding:0 8px;}"
                "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #FF5294,stop:1 #FF2D78);}"
            )
            del_btn.clicked.connect(lambda _, mid=member_id, name=m[1]: self._confirm_delete(mid, name))

            btn_row.addWidget(view_btn)
            btn_row.addWidget(edit_btn)
            btn_row.addWidget(del_btn)
            table_widget.setCellWidget(r_idx, 9, cell)

            # Status badge in status column
            badge = StatusBadge(m[9])
            table_widget.setCellWidget(r_idx, 8, badge)

    def _apply_filters(self):
        self._load_data()

    def _on_row_double_click(self, row_idx: int):
        if row_idx < len(self.table._filtered_data):
            member_id = self.table._filtered_data[row_idx][0]
            self.open_profile.emit(member_id)

    def _confirm_delete(self, member_id: int, name: str):
        dlg = ConfirmDialog(
            "Delete Member",
            f"Are you sure you want to permanently delete\n'{name}'?\n\nThis cannot be undone.",
            "Delete", "danger", self
        )
        if dlg.exec():
            result = member_svc.delete_member(member_id, self._session.user_id)
            dlg2 = InfoDialog(
                "Deleted" if result["success"] else "Error",
                result["message"],
                "success" if result["success"] else "error",
                self
            )
            dlg2.exec()
            if result["success"]:
                self._load_data()

    def refresh(self):
        self._load_data()
