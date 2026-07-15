"""
FitLife — Attendance Screen
Daily check-in panel, date filter log, attendance stats KPIs.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QDateEdit,
    QTableWidget, QTableWidgetItem, QLineEdit, QSplitter,
    QHeaderView, QTextEdit
)
from PyQt6.QtCore import Qt, QDate, QTimer, pyqtSignal, QDateTime
from PyQt6.QtGui import QFont

from ui.components.glass_card import KPICard, StatusBadge, SectionHeader
from ui.components.confirm_dialog import InfoDialog
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
import services.attendance_service as att_svc
import services.member_service as member_svc
from config.constants import ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER, ATTEND_STATUSES
from datetime import date as dt_date


class AttendanceScreen(QWidget):
    """
    Attendance module with:
    - Live check-in / check-out panel (left)
    - Daily log table (right) with date picker
    - KPI stats (top)
    """

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self._branch_id = session.branch_id
        self._members_map: dict = {}
        self.setStyleSheet("background:transparent;")

        # Live clock
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)

        self._setup_ui()
        self._populate_member_dropdown()
        self._load_daily_log()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QWidget { border:none; background:transparent; }")
        container = QWidget(); container.setStyleSheet("background:transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(28,24,28,24); main.setSpacing(20)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("📅  Attendance Management")
        title.setStyleSheet("QWidget { font-size:26px; font-weight:900; color:#F0F4FF; }")
        hdr.addWidget(title); hdr.addStretch()
        self.clock_lbl = QLabel()
        self.clock_lbl.setStyleSheet("QWidget { font-size:18px; color:#00F5FF; font-weight:bold; }")
        hdr.addWidget(self.clock_lbl)
        main.addLayout(hdr)
        self._update_clock()

        # ── KPI row ───────────────────────────────────────────────────────────
        krow = QHBoxLayout(); krow.setSpacing(14)
        self._kpi_present = KPICard("Present Today", "—", "✅","","#00E676")
        self._kpi_late    = KPICard("Late Today",    "—", "⚠️","","#FFB800")
        self._kpi_total   = KPICard("Total Logged",  "—", "📊","","#0066FF")
        for k in [self._kpi_present, self._kpi_late, self._kpi_total]:
            krow.addWidget(k)
        krow.addStretch(); main.addLayout(krow)

        # ── Main Split: Check-in Panel (left) | Daily Log (right) ─────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle{background:rgba(0, 102, 255, 0.3);width:2px;}")
        splitter.setHandleWidth(2)

        # ── LEFT: Check-in Panel ──────────────────────────────────────────────
        left_frame = QFrame()
        left_frame.setObjectName("glassCard")
        left_frame.setStyleSheet("""
            QFrame {background:rgba(255,255,255,0.05);
            border:1px solid rgba(0, 102, 255, 0.25);border-radius:16px;}
        """)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(20,20,20,20); left_layout.setSpacing(14)

        sec_in = SectionHeader("🏃  Check In / Out")
        left_layout.addWidget(sec_in)

        # Member selector (search + dropdown)
        left_layout.addWidget(QLabel("Member Search:"))
        self.member_search = QLineEdit()
        self.member_search.setPlaceholderText("Type name or CNIC...")
        self.member_search.setMinimumHeight(38)
        self.member_search.textChanged.connect(self._filter_members)
        left_layout.addWidget(self.member_search)

        self.member_cb = QComboBox()
        self.member_cb.setMinimumHeight(40)
        self.member_cb.setStyleSheet("QWidget { font-size:14px; }")
        self.member_cb.currentIndexChanged.connect(self._on_member_selected)
        left_layout.addWidget(self.member_cb)

        # Status indicator
        self.status_indicator = QLabel("Select a member above")
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_indicator.setStyleSheet(
            "background:rgba(0, 102, 255, 0.1);border:1px solid rgba(0, 102, 255, 0.3);"
            "border-radius:10px;padding:10px;color:#9CA3AF;font-size:13px;"
        )
        self.status_indicator.setFixedHeight(60)
        left_layout.addWidget(self.status_indicator)

        # Notes
        left_layout.addWidget(QLabel("Notes (optional):"))
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("e.g. Arrived by bus...")
        self.notes_input.setMinimumHeight(36)
        left_layout.addWidget(self.notes_input)

        # Check-in / Check-out buttons
        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        self.checkin_btn = QPushButton("✅  Check IN")
        self.checkin_btn.setObjectName("btnSuccess")
        self.checkin_btn.setMinimumHeight(46)
        self.checkin_btn.setStyleSheet("""
            QPushButton{background:rgba(0,230,118,0.15);border:1px solid #00E676;
            border-radius:12px;color:#00E676;font-size:15px;font-weight:bold;}
            QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #33FF99,stop:1 #00E676);}
        """)
        self.checkin_btn.clicked.connect(self._do_checkin)

        self.checkout_btn = QPushButton("🔴  Check OUT")
        self.checkout_btn.setMinimumHeight(46)
        self.checkout_btn.setStyleSheet("""
            QPushButton{background:rgba(255,45,120,0.15);border:1px solid #FF2D78;
            border-radius:12px;color:#FF2D78;font-size:15px;font-weight:bold;}
            QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #FF5294,stop:1 #FF2D78);}
        """)
        self.checkout_btn.clicked.connect(self._do_checkout)
        btn_row.addWidget(self.checkin_btn)
        btn_row.addWidget(self.checkout_btn)
        left_layout.addLayout(btn_row)

        # Result message
        self.result_lbl = QLabel("")
        self.result_lbl.setWordWrap(True)
        self.result_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_lbl.setStyleSheet(
            "color:#00E676;font-size:13px;padding:8px;"
            "background:rgba(0,230,118,0.1);border-radius:8px;"
        )
        self.result_lbl.hide()
        left_layout.addWidget(self.result_lbl)
        left_layout.addStretch()
        
        if self._session.role == ROLE_TRAINER:
            self.checkin_btn.hide()
            self.checkout_btn.hide()
            self.member_search.setEnabled(False)
            self.member_cb.setEnabled(False)
            self.notes_input.setEnabled(False)
            self.status_indicator.setText("View Only Mode (Trainer)")

        splitter.addWidget(left_frame)

        # ── RIGHT: Daily Log ──────────────────────────────────────────────────
        right_frame = QFrame()
        right_frame.setObjectName("glassCard")
        right_frame.setStyleSheet("""
            QFrame {background:rgba(255,255,255,0.05);
            border:1px solid rgba(0, 102, 255, 0.25);border-radius:16px;}
        """)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(20,20,20,20); right_layout.setSpacing(12)

        # Date filter row
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Date:"))
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("dd/MM/yyyy")
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setFixedHeight(36)
        self.date_picker.dateChanged.connect(self._load_daily_log)
        filter_row.addWidget(self.date_picker)
        filter_row.addStretch()
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setObjectName("btnSecondary")
        refresh_btn.setFixedHeight(34)
        refresh_btn.clicked.connect(self._load_daily_log)
        filter_row.addWidget(refresh_btn)
        right_layout.addLayout(filter_row)

        # Log table
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(7)
        self.log_table.setHorizontalHeaderLabels(
            ["Member","CNIC","Check In","Check Out","Status","Notes","Actions"]
        )
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.horizontalHeader().setStretchLastSection(True)
        self.log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.log_table.setStyleSheet("""
            QTableWidget{background:transparent;border:none;color:#F0F4FF;}
            QTableWidget::item{padding:8px;border-bottom:1px solid rgba(0, 102, 255, 0.15);}
            QTableWidget::item:hover{background:rgba(0, 102, 255, 0.1);}
            QHeaderView::section{background:rgba(0, 102, 255, 0.2);color:#00F5FF;
            padding:10px;border:none;font-weight:bold;}
        """)
        right_layout.addWidget(self.log_table)
        splitter.addWidget(right_frame)
        splitter.setSizes([380, 800])
        main.addWidget(splitter)

        self._overlay = LoadingOverlay(self)
        scroll.setWidget(container)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _update_clock(self):
        now = QDateTime.currentDateTime()
        self.clock_lbl.setText(now.toString("ddd  dd MMM yyyy   hh:mm:ss"))

    def _populate_member_dropdown(self):
        self._all_members = []
        members = att_svc.get_members_for_checkin(self._branch_id)
        for m in members: self._all_members.append(("Member", m))
        trainers = att_svc.get_trainers_for_checkin(self._branch_id)
        for t in trainers: self._all_members.append(("Trainer", t))
        self._rebuild_member_cb(self._all_members)

    def _rebuild_member_cb(self, entities):
        self.member_cb.blockSignals(True)
        self.member_cb.clear()
        self.member_cb.addItem("— Select Person —", None)
        for etype, m in entities:
            label = f"[{etype}] {m[1]}  ({m[2]})"
            if m[3]: label += "  ✅ In"
            self.member_cb.addItem(label, (etype, m[0]))
        self.member_cb.blockSignals(False)
        self._on_member_selected(self.member_cb.currentIndex())

    def _on_member_selected(self, index):
        if self._session.role == ROLE_TRAINER:
            return
        if index > 0:
            name = self.member_cb.currentText().replace("  ✅ In", "")
            self.status_indicator.setText(f"Ready:\n{name}")
            self.status_indicator.setStyleSheet(
                "background:rgba(0,230,118,0.1);border:1px solid rgba(0,230,118,0.3);"
                "border-radius:10px;padding:10px;color:#00E676;font-size:13px;font-weight:bold;"
            )
        else:
            self.status_indicator.setText("Select a member above")
            self.status_indicator.setStyleSheet(
                "background:rgba(0, 102, 255, 0.1);border:1px solid rgba(0, 102, 255, 0.3);"
                "border-radius:10px;padding:10px;color:#9CA3AF;font-size:13px;"
            )

    def _filter_members(self, text):
        if not text.strip():
            self._rebuild_member_cb(self._all_members)
            return
        text = text.lower()
        filtered = [item for item in self._all_members
                    if text in str(item[1][1]).lower() or text in str(item[1][2]).lower()]
        self._rebuild_member_cb(filtered)

    def _load_daily_log(self):
        self._overlay.show_loading("Loading attendance...")
        log_date = self.date_picker.date().toPyDate()
        mid = None
        is_trainer = False
        if self._session.role == ROLE_MEMBER:
            member = member_svc.get_member_by_user_id(self._session.user_id)
            mid = member[0] if member else None
        elif self._session.role == ROLE_TRAINER:
            import services.trainer_service as t_svc
            trainer = t_svc.get_trainer_by_user_id(self._session.user_id)
            mid = trainer[0] if trainer else None
            is_trainer = True

        self._worker = Worker(att_svc.get_daily_log, self._branch_id, log_date, mid, is_trainer=is_trainer)
        self._worker.result.connect(self._on_log_loaded)
        self._worker.error.connect(lambda e: self._overlay.hide_loading())
        self._worker.start()

    def _on_log_loaded(self, records):
        self._overlay.hide_loading()
        mid = None
        is_trainer = False
        if self._session.role == ROLE_MEMBER:
            member = member_svc.get_member_by_user_id(self._session.user_id)
            mid = member[0] if member else None
        elif self._session.role == ROLE_TRAINER:
            import services.trainer_service as t_svc
            trainer = t_svc.get_trainer_by_user_id(self._session.user_id)
            mid = trainer[0] if trainer else None
            is_trainer = True
            
        stats = att_svc.get_attendance_stats(self._branch_id, self.date_picker.date().toPyDate(), mid, is_trainer=is_trainer)
        self._kpi_present.set_value(str(stats["present"]))
        self._kpi_late.set_value(str(stats["late"]))
        self._kpi_total.set_value(str(stats["total"]))

        self.log_table.setRowCount(0)
        for rec in records:
            r = self.log_table.rowCount()
            self.log_table.insertRow(r)
            self.log_table.setItem(r, 0, QTableWidgetItem(rec[1]))
            self.log_table.setItem(r, 1, QTableWidgetItem(rec[2]))
            cin = rec[3].strftime("%H:%M:%S") if hasattr(rec[3], 'strftime') else (str(rec[3]).split('.')[0].split()[-1] if rec[3] else "—")
            cout = rec[4].strftime("%H:%M:%S") if hasattr(rec[4], 'strftime') else (str(rec[4]).split('.')[0].split()[-1] if rec[4] else "—")
            self.log_table.setItem(r, 2, QTableWidgetItem(cin))
            self.log_table.setItem(r, 3, QTableWidgetItem(cout))
            self.log_table.setCellWidget(r, 4, StatusBadge(rec[5]))
            self.log_table.setItem(r, 5, QTableWidgetItem(rec[6] or ""))

        # Refresh member dropdown after any change
        self._populate_member_dropdown()

    def _do_checkin(self):
        data = self.member_cb.currentData()
        if not data:
            InfoDialog("Error","Please select a person.","error",self).exec(); return
        etype, mid = data
        result = att_svc.check_in(mid, self._branch_id,
                                  self._session.user_id,
                                  self.notes_input.text().strip(),
                                  is_trainer=(etype == "Trainer"))
        self._show_result(result)
        if result["success"]: self._load_daily_log()

    def _do_checkout(self):
        data = self.member_cb.currentData()
        if not data:
            InfoDialog("Error","Please select a person.","error",self).exec(); return
        etype, mid = data
        result = att_svc.check_out(mid, self._session.user_id, is_trainer=(etype == "Trainer"))
        self._show_result(result)
        if result["success"]: self._load_daily_log()

    def _show_result(self, result: dict):
        color = "#00E676" if result["success"] else "#FF2D78"
        bg    = "rgba(0,230,118,0.1)" if result["success"] else "rgba(255,45,120,0.1)"
        self.result_lbl.setStyleSheet(
            f"color:{color};font-size:13px;padding:8px;background:{bg};border-radius:8px;"
        )
        self.result_lbl.setText(result["message"])
        self.result_lbl.show()
        QTimer.singleShot(4000, self.result_lbl.hide)
        self.notes_input.clear()

    def refresh(self):
        self._load_daily_log()
