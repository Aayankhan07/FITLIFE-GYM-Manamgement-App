"""
FitLife — Workout Plans Module
List → Add/Edit Plan → Exercise Builder → Approval workflow
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QLineEdit, QGridLayout,
    QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QStackedWidget, QDialog, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.components.glass_card import KPICard, StatusBadge, SectionHeader
from ui.components.data_table import DataTable
from ui.components.confirm_dialog import ConfirmDialog, InfoDialog
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
import services.workout_service as workout_svc
import services.member_service as member_svc
import services.trainer_service as trainer_svc
import services.branch_service as branch_svc
from config.constants import (
    PLAN_STATUSES, FITNESS_GOALS, DAYS_OF_WEEK,
    ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER
)


# ── Plans List ────────────────────────────────────────────────────────────────
class WorkoutPlansScreen(QWidget):
    open_add    = pyqtSignal()
    open_edit   = pyqtSignal(int)
    open_detail = pyqtSignal(int)

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self._branch_id = session.branch_id
        self.setStyleSheet("background:transparent;")
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        container = QWidget(); container.setStyleSheet("background:transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(28,24,28,24); main.setSpacing(20)

        hdr = QHBoxLayout()
        title = QLabel("🏋️  Workout Plans")
        title.setStyleSheet("font-size:26px; font-weight:900; color:#F0F4FF;")
        hdr.addWidget(title); hdr.addStretch()
        if self._session.role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER):
            self.add_btn = QPushButton("➕  New Plan")
            self.add_btn.setObjectName("btnPrimary"); self.add_btn.setMinimumHeight(40)
            self.add_btn.clicked.connect(self.open_add.emit)
            hdr.addWidget(self.add_btn)
        main.addLayout(hdr)

        # KPIs
        krow = QHBoxLayout(); krow.setSpacing(14)
        self._kpi_total   = KPICard("Total Plans", "—","📋","","#7C3AED")
        self._kpi_active  = KPICard("Active",      "—","✅","","#00E676")
        self._kpi_pending = KPICard("Pending",     "—","⏳","","#FFB800")
        self._kpi_approved= KPICard("Approved",    "—","🏆","","#00F5FF")
        for k in [self._kpi_total, self._kpi_active, self._kpi_pending, self._kpi_approved]:
            krow.addWidget(k)
        main.addLayout(krow)

        # Status filter
        fbar = QFrame()
        fbar.setStyleSheet("background:rgba(255,255,255,0.04);border:1px solid rgba(124,58,237,0.2);border-radius:12px;")
        fr = QHBoxLayout(fbar); fr.setContentsMargins(16,10,16,10); fr.setSpacing(12)
        fr.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox(); self.status_filter.setFixedHeight(34)
        self.status_filter.addItem("All", None)
        for s in PLAN_STATUSES: self.status_filter.addItem(s, s)
        self.status_filter.currentIndexChanged.connect(self._load_data)
        fr.addWidget(self.status_filter); fr.addStretch()
        ref = QPushButton("🔄 Refresh"); ref.setObjectName("btnSecondary"); ref.setFixedHeight(34)
        ref.clicked.connect(self._load_data); fr.addWidget(ref)
        main.addWidget(fbar)

        # Table
        cols = ["ID","Member","Trainer","Plan Name","Goal","Weeks","Status","Actions"]
        self.table = DataTable(cols)
        self.table.row_double_clicked.connect(
            lambda r: self.open_detail.emit(self.table._filtered_data[r][0])
            if r < len(self.table._filtered_data) else None
        )
        tc = QFrame()
        tc.setStyleSheet("background:rgba(255,255,255,0.04);border:1px solid rgba(124,58,237,0.2);border-radius:16px;")
        tcl = QVBoxLayout(tc); tcl.setContentsMargins(16,16,16,16); tcl.addWidget(self.table)
        main.addWidget(tc)

        self._overlay = LoadingOverlay(self)
        scroll.setWidget(container)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

    def _load_data(self):
        self._overlay.show_loading("Loading plans...")
        status = self.status_filter.currentData()
        role   = self._session.role
        tid    = None
        mid    = None
        bid    = self._branch_id
        if role == ROLE_TRAINER:
            trainer = trainer_svc.get_trainer_by_user_id(self._session.user_id)
            tid = trainer[0] if trainer else None
        elif role == ROLE_MEMBER:
            member = member_svc.get_member_by_user_id(self._session.user_id)
            mid = member[0] if member else None

        self._worker = Worker(workout_svc.get_all_plans, bid, mid, status, tid)
        self._worker.result.connect(self._on_loaded)
        self._worker.error.connect(lambda e: self._overlay.hide_loading())
        self._worker.start()

    def _on_loaded(self, plans):
        self._overlay.hide_loading()
        mid = None
        if self._session.role == ROLE_MEMBER:
            member = member_svc.get_member_by_user_id(self._session.user_id)
            mid = member[0] if member else None
            
        stats = workout_svc.get_plan_stats(self._branch_id, mid)
        self._kpi_total.set_value(str(stats["total"]))
        self._kpi_active.set_value(str(stats["active"]))
        self._kpi_pending.set_value(str(stats["pending"]))
        self._kpi_approved.set_value(str(stats["approved"]))
        rows = [[p[0],p[1],p[2] or "—",p[3],p[4],p[5],p[6],""] for p in plans]
        self.table.set_data(rows)
        self._inject_buttons(plans)

    def _inject_buttons(self, plans):
        tw = self.table.table
        visible = plans[
            self.table._current_page*self.table._page_size:
            (self.table._current_page+1)*self.table._page_size
        ]
        role = self._session.role
        for r_idx, p in enumerate(visible):
            pid, status = p[0], p[6]
            cell = QWidget(); bl = QHBoxLayout(cell)
            bl.setContentsMargins(4,2,4,2); bl.setSpacing(4)

            view_btn = QPushButton("👁 View")
            view_btn.setFixedHeight(32)
            view_btn.setStyleSheet("QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0097B2,stop:1 #00D4E8);border:none;border-radius:6px;color:#001A1F;font-weight:600;font-size: 13px;padding:0 8px;}QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00B8D9,stop:1 #00F5FF);}")
            view_btn.clicked.connect(lambda _, i=pid: self.open_detail.emit(i))
            bl.addWidget(view_btn)

            if role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER):
                edit_btn = QPushButton("✏️ Edit")
                edit_btn.setFixedHeight(32)
                edit_btn.setStyleSheet("QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7C3AED,stop:1 #5B21B6);border:none;border-radius:6px;color:#FFFFFF;font-weight:600;font-size: 13px;padding:0 8px;}QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #8B5CF6,stop:1 #7C3AED);}")
                edit_btn.clicked.connect(lambda _, i=pid: self.open_edit.emit(i))
                bl.addWidget(edit_btn)

                if role == ROLE_TRAINER and status == "Pending Verification":
                    approve_btn = QPushButton("✅ Approve")
                    approve_btn.setFixedHeight(32)
                    approve_btn.setStyleSheet("QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00E676,stop:1 #00B248);border:none;border-radius:6px;color:#001A0A;font-weight:600;font-size: 13px;padding:0 8px;}")
                    approve_btn.clicked.connect(lambda _, i=pid: self._approve_plan(i))
                    bl.addWidget(approve_btn)

            tw.setCellWidget(r_idx, 7, cell)
            tw.setCellWidget(r_idx, 6, StatusBadge(status))

    def _approve_plan(self, plan_id):
        trainer = trainer_svc.get_trainer_by_user_id(self._session.user_id)
        if not trainer:
            InfoDialog("Error","Trainer record not found.","error",self).exec(); return
        result = workout_svc.approve_plan(plan_id, trainer[0])
        InfoDialog("Result", result["message"],
                   "success" if result["success"] else "error", self).exec()
        if result["success"]: self._load_data()

    def refresh(self): self._load_data()


# ── Plan Detail / Exercise Builder ────────────────────────────────────────────
class WorkoutPlanDetail(QWidget):
    go_back = pyqtSignal()
    go_edit = pyqtSignal(int)

    def __init__(self, session, plan_id, parent=None):
        super().__init__(parent)
        self._session = session
        self._plan_id = plan_id
        self.setStyleSheet("background:transparent;")
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        container = QWidget(); container.setStyleSheet("background:transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(28,24,28,28); main.setSpacing(20)

        hdr = QHBoxLayout()
        back = QPushButton("← Back"); back.setObjectName("btnSecondary")
        back.setFixedHeight(36); back.clicked.connect(self.go_back.emit); hdr.addWidget(back)
        hdr.addStretch()
        if self._session.role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER):
            edit = QPushButton("✏️ Edit Plan"); edit.setObjectName("btnPrimary")
            edit.setFixedHeight(36); edit.clicked.connect(lambda: self.go_edit.emit(self._plan_id))
            hdr.addWidget(edit)
        main.addLayout(hdr)

        # Header card
        hc = QFrame()
        hc.setStyleSheet("background:rgba(124,58,237,0.1);border:1px solid rgba(124,58,237,0.4);border-radius:16px;")
        hcl = QHBoxLayout(hc); hcl.setContentsMargins(24,20,24,20); hcl.setSpacing(20)
        info = QVBoxLayout(); info.setSpacing(6)
        self.title_lbl = QLabel("—")
        self.title_lbl.setStyleSheet("font-size:22px;font-weight:900;color:#F0F4FF;")
        self.sub_lbl = QLabel("—"); self.sub_lbl.setStyleSheet("font-size:14px;color:#9CA3AF;")
        self.status_badge = StatusBadge("Draft")
        for w in [self.title_lbl, self.sub_lbl, self.status_badge]: info.addWidget(w)
        hcl.addLayout(info); hcl.addStretch()
        krow = QHBoxLayout()
        self.kpi_weeks = KPICard("Weeks","—","📅","","#7C3AED")
        self.kpi_exercises = KPICard("Exercises","—","💪","","#00F5FF")
        for k in [self.kpi_weeks, self.kpi_exercises]: k.setFixedWidth(160); krow.addWidget(k)
        hcl.addLayout(krow); main.addWidget(hc)

        # Exercises per day
        SectionHeader_lbl = SectionHeader("📋  Exercise Schedule")
        main.addWidget(SectionHeader_lbl)

        # Add exercise row (staff only)
        if self._session.role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER):
            add_ex_frame = QFrame()
            add_ex_frame.setStyleSheet("background:rgba(0,245,255,0.05);border:1px solid rgba(0,245,255,0.2);border-radius:12px;")
            exf = QGridLayout(add_ex_frame)
            exf.setContentsMargins(16,12,16,12); exf.setSpacing(10)

            self.ex_name  = QLineEdit(); self.ex_name.setPlaceholderText("Exercise name*"); self.ex_name.setMinimumHeight(34)
            self.ex_day   = QComboBox(); self.ex_day.setMinimumHeight(34)
            for d in DAYS_OF_WEEK: self.ex_day.addItem(d,d)
            self.ex_sets  = QSpinBox(); self.ex_sets.setRange(1,20); self.ex_sets.setValue(3); self.ex_sets.setMinimumHeight(34)
            self.ex_reps  = QSpinBox(); self.ex_reps.setRange(1,100); self.ex_reps.setValue(10); self.ex_reps.setMinimumHeight(34)
            self.ex_rest  = QSpinBox(); self.ex_rest.setRange(0,300); self.ex_rest.setValue(60); self.ex_rest.setSuffix("s"); self.ex_rest.setMinimumHeight(34)
            self.ex_notes = QLineEdit(); self.ex_notes.setPlaceholderText("Notes"); self.ex_notes.setMinimumHeight(34)

            exf.addWidget(QLabel("Exercise:"),0,0); exf.addWidget(self.ex_name,0,1)
            exf.addWidget(QLabel("Day:"),0,2);      exf.addWidget(self.ex_day,0,3)
            exf.addWidget(QLabel("Sets:"),0,4);     exf.addWidget(self.ex_sets,0,5)
            exf.addWidget(QLabel("Reps:"),0,6);     exf.addWidget(self.ex_reps,0,7)
            exf.addWidget(QLabel("Rest:"),1,0);     exf.addWidget(self.ex_rest,1,1)
            exf.addWidget(QLabel("Notes:"),1,2);    exf.addWidget(self.ex_notes,1,3,1,3)

            add_ex_btn = QPushButton("➕ Add Exercise"); add_ex_btn.setObjectName("btnPrimary")
            add_ex_btn.setFixedHeight(36); add_ex_btn.clicked.connect(self._add_exercise)
            exf.addWidget(add_ex_btn,1,6,1,2)
            main.addWidget(add_ex_frame)

        # Exercises table — columns depend on role
        is_staff = self._session.role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER)
        if is_staff:
            self._ex_col_count = 7
            headers = ["Exercise", "Day", "Sets", "Reps", "Rest (s)", "Notes", "Delete"]
        else:
            self._ex_col_count = 6
            headers = ["💪 Exercise", "📅 Day", "Sets", "Reps", "Rest", "Notes"]

        self.ex_table = QTableWidget()
        self.ex_table.setColumnCount(self._ex_col_count)
        self.ex_table.setHorizontalHeaderLabels(headers)
        self.ex_table.verticalHeader().setVisible(False)
        self.ex_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.ex_table.horizontalHeader().setStretchLastSection(not is_staff)
        self.ex_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.ex_table.setAlternatingRowColors(True)
        self.ex_table.setStyleSheet("""
            QTableWidget{background:rgba(255,255,255,0.04);border:1px solid rgba(124,58,237,0.2);
            border-radius:12px;color:#F0F4FF;gridline-color:rgba(124,58,237,0.1);}
            QTableWidget::item{padding:10px 8px;border-bottom:1px solid rgba(124,58,237,0.1);}
            QTableWidget::item:alternate{background:rgba(124,58,237,0.05);}
            QTableWidget::item:selected{background:rgba(124,58,237,0.25);}
            QHeaderView::section{background:rgba(124,58,237,0.25);color:#00F5FF;
            padding:10px;border:none;font-weight:bold;font-size:13px;}
        """)
        main.addWidget(self.ex_table)
        main.addStretch()
        scroll.setWidget(container)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

    def _load_data(self):
        plan = workout_svc.get_plan_by_id(self._plan_id)
        if not plan: return
        self.title_lbl.setText(plan[3])
        self.sub_lbl.setText(f"Member: {plan[10]}  |  Trainer: {plan[11] or '—'}  |  Goal: {plan[4]}")
        self.status_badge.set_status(plan[6])
        self.kpi_weeks.set_value(str(plan[5]))
        exercises = workout_svc.get_exercises(self._plan_id)
        self.kpi_exercises.set_value(str(len(exercises)))
        self._populate_exercises(exercises)

    def _populate_exercises(self, exercises):
        self.ex_table.setRowCount(0)
        can_delete = self._session.role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER)

        # Group by day for a clean display
        from collections import OrderedDict
        days_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        grouped = OrderedDict()
        for d in days_order:
            grouped[d] = []
        for ex in exercises:
            day = ex[5] if ex[5] in grouped else "Monday"
            grouped[day].append(ex)

        for day, exs in grouped.items():
            if not exs:
                continue
            # Day separator row
            sep_row = self.ex_table.rowCount()
            self.ex_table.insertRow(sep_row)
            day_item = QTableWidgetItem(f"  📅  {day}")
            day_item.setForeground(__import__('PyQt6.QtGui', fromlist=['QColor']).QColor("#FFB800"))
            from PyQt6.QtGui import QFont, QColor
            f = QFont(); f.setBold(True); f.setPointSize(11)
            day_item.setFont(f)
            day_item.setBackground(QColor(255, 184, 0, 25))
            self.ex_table.setItem(sep_row, 0, day_item)
            self.ex_table.setSpan(sep_row, 0, 1, self._ex_col_count)

            for ex in exs:
                r = self.ex_table.rowCount()
                self.ex_table.insertRow(r)
                vals = [ex[1], ex[5], str(ex[2]), str(ex[3]), f"{ex[4]}s", ex[6] or ""]
                for ci, val in enumerate(vals):
                    item = QTableWidgetItem(str(val))
                    self.ex_table.setItem(r, ci, item)
                if can_delete:
                    del_btn = QPushButton("🗑")
                    del_btn.setFixedHeight(30)
                    del_btn.setStyleSheet(
                        "QPushButton{background:rgba(255,45,120,0.15);border:1px solid #FF2D78;"
                        "border-radius:6px;color:#FF2D78;font-size:14px;}"
                        "QPushButton:hover{background:#FF2D78;color:#fff;}"
                    )
                    del_btn.clicked.connect(lambda _, eid=ex[0]: self._delete_exercise(eid))
                    self.ex_table.setCellWidget(r, 6, del_btn)

    def _add_exercise(self):
        name = self.ex_name.text().strip()
        if not name:
            InfoDialog("Error","Exercise name required.","error",self).exec(); return
        data = {
            "exercise_name": name,
            "day_of_week":   self.ex_day.currentData(),
            "sets":          self.ex_sets.value(),
            "reps":          self.ex_reps.value(),
            "rest_seconds":  self.ex_rest.value(),
            "notes":         self.ex_notes.text().strip(),
        }
        result = workout_svc.add_exercise(self._plan_id, data, self._session.user_id)
        if result["success"]:
            self.ex_name.clear(); self.ex_notes.clear()
            self._load_data()
        else:
            InfoDialog("Error", result["message"], "error", self).exec()

    def _delete_exercise(self, eid):
        dlg = ConfirmDialog("Remove Exercise","Remove this exercise?","Remove","danger",self)
        if dlg.exec():
            result = workout_svc.delete_exercise(eid)
            if result["success"]: self._load_data()


# ── Plan Form (Add/Edit) ──────────────────────────────────────────────────────
class WorkoutPlanForm(QWidget):
    saved     = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, session, plan_id=None, parent=None):
        super().__init__(parent)
        self._session = session
        self._plan_id = plan_id
        self._is_edit = plan_id is not None
        self.setStyleSheet("background:transparent;")
        self._setup_ui()
        self._populate_dropdowns()
        if self._is_edit: self._load_data()

    def _inp(self, ph=""): f=QLineEdit(); f.setPlaceholderText(ph); f.setMinimumHeight(38); return f
    def _lbl(self, t, req=False):
        l=QLabel(("* " if req else "")+t); l.setStyleSheet("color:#9CA3AF;font-size:13px;"); return l

    def _setup_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        container = QWidget(); container.setStyleSheet("background:transparent;")
        main = QVBoxLayout(container); main.setContentsMargins(28,24,28,28); main.setSpacing(20)

        hdr = QHBoxLayout()
        back = QPushButton("← Back"); back.setObjectName("btnSecondary")
        back.setFixedHeight(36); back.clicked.connect(self.cancelled.emit); hdr.addWidget(back)
        hdr.addWidget(QLabel(f"{'✏️ Edit' if self._is_edit else '➕ New'} Workout Plan"))
        hdr.addStretch()
        save = QPushButton("💾 Save Plan"); save.setObjectName("btnPrimary")
        save.setMinimumHeight(40); save.clicked.connect(self._save); hdr.addWidget(save)
        main.addLayout(hdr)

        card = QFrame()
        card.setStyleSheet("background:rgba(255,255,255,0.05);border:1px solid rgba(124,58,237,0.25);border-radius:16px;")
        grid = QGridLayout(card); grid.setContentsMargins(28,24,28,28); grid.setSpacing(14)
        grid.setColumnStretch(1,1); grid.setColumnStretch(3,1); r=0

        grid.addWidget(self._lbl("Plan Name",True),r,0)
        self.plan_name = self._inp("e.g. 12-Week Mass Builder"); grid.addWidget(self.plan_name,r,1)
        grid.addWidget(self._lbl("Goal"),r,2)
        self.goal_cb = QComboBox(); self.goal_cb.setMinimumHeight(38)
        for g in FITNESS_GOALS: self.goal_cb.addItem(g,g)
        grid.addWidget(self.goal_cb,r,3); r+=1

        grid.addWidget(self._lbl("Duration (weeks)"),r,0)
        self.weeks = QSpinBox(); self.weeks.setRange(1,52); self.weeks.setValue(4); self.weeks.setMinimumHeight(38)
        grid.addWidget(self.weeks,r,1)
        grid.addWidget(self._lbl("Status"),r,2)
        self.status_cb = QComboBox(); self.status_cb.setMinimumHeight(38)
        for s in PLAN_STATUSES: self.status_cb.addItem(s,s)
        if self._session.role in (ROLE_ADMIN, ROLE_MANAGER):
            idx = self.status_cb.findData("Pending Verification")
            if idx >= 0: self.status_cb.setCurrentIndex(idx)
        grid.addWidget(self.status_cb,r,3); r+=1

        grid.addWidget(self._lbl("Member",True),r,0)
        self.member_cb = QComboBox(); self.member_cb.setMinimumHeight(38)
        grid.addWidget(self.member_cb,r,1)
        grid.addWidget(self._lbl("Assigned Trainer"),r,2)
        self.trainer_cb = QComboBox(); self.trainer_cb.setMinimumHeight(38)
        self.trainer_cb.addItem("— No Trainer —", None)
        grid.addWidget(self.trainer_cb,r,3); r+=1

        grid.addWidget(self._lbl("Notes / Description"),r,0)
        self.notes = QTextEdit(); self.notes.setFixedHeight(90)
        self.notes.setPlaceholderText("Overview, special instructions...")
        grid.addWidget(self.notes,r,1,1,3)

        main.addWidget(card); main.addStretch()
        scroll.setWidget(container)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

    def _populate_dropdowns(self):
        bid = self._session.branch_id
        members = member_svc.get_all_members(branch_id=bid, status="Active")
        self.member_cb.clear(); self.member_cb.addItem("— Select Member —", None)
        for m in members: self.member_cb.addItem(f"{m[1]} ({m[2]})", m[0])

        if bid:
            trainers = trainer_svc.get_trainers_for_branch(bid)
            for t in trainers: self.trainer_cb.addItem(f"{t[1]} ({t[2]})", t[0])

    def _load_data(self):
        p = workout_svc.get_plan_by_id(self._plan_id)
        if not p: return
        self.plan_name.setText(p[3] or "")
        idx = self.goal_cb.findData(p[4]); self.goal_cb.setCurrentIndex(max(0,idx))
        self.weeks.setValue(p[5] or 4)
        idx = self.status_cb.findData(p[6]); self.status_cb.setCurrentIndex(max(0,idx))
        idx = self.member_cb.findData(p[1]); self.member_cb.setCurrentIndex(max(0,idx))
        if p[2]:
            idx = self.trainer_cb.findData(p[2]); self.trainer_cb.setCurrentIndex(max(0,idx))
        self.notes.setPlainText(p[7] or "")

    def _save(self):
        if not self.plan_name.text().strip():
            InfoDialog("Error","Plan name is required.","error",self).exec(); return
        if not self.member_cb.currentData():
            InfoDialog("Error","Please select a member.","error",self).exec(); return
        data = {
            "plan_name":  self.plan_name.text().strip(),
            "goal":       self.goal_cb.currentData(),
            "weeks":      self.weeks.value(),
            "status":     self.status_cb.currentData(),
            "member_id":  self.member_cb.currentData(),
            "trainer_id": self.trainer_cb.currentData(),
            "notes":      self.notes.toPlainText().strip(),
        }
        if self._is_edit:
            result = workout_svc.update_plan(self._plan_id, data, self._session.user_id)
        else:
            result = workout_svc.create_plan(data, self._session.user_id)
        InfoDialog("Result", result["message"],
                   "success" if result["success"] else "error", self).exec()
        if result["success"]: self.saved.emit()


# ── Module Container ──────────────────────────────────────────────────────────
class WorkoutPlansModule(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setStyleSheet("background:transparent;")
        self._stack = QStackedWidget(); self._stack.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.addWidget(self._stack)
        self._list = WorkoutPlansScreen(session)
        self._list.open_add.connect(self._show_add)
        self._list.open_edit.connect(self._show_edit)
        self._list.open_detail.connect(self._show_detail)
        self._stack.addWidget(self._list); self._stack.setCurrentWidget(self._list)

    def _show_add(self):
        form = WorkoutPlanForm(self._session)
        form.saved.connect(self._back); form.cancelled.connect(self._back)
        self._stack.addWidget(form); self._stack.setCurrentWidget(form)

    def _show_edit(self, pid):
        form = WorkoutPlanForm(self._session, plan_id=pid)
        form.saved.connect(self._back); form.cancelled.connect(self._back)
        self._stack.addWidget(form); self._stack.setCurrentWidget(form)

    def _show_detail(self, pid):
        detail = WorkoutPlanDetail(self._session, pid)
        detail.go_back.connect(self._back); detail.go_edit.connect(self._show_edit)
        self._stack.addWidget(detail); self._stack.setCurrentWidget(detail)

    def _back(self):
        while self._stack.count() > 1:
            w = self._stack.widget(1); self._stack.removeWidget(w); w.deleteLater()
        self._stack.setCurrentWidget(self._list); self._list.refresh()

    def refresh(self):
        if hasattr(self._stack.currentWidget(), "refresh"):
            self._stack.currentWidget().refresh()
