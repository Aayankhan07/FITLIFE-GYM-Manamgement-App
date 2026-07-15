"""
FitLife — Branches Module
Full CRUD for branch management (Admin only).
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QLineEdit, QGridLayout,
    QSpinBox, QDateEdit, QStackedWidget
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from ui.components.glass_card import KPICard, StatusBadge
from ui.components.data_table import DataTable
from ui.components.confirm_dialog import ConfirmDialog, InfoDialog
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
import services.branch_service as branch_svc
from config.constants import BRANCH_STATUSES


# ── Branches List ─────────────────────────────────────────────────────────────
class BranchesScreen(QWidget):
    open_add_form  = pyqtSignal()
    open_edit_form = pyqtSignal(int)

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setStyleSheet("background:transparent;")
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QWidget { border:none; background:transparent; }")
        container = QWidget(); container.setStyleSheet("background:transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(28, 24, 28, 24); main.setSpacing(20)

        hdr = QHBoxLayout()
        title = QLabel("🏢  Branch Management")
        title.setStyleSheet("QWidget { font-size:26px;font-weight:900;color:#F0F4FF; }")
        hdr.addWidget(title); hdr.addStretch()
        self.add_btn = QPushButton("➕  Add Branch")
        self.add_btn.setObjectName("btnPrimary"); self.add_btn.setMinimumHeight(40)
        self.add_btn.clicked.connect(self.open_add_form.emit)
        hdr.addWidget(self.add_btn); main.addLayout(hdr)

        # KPI row
        krow = QHBoxLayout(); krow.setSpacing(14)
        self._kpi_total  = KPICard("Total Branches", "—", "🏢","","#0066FF")
        self._kpi_active = KPICard("Active",         "—", "✅","","#00E676")
        for k in [self._kpi_total, self._kpi_active]: krow.addWidget(k)
        krow.addStretch(); main.addLayout(krow)

        # Table
        cols = ["ID","Branch Name","City","Phone","Manager","Members","Trainers","Status","Actions"]
        self.table = DataTable(cols)
        tc = QFrame()
        tc.setStyleSheet("QFrame { background:rgba(255,255,255,0.04); border:1px solid rgba(0, 102, 255, 0.2); border-radius:16px; }")
        tcl = QVBoxLayout(tc); tcl.setContentsMargins(16,16,16,16); tcl.addWidget(self.table)
        main.addWidget(tc)
        self._overlay = LoadingOverlay(self)
        scroll.setWidget(container)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

    def _load_data(self):
        self._overlay.show_loading("Loading branches...")
        self._worker = Worker(branch_svc.get_all_branches)
        self._worker.result.connect(self._on_loaded)
        self._worker.error.connect(lambda e: self._overlay.hide_loading())
        self._worker.start()

    def _on_loaded(self, branches):
        self._overlay.hide_loading()
        self._branches = branches
        active = sum(1 for b in branches if b[8] == "Active")
        self._kpi_total.set_value(str(len(branches)))
        self._kpi_active.set_value(str(active))

        rows = []
        for b in branches:
            rows.append([b[0], b[1], b[2], b[4], b[9] or "—",
                         b[10], b[11], b[8], ""])
        self.table.set_data(rows)
        self._inject_buttons(branches)

    def _inject_buttons(self, branches):
        tw = self.table.table
        visible = branches[
            self.table._current_page * self.table._page_size:
            (self.table._current_page + 1) * self.table._page_size
        ]
        for r_idx, b in enumerate(visible):
            bid = b[0]
            cell = QWidget()
            bl = QHBoxLayout(cell); bl.setContentsMargins(4,2,4,2); bl.setSpacing(4)
            for label, color, handler in [
                ("✏️ Edit", "#0066FF", lambda _, i=bid: self.open_edit_form.emit(i)),
                ("🗑 Del",  "#FF2D78", lambda _, i=bid, n=b[1]: self._confirm_delete(i, n)),
            ]:
                btn = QPushButton(label); btn.setFixedHeight(32)
                btn.setStyleSheet(
                    f"QPushButton{{background:rgba(0,0,0,0.2);border:1px solid {color};"
                    f"border-radius:6px;color:{color};font-size: 13px;padding:0 8px;}}"
                    f"QPushButton:hover{{background:{color}22;}}"
                )
                btn.clicked.connect(handler); bl.addWidget(btn)
            tw.setCellWidget(r_idx, 8, cell)
            tw.setCellWidget(r_idx, 7, StatusBadge(b[8]))

    def _confirm_delete(self, bid, name):
        dlg = ConfirmDialog("Delete Branch",
                            f"Delete branch '{name}'?\nThis cannot be undone.",
                            "Delete", "danger", self)
        if dlg.exec():
            result = branch_svc.delete_branch(bid, self._session.user_id)
            InfoDialog("Result", result["message"],
                       "success" if result["success"] else "error", self).exec()
            if result["success"]: self._load_data()

    def refresh(self): self._load_data()


# ── Branch Add/Edit Form ──────────────────────────────────────────────────────
class BranchForm(QWidget):
    saved     = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, session, branch_id=None, parent=None):
        super().__init__(parent)
        self._session = session
        self._branch_id = branch_id
        self._is_edit = branch_id is not None
        self.setStyleSheet("background:transparent;")
        self._setup_ui()
        self._populate_managers()
        if self._is_edit: self._load_data()

    def _inp(self, ph=""):
        f = QLineEdit(); f.setPlaceholderText(ph); f.setMinimumHeight(38); return f

    def _lbl(self, t, req=False):
        l = QLabel(("* " if req else "") + t)
        l.setStyleSheet("color:#9CA3AF;font-size:13px;" + ("font-weight:600;" if req else ""))
        return l

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True); scroll.setStyleSheet("QWidget { border:none;background:transparent; }")
        container = QWidget(); container.setStyleSheet("background:transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(28,24,28,28); main.setSpacing(20)

        hdr = QHBoxLayout()
        back = QPushButton("← Back"); back.setObjectName("btnSecondary")
        back.setFixedHeight(36); back.clicked.connect(self.cancelled.emit); hdr.addWidget(back)
        hdr.addWidget(QLabel(f"{'✏️ Edit' if self._is_edit else '➕ Add'} Branch"))
        hdr.addStretch()
        save = QPushButton("💾 Save Branch"); save.setObjectName("btnPrimary")
        save.setMinimumHeight(40); save.clicked.connect(self._save); hdr.addWidget(save)
        main.addLayout(hdr)

        card = QFrame()
        card.setStyleSheet("QFrame { background:rgba(255,255,255,0.05);border:1px solid rgba(0, 102, 255, 0.25);border-radius:16px; }")
        grid = QGridLayout(card)
        grid.setContentsMargins(28,24,28,28); grid.setSpacing(14)
        grid.setColumnStretch(1,1); grid.setColumnStretch(3,1)
        r = 0

        grid.addWidget(self._lbl("Branch Name",True),r,0)
        self.branch_name = self._inp("e.g. FitLife Downtown")
        grid.addWidget(self.branch_name,r,1)
        grid.addWidget(self._lbl("City",True),r,2)
        self.city = self._inp("e.g. Karachi")
        grid.addWidget(self.city,r,3); r+=1

        grid.addWidget(self._lbl("Phone",True),r,0)
        self.phone = self._inp("02112345678")
        grid.addWidget(self.phone,r,1)
        grid.addWidget(self._lbl("Email"),r,2)
        self.email = self._inp("branch@fitlife.pk")
        grid.addWidget(self.email,r,3); r+=1

        grid.addWidget(self._lbl("Address",True),r,0)
        self.address = self._inp("Full branch address")
        grid.addWidget(self.address,r,1,1,3); r+=1

        grid.addWidget(self._lbl("Capacity"),r,0)
        self.capacity = QSpinBox()
        self.capacity.setRange(10,5000); self.capacity.setValue(100)
        self.capacity.setSuffix(" members"); self.capacity.setMinimumHeight(38)
        grid.addWidget(self.capacity,r,1)
        grid.addWidget(self._lbl("Opening Date",True),r,2)
        self.opening_date = QDateEdit(); self.opening_date.setCalendarPopup(True)
        self.opening_date.setDisplayFormat("dd/MM/yyyy")
        self.opening_date.setDate(QDate.currentDate()); self.opening_date.setMinimumHeight(38)
        grid.addWidget(self.opening_date,r,3); r+=1

        grid.addWidget(self._lbl("Status"),r,0)
        self.status_cb = QComboBox(); self.status_cb.setMinimumHeight(38)
        for s in BRANCH_STATUSES: self.status_cb.addItem(s,s)
        grid.addWidget(self.status_cb,r,1)
        grid.addWidget(self._lbl("Manager"),r,2)
        self.manager_cb = QComboBox(); self.manager_cb.setMinimumHeight(38)
        self.manager_cb.addItem("— No Manager —", None)
        grid.addWidget(self.manager_cb,r,3); r+=1

        main.addWidget(card); main.addStretch()
        scroll.setWidget(container)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

    def _populate_managers(self):
        for mid, mname in branch_svc.get_managers_dropdown():
            self.manager_cb.addItem(mname, mid)

    def _load_data(self):
        b = branch_svc.get_branch_by_id(self._branch_id)
        if not b: return
        self.branch_name.setText(b[1] or "")
        self.city.setText(b[2] or "")
        self.address.setText(b[3] or "")
        self.phone.setText(b[4] or "")
        self.email.setText(b[5] or "")
        self.capacity.setValue(b[6] or 100)
        if b[7]: self.opening_date.setDate(QDate(b[7].year,b[7].month,b[7].day))
        idx = self.status_cb.findData(b[8])
        if idx >= 0: self.status_cb.setCurrentIndex(idx)
        if b[9]:
            idx = self.manager_cb.findData(b[9])
            if idx >= 0: self.manager_cb.setCurrentIndex(idx)

    def _validate(self):
        if not self.branch_name.text().strip(): return False,"Branch name required."
        if not self.city.text().strip():        return False,"City required."
        if not self.address.text().strip():     return False,"Address required."
        if not self.phone.text().strip():       return False,"Phone required."
        return True, ""

    def _save(self):
        ok, msg = self._validate()
        if not ok:
            InfoDialog("Validation Error",msg,"error",self).exec(); return
        data = {
            "branch_name":  self.branch_name.text().strip(),
            "city":         self.city.text().strip(),
            "address":      self.address.text().strip(),
            "phone":        self.phone.text().strip(),
            "email":        self.email.text().strip() or None,
            "capacity":     self.capacity.value(),
            "opening_date": self.opening_date.date().toPyDate(),
            "status":       self.status_cb.currentData(),
            "manager_id":   self.manager_cb.currentData(),
        }
        if self._is_edit:
            result = branch_svc.update_branch(self._branch_id, data, self._session.user_id)
        else:
            result = branch_svc.create_branch(data, self._session.user_id)
        InfoDialog("Saved" if result["success"] else "Error",
                   result["message"],
                   "success" if result["success"] else "error", self).exec()
        if result["success"]: self.saved.emit()


# ── Module Container ──────────────────────────────────────────────────────────
class BranchesModule(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setStyleSheet("background:transparent;")
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self._stack)
        self._list = BranchesScreen(session)
        self._list.open_add_form.connect(self._show_add)
        self._list.open_edit_form.connect(self._show_edit)
        self._stack.addWidget(self._list)
        self._stack.setCurrentWidget(self._list)

    def _show_add(self):
        form = BranchForm(self._session)
        form.saved.connect(self._back); form.cancelled.connect(self._back)
        self._stack.addWidget(form); self._stack.setCurrentWidget(form)

    def _show_edit(self, bid):
        form = BranchForm(self._session, branch_id=bid)
        form.saved.connect(self._back); form.cancelled.connect(self._back)
        self._stack.addWidget(form); self._stack.setCurrentWidget(form)

    def _back(self):
        while self._stack.count() > 1:
            w = self._stack.widget(1)
            self._stack.removeWidget(w); w.deleteLater()
        self._stack.setCurrentWidget(self._list)
        self._list.refresh()

    def refresh(self):
        if hasattr(self._stack.currentWidget(), "refresh"):
            self._stack.currentWidget().refresh()
