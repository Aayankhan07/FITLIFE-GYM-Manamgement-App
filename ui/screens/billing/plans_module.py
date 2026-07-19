"""
FitLife — Membership Plans Module
Full CRUD + assign membership to member with auto-expiry.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QLineEdit, QGridLayout,
    QDoubleSpinBox, QSpinBox, QTextEdit, QStackedWidget,
    QTableWidget, QTableWidgetItem, QCheckBox, QDateEdit, QHeaderView
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from ui.components.glass_card import KPICard, StatusBadge
from ui.components.data_table import DataTable
from ui.components.confirm_dialog import ConfirmDialog, InfoDialog
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
import services.membership_service as membership_svc
import services.member_service as member_svc
import services.branch_service as branch_svc


# ── Plans List ────────────────────────────────────────────────────────────────
class PlansScreen(QWidget):
    open_add_form  = pyqtSignal()
    open_edit_form = pyqtSignal(int)
    open_assign    = pyqtSignal()

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
        main.setContentsMargins(28,24,28,24); main.setSpacing(20)

        hdr = QHBoxLayout()
        title = QLabel("📋  Membership Plans")
        title.setStyleSheet("QWidget { font-size:26px;font-weight:900;color:#F0F4FF; }")
        hdr.addWidget(title); hdr.addStretch()

        self.assign_btn = QPushButton("🔗  Assign Membership")
        self.assign_btn.setObjectName("btnSecondary")
        self.assign_btn.setMinimumHeight(40)
        self.assign_btn.clicked.connect(self.open_assign.emit)
        hdr.addWidget(self.assign_btn)

        self.add_btn = QPushButton("➕  New Plan")
        self.add_btn.setObjectName("btnPrimary")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.clicked.connect(self.open_add_form.emit)
        hdr.addWidget(self.add_btn)
        main.addLayout(hdr)

        # KPIs
        krow = QHBoxLayout(); krow.setSpacing(14)
        self._kpi_total  = KPICard("Total Plans",  "—", "📋","","#0066FF")
        self._kpi_active = KPICard("Active Plans", "—", "✅","","#00E676")
        for k in [self._kpi_total, self._kpi_active]: krow.addWidget(k)
        krow.addStretch(); main.addLayout(krow)

        # Usage stats table
        stats_lbl = QLabel("Plan Usage Statistics")
        stats_lbl.setStyleSheet("QWidget { font-size:15px;font-weight:bold;color:#F0F4FF; }")
        main.addWidget(stats_lbl)

        self.usage_table = QTableWidget()
        self.usage_table.setColumnCount(4)
        self.usage_table.setHorizontalHeaderLabels(["Plan Name","Active Members","Duration","Price"])
        self.usage_table.verticalHeader().setVisible(False)
        self.usage_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.usage_table.setStyleSheet("""
            QTableWidget{background:rgba(255,255,255,0.04);border:1px solid rgba(0, 102, 255, 0.2);
            border-radius:12px;color:#F0F4FF;}
            QTableWidget::item{padding:8px;border-bottom:1px solid rgba(0, 102, 255, 0.15);}
            QHeaderView::section{background:rgba(0, 102, 255, 0.2);color:#00F5FF;padding:10px;border:none;font-weight:bold;}
        """)
        header = self.usage_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 4):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.usage_table.setMaximumHeight(200)
        main.addWidget(self.usage_table)

        # Full plans table
        cols = ["ID","Plan Name","Duration (days)","Price","Description","Active","Actions"]
        self.table = DataTable(cols)
        tc = QFrame()
        tc.setStyleSheet("QFrame { background:rgba(255,255,255,0.04);border:1px solid rgba(0, 102, 255, 0.2);border-radius:16px; }")
        tcl = QVBoxLayout(tc); tcl.setContentsMargins(16,16,16,16); tcl.addWidget(self.table)
        main.addWidget(tc)

        self._overlay = LoadingOverlay(self)
        scroll.setWidget(container)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

    def _load_data(self):
        self._overlay.show_loading("Loading plans...")
        self._worker = Worker(membership_svc.get_all_plans)
        self._worker.result.connect(self._on_loaded)
        self._worker.error.connect(lambda e: self._overlay.hide_loading())
        self._worker.start()

    def _on_loaded(self, plans):
        self._overlay.hide_loading()
        self._plans = plans
        active = sum(1 for p in plans if p[5])
        self._kpi_total.set_value(str(len(plans)))
        self._kpi_active.set_value(str(active))

        # Usage stats
        stats = membership_svc.get_plan_usage_stats()
        self.usage_table.setRowCount(0)
        for s in stats:
            r = self.usage_table.rowCount()
            self.usage_table.insertRow(r)
            self.usage_table.setItem(r,0,QTableWidgetItem(s[0]))
            self.usage_table.setItem(r,1,QTableWidgetItem(str(s[1])))
            self.usage_table.setItem(r,2,QTableWidgetItem(f"{s[3]} days"))
            self.usage_table.setItem(r,3,QTableWidgetItem(f"Rs. {float(s[2]):,.0f}"))

        rows = []
        for p in plans:
            rows.append([p[0], p[1], p[2], f"Rs. {float(p[3]):,.0f}",
                         (p[4] or "")[:40], "Yes" if p[5] else "No", ""])
        self.table.set_data(rows)
        self._inject_buttons(plans)

    def _inject_buttons(self, plans):
        tw = self.table.table
        visible = plans[
            self.table._current_page * self.table._page_size:
            (self.table._current_page + 1) * self.table._page_size
        ]
        for r_idx, p in enumerate(visible):
            pid = p[0]
            cell = QWidget()
            bl = QHBoxLayout(cell); bl.setContentsMargins(4,2,4,2); bl.setSpacing(4)
            is_active = bool(p[5])
            toggle_lbl = "🔴 Deactivate" if is_active else "🟢 Activate"
            toggle_color = "#FF2D78" if is_active else "#00E676"
            for label, color, handler in [
                ("✏️ Edit",     "#0066FF", lambda _, i=pid: self.open_edit_form.emit(i)),
                (toggle_lbl, toggle_color, lambda _, i=pid: self._toggle_active(i)),
                ("🗑 Del",     "#FF2D78", lambda _, i=pid, n=p[1]: self._confirm_delete(i,n)),
            ]:
                btn = QPushButton(label); btn.setFixedHeight(32)
                btn.setStyleSheet(
                    f"QPushButton{{background:rgba(0,0,0,0.2);border:1px solid {color};"
                    f"border-radius:6px;color:{color};font-size: 13px;padding:0 8px;}}"
                    f"QPushButton:hover{{background:{color}22;}}"
                )
                btn.clicked.connect(handler); bl.addWidget(btn)
            tw.setCellWidget(r_idx, 6, cell)

    def _toggle_active(self, pid):
        result = membership_svc.toggle_plan_active(pid, self._session.user_id)
        if result["success"]: self._load_data()

    def _confirm_delete(self, pid, name):
        dlg = ConfirmDialog("Delete Plan",
                            f"Delete membership plan '{name}'?",
                            "Delete", "danger", self)
        if dlg.exec():
            result = membership_svc.delete_plan(pid, self._session.user_id)
            InfoDialog("Result", result["message"],
                       "success" if result["success"] else "error", self).exec()
            if result["success"]: self._load_data()

    def refresh(self): self._load_data()


# ── Plan Add/Edit Form ─────────────────────────────────────────────────────────
class PlanForm(QWidget):
    saved     = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, session, plan_id=None, parent=None):
        super().__init__(parent)
        self._session = session
        self._plan_id = plan_id
        self._is_edit = plan_id is not None
        self.setStyleSheet("background:transparent;")
        self._setup_ui()
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
        hdr.addWidget(QLabel(f"{'✏️ Edit' if self._is_edit else '➕ New'} Membership Plan"))
        hdr.addStretch()
        save = QPushButton("💾 Save Plan"); save.setObjectName("btnPrimary")
        save.setMinimumHeight(40); save.clicked.connect(self._save); hdr.addWidget(save)
        main.addLayout(hdr)

        card = QFrame()
        card.setStyleSheet("QFrame { background:rgba(255,255,255,0.05);border:1px solid rgba(0, 102, 255, 0.25);border-radius:16px; }")
        grid = QGridLayout(card)
        grid.setContentsMargins(28,24,28,28); grid.setSpacing(14)
        grid.setColumnStretch(1,1); grid.setColumnStretch(3,1)
        r=0

        grid.addWidget(self._lbl("Plan Name",True),r,0)
        self.plan_name = self._inp("e.g. Monthly Premium"); grid.addWidget(self.plan_name,r,1)
        grid.addWidget(self._lbl("Duration (days)",True),r,2)
        self.duration = QSpinBox()
        self.duration.setRange(1,3650); self.duration.setValue(30); self.duration.setMinimumHeight(38)
        grid.addWidget(self.duration,r,3); r+=1

        grid.addWidget(self._lbl("Price (Rs.)",True),r,0)
        self.price = QDoubleSpinBox()
        self.price.setRange(0,1000000); self.price.setValue(3500)
        self.price.setPrefix("Rs. "); self.price.setMinimumHeight(38)
        grid.addWidget(self.price,r,1)
        grid.addWidget(self._lbl("Status"),r,2)
        self.is_active = QCheckBox("Plan is Active")
        self.is_active.setChecked(True)
        self.is_active.setStyleSheet("QWidget { color:#F0F4FF; }")
        grid.addWidget(self.is_active,r,3); r+=1

        grid.addWidget(self._lbl("Description"),r,0)
        self.description = QTextEdit()
        self.description.setPlaceholderText("Describe plan features and inclusions...")
        self.description.setFixedHeight(90)
        grid.addWidget(self.description,r,1,1,3); r+=1

        # Preview
        self.preview_lbl = QLabel("")
        self.preview_lbl.setStyleSheet("QWidget { color:#00F5FF;font-size:13px; }")
        grid.addWidget(self.preview_lbl,r,0,1,4)
        self.duration.valueChanged.connect(self._update_preview)
        self.price.valueChanged.connect(self._update_preview)
        self._update_preview()

        main.addWidget(card); main.addStretch()
        scroll.setWidget(container)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

    def _update_preview(self):
        days = self.duration.value()
        price = self.price.value()
        per_day = price/days if days > 0 else 0
        self.preview_lbl.setText(f"📊  Rs. {per_day:.0f}/day  |  {days} days  |  Total: Rs. {price:,.0f}")

    def _load_data(self):
        p = membership_svc.get_plan_by_id(self._plan_id)
        if not p: return
        self.plan_name.setText(p[1] or "")
        self.duration.setValue(p[2] or 30)
        self.price.setValue(float(p[3] or 0))
        self.description.setPlainText(p[4] or "")
        self.is_active.setChecked(bool(p[5]))

    def _validate(self):
        if not self.plan_name.text().strip(): return False,"Plan name required."
        if self.duration.value() < 1:        return False,"Duration must be at least 1 day."
        if self.price.value() <= 0:          return False,"Price must be greater than 0."
        return True,""

    def _save(self):
        ok, msg = self._validate()
        if not ok:
            InfoDialog("Validation Error",msg,"error",self).exec(); return
        data = {
            "plan_name":    self.plan_name.text().strip(),
            "duration_days":self.duration.value(),
            "price":        self.price.value(),
            "description":  self.description.toPlainText().strip(),
            "is_active":    self.is_active.isChecked(),
        }
        if self._is_edit:
            result = membership_svc.update_plan(self._plan_id, data, self._session.user_id)
        else:
            result = membership_svc.create_plan(data, self._session.user_id)
        InfoDialog("Saved" if result["success"] else "Error",
                   result["message"],
                   "success" if result["success"] else "error", self).exec()
        if result["success"]: self.saved.emit()


# ── Assign Membership Form ─────────────────────────────────────────────────────
class AssignMembershipForm(QWidget):
    """Assign/renew a membership plan to a member with auto-expiry."""
    saved     = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, session, pre_member_id=None, parent=None):
        super().__init__(parent)
        self._session = session
        self._pre_member_id = pre_member_id
        self._plan_map = {}
        self.setStyleSheet("background:transparent;")
        self._setup_ui()
        self._populate()

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
        hdr.addWidget(QLabel("🔗  Assign / Renew Membership"))
        hdr.addStretch()
        save = QPushButton("✅ Assign Membership"); save.setObjectName("btnSuccess")
        save.setMinimumHeight(40); save.clicked.connect(self._save); hdr.addWidget(save)
        main.addLayout(hdr)

        card = QFrame()
        card.setStyleSheet("QFrame { background:rgba(255,255,255,0.05);border:1px solid rgba(0, 102, 255, 0.25);border-radius:16px; }")
        grid = QGridLayout(card)
        grid.setContentsMargins(28,24,28,28); grid.setSpacing(16)
        grid.setColumnStretch(1,1); grid.setColumnStretch(3,1)
        r=0

        grid.addWidget(self._lbl("Select Member",True),r,0)
        self.member_cb = QComboBox(); self.member_cb.setMinimumHeight(42)
        self.member_cb.addItem("— Select Member —", None)
        grid.addWidget(self.member_cb,r,1,1,3); r+=1

        grid.addWidget(self._lbl("Membership Plan",True),r,0)
        self.plan_cb = QComboBox(); self.plan_cb.setMinimumHeight(42)
        self.plan_cb.addItem("— Select Plan —", None)
        self.plan_cb.currentIndexChanged.connect(self._on_plan_changed)
        grid.addWidget(self.plan_cb,r,1,1,3); r+=1

        grid.addWidget(self._lbl("Start Date",True),r,0)
        self.start_date = QDateEdit(); self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd/MM/yyyy")
        self.start_date.setDate(QDate.currentDate()); self.start_date.setMinimumHeight(42)
        self.start_date.dateChanged.connect(self._on_plan_changed)
        grid.addWidget(self.start_date,r,1)

        grid.addWidget(self._lbl("Expiry Date (auto)"),r,2)
        self.expiry_date = QDateEdit(); self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setDisplayFormat("dd/MM/yyyy")
        self.expiry_date.setDate(QDate.currentDate().addDays(30))
        self.expiry_date.setMinimumHeight(42); self.expiry_date.setEnabled(False)
        grid.addWidget(self.expiry_date,r,3); r+=1

        # Summary card
        self.summary = QLabel("Select a plan to see membership details.")
        self.summary.setStyleSheet(
            "background:rgba(0,245,255,0.07);border:1px solid rgba(0,245,255,0.2);"
            "border-radius:10px;padding:14px;color:#00F5FF;font-size:14px;"
        )
        self.summary.setWordWrap(True)
        grid.addWidget(self.summary,r,0,1,4)

        main.addWidget(card); main.addStretch()
        scroll.setWidget(container)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

    def _populate(self):
        branch_id = self._session.branch_id
        members = member_svc.get_all_members(branch_id=branch_id, status="Active")
        for m in members:
            self.member_cb.addItem(f"{m[1]} ({m[2]})", m[0])
        if self._pre_member_id:
            idx = self.member_cb.findData(self._pre_member_id)
            if idx >= 0: self.member_cb.setCurrentIndex(idx)

        plans = membership_svc.get_plans_dropdown()
        for pid, pname, pdays, pprice in plans:
            self.plan_cb.addItem(f"{pname}  —  Rs. {pprice:,.0f}  ({pdays} days)", pid)
            self._plan_map[pid] = (pname, pdays, pprice)

    def _on_plan_changed(self):
        pid = self.plan_cb.currentData()
        if pid and pid in self._plan_map:
            pname, days, price = self._plan_map[pid]
            start = self.start_date.date().toPyDate()
            from services.membership_service import calculate_expiry
            exp = calculate_expiry(start, days)
            self.expiry_date.setDate(QDate(exp.year, exp.month, exp.day))
            self.summary.setText(
                f"📋  Plan: {pname}\n"
                f"💰  Price: Rs. {price:,.0f}\n"
                f"📅  Duration: {days} days\n"
                f"📆  Start: {start.strftime('%d %b %Y')}  →  Expires: {exp.strftime('%d %b %Y')}"
            )
        else:
            self.summary.setText("Select a plan to see membership details.")

    def _save(self):
        member_id = self.member_cb.currentData()
        plan_id   = self.plan_cb.currentData()
        if not member_id:
            InfoDialog("Error","Please select a member.","error",self).exec(); return
        if not plan_id:
            InfoDialog("Error","Please select a plan.","error",self).exec(); return

        dlg = ConfirmDialog(
            "Confirm Membership Assignment",
            f"Assign '{self.plan_cb.currentText()}'\nto the selected member?\n\nAny existing active membership will be expired.",
            "Assign Membership", "primary", self
        )
        if dlg.exec():
            result = membership_svc.assign_membership(
                member_id, plan_id,
                self.start_date.date().toPyDate(),
                self._session.user_id
            )
            InfoDialog("Result", result["message"],
                       "success" if result["success"] else "error", self).exec()
            if result["success"]: self.saved.emit()


# ── Module Container ──────────────────────────────────────────────────────────
class PlansModule(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setStyleSheet("background:transparent;")
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self._stack)

        self._list = PlansScreen(session)
        self._list.open_add_form.connect(self._show_add)
        self._list.open_edit_form.connect(self._show_edit)
        self._list.open_assign.connect(self._show_assign)
        self._stack.addWidget(self._list)
        self._stack.setCurrentWidget(self._list)

    def _show_add(self):
        form = PlanForm(self._session)
        form.saved.connect(self._back); form.cancelled.connect(self._back)
        self._stack.addWidget(form); self._stack.setCurrentWidget(form)

    def _show_edit(self, pid):
        form = PlanForm(self._session, plan_id=pid)
        form.saved.connect(self._back); form.cancelled.connect(self._back)
        self._stack.addWidget(form); self._stack.setCurrentWidget(form)

    def _show_assign(self):
        form = AssignMembershipForm(self._session)
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
