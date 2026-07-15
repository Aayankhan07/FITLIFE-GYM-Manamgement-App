"""
FitLife — Trainers Screen + Form + Profile
Complete CRUD for trainer management.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QLineEdit, QGridLayout,
    QTableWidget, QTableWidgetItem, QDoubleSpinBox, QDateEdit,
    QTextEdit, QStackedWidget, QHeaderView
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from ui.components.glass_card import KPICard, StatusBadge
from ui.components.confirm_dialog import ConfirmDialog, InfoDialog
from ui.components.data_table import DataTable
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
import services.trainer_service as trainer_svc
import services.branch_service as branch_svc
from config.constants import SPECIALIZATIONS, ROLE_ADMIN, ROLE_MANAGER


# ── Trainers List Screen ──────────────────────────────────────────────────────
class TrainersScreen(QWidget):
    open_add_form  = pyqtSignal()
    open_edit_form = pyqtSignal(int)
    open_profile   = pyqtSignal(int)

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self._branch_id = session.branch_id if session.role == ROLE_MANAGER else None
        self.setStyleSheet("background:transparent;")
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        container = QWidget()
        container.setStyleSheet("background:transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(28, 24, 28, 24)
        main.setSpacing(20)

        hdr = QHBoxLayout()
        title = QLabel("💪  Trainers Management")
        title.setStyleSheet("font-size:26px; font-weight:900; color:#F0F4FF;")
        hdr.addWidget(title)
        hdr.addStretch()
        self.add_btn = QPushButton("➕  Add Trainer")
        self.add_btn.setObjectName("btnPrimary")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self.open_add_form.emit)
        hdr.addWidget(self.add_btn)
        main.addLayout(hdr)

        # KPIs
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)
        self._kpi_total  = KPICard("Total Trainers",  "—", "💪", "", "#0066FF")
        self._kpi_salary = KPICard("Avg Salary",      "—", "💰", "", "#00E676")
        for k in [self._kpi_total, self._kpi_salary]:
            kpi_row.addWidget(k)
        kpi_row.addStretch()
        main.addLayout(kpi_row)

        # Filter bar
        fbar = QFrame()
        fbar.setStyleSheet("background:rgba(255,255,255,0.04); border:1px solid rgba(0, 102, 255, 0.2); border-radius:12px;")
        fr = QHBoxLayout(fbar)
        fr.setContentsMargins(16, 10, 16, 10)
        fr.setSpacing(12)

        if self._session.role == ROLE_ADMIN:
            fr.addWidget(QLabel("Branch:"))
            self.branch_filter = QComboBox()
            self.branch_filter.setFixedHeight(34)
            self.branch_filter.addItem("All Branches", None)
            for bid, bname in branch_svc.get_all_branches_dropdown():
                self.branch_filter.addItem(bname, bid)
            self.branch_filter.currentIndexChanged.connect(self._load_data)
            fr.addWidget(self.branch_filter)

        fr.addStretch()
        refresh = QPushButton("🔄 Refresh")
        refresh.setObjectName("btnSecondary")
        refresh.setFixedHeight(34)
        refresh.clicked.connect(self._load_data)
        fr.addWidget(refresh)
        main.addWidget(fbar)

        # Table
        cols = ["ID", "Full Name", "CNIC", "Branch", "Specialization",
                "Salary", "Status", "Members", "Actions"]
        self.table = DataTable(cols)
        self.table.row_double_clicked.connect(self._on_double_click)
        tc = QFrame()
        tc.setStyleSheet("background:rgba(255,255,255,0.04); border:1px solid rgba(0, 102, 255, 0.2); border-radius:16px;")
        tc_l = QVBoxLayout(tc)
        tc_l.setContentsMargins(16, 16, 16, 16)
        tc_l.addWidget(self.table)
        main.addWidget(tc)

        self._overlay = LoadingOverlay(self)
        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _load_data(self):
        self._overlay.show_loading("Loading trainers...")
        branch_id = self._branch_id
        if self._session.role == ROLE_ADMIN and hasattr(self, "branch_filter"):
            branch_id = self.branch_filter.currentData()
        self._worker = Worker(trainer_svc.get_all_trainers, branch_id)
        self._worker.result.connect(self._on_loaded)
        self._worker.error.connect(lambda e: self._overlay.hide_loading())
        self._worker.start()

    def _on_loaded(self, trainers):
        self._overlay.hide_loading()
        self._trainers = trainers
        stats = trainer_svc.get_trainer_stats(self._branch_id)
        self._kpi_total.set_value(str(stats["total"]))
        self._kpi_salary.set_value(f"Rs. {stats['avg_salary']:,.0f}")

        rows = []
        for t in trainers:
            rows.append([
                t[0], t[1], t[2], t[5], t[6],
                f"Rs. {float(t[7]):,.0f}", t[9],
                t[12], ""
            ])
        self.table.set_data(rows)
        self._inject_buttons(trainers)

    def _inject_buttons(self, trainers):
        tw = self.table.table
        visible = trainers[
            self.table._current_page * self.table._page_size:
            (self.table._current_page + 1) * self.table._page_size
        ]
        for r_idx, t in enumerate(visible):
            tid = t[0]
            cell = QWidget()
            bl = QHBoxLayout(cell)
            bl.setContentsMargins(4, 2, 4, 2)
            bl.setSpacing(4)
            for label, color, signal in [
                ("👁 View", "#00F5FF", lambda _, i=tid: self.open_profile.emit(i)),
                ("✏️ Edit", "#0066FF", lambda _, i=tid: self.open_edit_form.emit(i)),
                ("🗑 Del",  "#FF2D78", lambda _, i=tid, n=t[1]: self._confirm_delete(i, n)),
            ]:
                btn = QPushButton(label)
                btn.setFixedHeight(32)
                btn.setStyleSheet(
                    f"QPushButton{{background:rgba(0,0,0,0.2);border:1px solid {color};"
                    f"border-radius:6px;color:{color};font-size: 13px;padding:0 8px;}}"
                    f"QPushButton:hover{{background:{color}22;}}"
                )
                btn.clicked.connect(signal)
                bl.addWidget(btn)
            tw.setCellWidget(r_idx, 8, cell)
            badge = StatusBadge(t[9])
            tw.setCellWidget(r_idx, 6, badge)

    def _on_double_click(self, row_idx):
        if row_idx < len(self.table._filtered_data):
            self.open_profile.emit(self.table._filtered_data[row_idx][0])

    def _confirm_delete(self, tid, name):
        dlg = ConfirmDialog("Delete Trainer",
                            f"Delete trainer '{name}'?\nAssigned members will be unlinked.",
                            "Delete", "danger", self)
        if dlg.exec():
            result = trainer_svc.delete_trainer(tid, self._session.user_id)
            InfoDialog("Result", result["message"],
                       "success" if result["success"] else "error", self).exec()
            if result["success"]:
                self._load_data()

    def refresh(self): self._load_data()


# ── Trainer Add/Edit Form ─────────────────────────────────────────────────────
class TrainerForm(QWidget):
    saved     = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, session, trainer_id=None, parent=None):
        super().__init__(parent)
        self._session = session
        self._trainer_id = trainer_id
        self._is_edit = trainer_id is not None
        self.setStyleSheet("background:transparent;")
        self._setup_ui()
        self._populate_dropdowns()
        if self._is_edit:
            self._load_data()

    def _inp(self, ph=""):
        f = QLineEdit(); f.setPlaceholderText(ph); f.setMinimumHeight(38); return f

    def _lbl(self, t, req=False):
        l = QLabel(("* " if req else "") + t)
        l.setStyleSheet("color:#9CA3AF;font-size:13px;" + ("font-weight:600;" if req else ""))
        return l

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        container = QWidget(); container.setStyleSheet("background:transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(28, 24, 28, 28)
        main.setSpacing(20)

        hdr = QHBoxLayout()
        back = QPushButton("← Back"); back.setObjectName("btnSecondary")
        back.setFixedHeight(36); back.clicked.connect(self.cancelled.emit)
        hdr.addWidget(back)
        hdr.addWidget(QLabel(f"{'✏️ Edit' if self._is_edit else '➕ Add'} Trainer"))
        hdr.addStretch()
        save = QPushButton("💾 Save Trainer"); save.setObjectName("btnPrimary")
        save.setMinimumHeight(40); save.clicked.connect(self._save)
        hdr.addWidget(save)
        main.addLayout(hdr)

        card = QFrame()
        card.setStyleSheet("background:rgba(255,255,255,0.05); border:1px solid rgba(0, 102, 255, 0.25); border-radius:16px;")
        grid = QGridLayout(card)
        grid.setContentsMargins(28, 24, 28, 28)
        grid.setSpacing(14)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(3, 1)
        r = 0

        # Row 0: Full Name / CNIC
        grid.addWidget(self._lbl("Full Name", True), r, 0)
        self.full_name = self._inp("e.g. Usman Farooq")
        grid.addWidget(self.full_name, r, 1)
        grid.addWidget(self._lbl("CNIC (13 digits)", True), r, 2)
        self.cnic = self._inp("4210112345678")
        grid.addWidget(self.cnic, r, 3); r += 1

        # Row 1: Phone / Email
        grid.addWidget(self._lbl("Phone", True), r, 0)
        self.phone = self._inp("03001234567")
        grid.addWidget(self.phone, r, 1)
        grid.addWidget(self._lbl("Email"), r, 2)
        self.email = self._inp("trainer@fitlife.pk")
        grid.addWidget(self.email, r, 3); r += 1

        # Row 2: Branch / Specialization
        grid.addWidget(self._lbl("Branch", True), r, 0)
        self.branch_cb = QComboBox(); self.branch_cb.setMinimumHeight(38)
        grid.addWidget(self.branch_cb, r, 1)
        grid.addWidget(self._lbl("Specialization"), r, 2)
        self.spec_cb = QComboBox(); self.spec_cb.setMinimumHeight(38)
        for s in SPECIALIZATIONS: self.spec_cb.addItem(s, s)
        grid.addWidget(self.spec_cb, r, 3); r += 1

        # Row 3: Salary / Hire Date
        grid.addWidget(self._lbl("Monthly Salary (Rs.)", True), r, 0)
        self.salary = QDoubleSpinBox()
        self.salary.setRange(0, 1000000); self.salary.setValue(45000)
        self.salary.setPrefix("Rs. "); self.salary.setMinimumHeight(38)
        grid.addWidget(self.salary, r, 1)
        grid.addWidget(self._lbl("Hire Date", True), r, 2)
        self.hire_date = QDateEdit(); self.hire_date.setCalendarPopup(True)
        self.hire_date.setDisplayFormat("dd/MM/yyyy")
        self.hire_date.setDate(QDate.currentDate()); self.hire_date.setMinimumHeight(38)
        grid.addWidget(self.hire_date, r, 3); r += 1

        # Row 4: Qualification / Address
        grid.addWidget(self._lbl("Qualification"), r, 0)
        self.qualification = self._inp("e.g. BSc Sports Science")
        grid.addWidget(self.qualification, r, 1)
        grid.addWidget(self._lbl("Address"), r, 2)
        self.address = self._inp("Full address")
        grid.addWidget(self.address, r, 3); r += 1

        # Row 5: Certifications (full width)
        grid.addWidget(self._lbl("Certifications"), r, 0)
        self.certs = self._inp("e.g. NASM CPT, CrossFit L2")
        grid.addWidget(self.certs, r, 1, 1, 3); r += 1

        main.addWidget(card)
        main.addStretch()
        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _populate_dropdowns(self):
        self.branch_cb.clear()
        for bid, bname in branch_svc.get_all_branches_dropdown():
            self.branch_cb.addItem(bname, bid)
        if self._session.role == ROLE_MANAGER and self._session.branch_id:
            idx = self.branch_cb.findData(self._session.branch_id)
            if idx >= 0: self.branch_cb.setCurrentIndex(idx)
            self.branch_cb.setEnabled(False)

    def _load_data(self):
        t = trainer_svc.get_trainer_by_id(self._trainer_id)
        if not t: return
        self.full_name.setText(t[3] or "")
        self.cnic.setText(t[4] or "")
        self.phone.setText(t[5] or "")
        self.email.setText(t[6] or "")
        self.address.setText(t[7] or "")
        idx = self.spec_cb.findData(t[9])
        if idx >= 0: self.spec_cb.setCurrentIndex(idx)
        self.salary.setValue(float(t[10]))
        if t[11]: self.hire_date.setDate(QDate(t[11].year, t[11].month, t[11].day))
        self.qualification.setText(t[12] or "")
        self.certs.setText(t[13] or "")
        idx = self.branch_cb.findData(t[2])
        if idx >= 0: self.branch_cb.setCurrentIndex(idx)

    def _validate(self):
        if not self.full_name.text().strip(): return False, "Full Name required."
        c = self.cnic.text().strip()
        if not c.isdigit() or len(c) != 13: return False, "CNIC must be 13 digits."
        if not self.phone.text().strip(): return False, "Phone required."
        if not self.branch_cb.currentData(): return False, "Branch required."
        if self.salary.value() <= 0: return False, "Salary must be > 0."
        return True, ""

    def _save(self):
        ok, msg = self._validate()
        if not ok:
            InfoDialog("Validation Error", msg, "error", self).exec()
            return
        data = {
            "branch_id":     self.branch_cb.currentData(),
            "full_name":     self.full_name.text().strip(),
            "cnic":          self.cnic.text().strip(),
            "phone":         self.phone.text().strip(),
            "email":         self.email.text().strip() or None,
            "address":       self.address.text().strip() or None,
            "specialization":self.spec_cb.currentData(),
            "monthly_salary":self.salary.value(),
            "hire_date":     self.hire_date.date().toPyDate(),
            "qualification": self.qualification.text().strip() or None,
            "certifications":self.certs.text().strip() or None,
            "status":        "Active",
        }
        if self._is_edit:
            result = trainer_svc.update_trainer(self._trainer_id, data, self._session.user_id)
        else:
            result = trainer_svc.create_trainer(data, self._session.user_id)
        InfoDialog("Saved" if result["success"] else "Error",
                   result["message"],
                   "success" if result["success"] else "error", self).exec()
        if result["success"]: self.saved.emit()


# ── Trainer Profile ───────────────────────────────────────────────────────────
class TrainerProfile(QWidget):
    go_back = pyqtSignal()
    go_edit = pyqtSignal(int)

    def __init__(self, session, trainer_id, parent=None):
        super().__init__(parent)
        self._session = session
        self._trainer_id = trainer_id
        self.setStyleSheet("background:transparent;")
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        container = QWidget(); container.setStyleSheet("background:transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(28, 24, 28, 28); main.setSpacing(20)

        hdr = QHBoxLayout()
        back = QPushButton("← Back"); back.setObjectName("btnSecondary")
        back.setFixedHeight(36); back.clicked.connect(self.go_back.emit); hdr.addWidget(back)
        hdr.addStretch()
        edit = QPushButton("✏️ Edit Trainer"); edit.setObjectName("btnPrimary")
        edit.setFixedHeight(36); edit.clicked.connect(lambda: self.go_edit.emit(self._trainer_id))
        hdr.addWidget(edit); main.addLayout(hdr)

        # Header card
        hc = QFrame()
        hc.setStyleSheet("background:rgba(0, 102, 255, 0.1); border:1px solid rgba(0, 102, 255, 0.4); border-radius:16px;")
        hcl = QHBoxLayout(hc); hcl.setContentsMargins(24, 20, 24, 20); hcl.setSpacing(20)
        self.avatar = QLabel("💪"); self.avatar.setStyleSheet("font-size:60px;"); self.avatar.setFixedWidth(80)
        hcl.addWidget(self.avatar)
        info = QVBoxLayout(); info.setSpacing(4)
        self.name_lbl = QLabel("—"); self.name_lbl.setStyleSheet("font-size:22px;font-weight:900;color:#F0F4FF;")
        self.sub_lbl  = QLabel("—"); self.sub_lbl.setStyleSheet("font-size:14px;color:#9CA3AF;")
        self.stat_badge = StatusBadge("Active")
        for w in [self.name_lbl, self.sub_lbl, self.stat_badge]: info.addWidget(w)
        hcl.addLayout(info); hcl.addStretch()
        krow = QHBoxLayout()
        self.kpi_salary  = KPICard("Salary",    "—", "💰","","#00E676")
        self.kpi_members = KPICard("Members",   "—", "👥","","#0066FF")
        for k in [self.kpi_salary, self.kpi_members]:
            k.setFixedWidth(160); krow.addWidget(k)
        hcl.addLayout(krow); main.addWidget(hc)

        # Assigned members table
        sec = QLabel("👥  Assigned Members")
        sec.setStyleSheet("font-size:16px;font-weight:bold;color:#F0F4FF;")
        main.addWidget(sec)
        self.members_table = QTableWidget()
        self.members_table.setColumnCount(5)
        self.members_table.setHorizontalHeaderLabels(["Name","Phone","Goal","Status","Expiry"])
        self.members_table.verticalHeader().setVisible(False)
        self.members_table.horizontalHeader().setStretchLastSection(True)
        self.members_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.members_table.setStyleSheet("""
            QTableWidget{background:rgba(255,255,255,0.04);border:1px solid rgba(0, 102, 255, 0.2);
            border-radius:12px;color:#F0F4FF;}
            QTableWidget::item{padding:8px;border-bottom:1px solid rgba(0, 102, 255, 0.15);}
            QHeaderView::section{background:rgba(0, 102, 255, 0.2);color:#00F5FF;
            padding:10px;border:none;font-weight:bold;}
        """)
        main.addWidget(self.members_table)
        main.addStretch()
        scroll.setWidget(container)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

    def _load_data(self):
        t = trainer_svc.get_trainer_by_id(self._trainer_id)
        if not t: return
        self.name_lbl.setText(t[3])
        self.sub_lbl.setText(f"Branch: {t[17]}  |  Spec: {t[9]}")
        self.stat_badge.set_status(t[14])
        self.kpi_salary.set_value(f"Rs. {float(t[10]):,.0f}")

        members = trainer_svc.get_assigned_members(self._trainer_id)
        self.kpi_members.set_value(str(len(members)))
        self.members_table.setRowCount(0)
        for m in members:
            r = self.members_table.rowCount()
            self.members_table.insertRow(r)
            for ci, val in enumerate([m[1], m[2], m[3]]):
                self.members_table.setItem(r, ci, QTableWidgetItem(str(val) if val else "—"))
            self.members_table.setCellWidget(r, 3, StatusBadge(m[4]))
            self.members_table.setItem(r, 4, QTableWidgetItem(str(m[5]) if m[5] else "—"))


# ── Module Container ─────────────────────────────────────────────────────────
class TrainersModule(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setStyleSheet("background:transparent;")
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)

        self._list = TrainersScreen(session)
        self._list.open_add_form.connect(self._show_add)
        self._list.open_edit_form.connect(self._show_edit)
        self._list.open_profile.connect(self._show_profile)
        self._stack.addWidget(self._list)
        self._stack.setCurrentWidget(self._list)

    def _show_add(self):
        form = TrainerForm(self._session)
        form.saved.connect(self._back)
        form.cancelled.connect(self._back)
        self._stack.addWidget(form)
        self._stack.setCurrentWidget(form)

    def _show_edit(self, tid):
        form = TrainerForm(self._session, trainer_id=tid)
        form.saved.connect(self._back)
        form.cancelled.connect(self._back)
        self._stack.addWidget(form)
        self._stack.setCurrentWidget(form)

    def _show_profile(self, tid):
        p = TrainerProfile(self._session, tid)
        p.go_back.connect(self._back)
        p.go_edit.connect(self._show_edit)
        self._stack.addWidget(p)
        self._stack.setCurrentWidget(p)

    def _back(self):
        while self._stack.count() > 1:
            w = self._stack.widget(1)
            self._stack.removeWidget(w)
            w.deleteLater()
        self._stack.setCurrentWidget(self._list)
        self._list.refresh()

    def refresh(self):
        if hasattr(self._stack.currentWidget(), "refresh"):
            self._stack.currentWidget().refresh()
