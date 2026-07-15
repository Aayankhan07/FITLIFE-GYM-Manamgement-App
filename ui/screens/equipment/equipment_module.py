"""
FitLife — Equipment Module
Full CRUD: inventory list, add/edit form, maintenance tracker.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QLineEdit, QGridLayout,
    QDoubleSpinBox, QSpinBox, QDateEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QStackedWidget, QHeaderView
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from ui.components.glass_card import KPICard, StatusBadge, SectionHeader
from ui.components.data_table import DataTable
from ui.components.confirm_dialog import ConfirmDialog, InfoDialog
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
import services.equipment_service as equip_svc
import services.branch_service as branch_svc
from config.constants import (
    EQUIPMENT_CATEGORIES, EQUIPMENT_CONDITIONS, ROLE_ADMIN, ROLE_MANAGER
)


# ── Equipment List ─────────────────────────────────────────────────────────────
class EquipmentScreen(QWidget):
    open_add    = pyqtSignal()
    open_edit   = pyqtSignal(int)

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
        main = QVBoxLayout(container); main.setContentsMargins(28,24,28,24); main.setSpacing(20)

        hdr = QHBoxLayout()
        title = QLabel("🏋️  Equipment Inventory")
        title.setStyleSheet("font-size:26px;font-weight:900;color:#F0F4FF;")
        hdr.addWidget(title); hdr.addStretch()
        self.add_btn = QPushButton("➕  Add Equipment")
        self.add_btn.setObjectName("btnPrimary"); self.add_btn.setMinimumHeight(40)
        self.add_btn.clicked.connect(self.open_add.emit); hdr.addWidget(self.add_btn)
        main.addLayout(hdr)

        # KPIs
        krow = QHBoxLayout(); krow.setSpacing(14)
        self._kpi_total   = KPICard("Total Items",  "—","📦","","#0066FF")
        self._kpi_active  = KPICard("Active",       "—","✅","","#00E676")
        self._kpi_maint   = KPICard("Maintenance",  "—","🔧","","#FFB800")
        self._kpi_value   = KPICard("Total Value",  "—","💰","","#00F5FF")
        for k in [self._kpi_total, self._kpi_active, self._kpi_maint, self._kpi_value]:
            krow.addWidget(k)
        main.addLayout(krow)

        # Filters
        fbar = QFrame()
        fbar.setStyleSheet("background:rgba(255,255,255,0.04);border:1px solid rgba(0, 102, 255, 0.2);border-radius:12px;")
        fr = QHBoxLayout(fbar); fr.setContentsMargins(16,10,16,10); fr.setSpacing(12)
        fr.addWidget(QLabel("Category:"))
        self.cat_filter = QComboBox(); self.cat_filter.setFixedHeight(34)
        self.cat_filter.addItem("All",None)
        for c in EQUIPMENT_CATEGORIES: self.cat_filter.addItem(c,c)
        self.cat_filter.currentIndexChanged.connect(self._load_data)
        fr.addWidget(self.cat_filter)
        fr.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox(); self.status_filter.setFixedHeight(34)
        self.status_filter.addItem("All",None)
        self.status_filter.addItems(["Active", "Inactive", "Maintenance"])
        self.status_filter.currentIndexChanged.connect(self._load_data)
        fr.addWidget(self.status_filter)
        self.search = QLineEdit(); self.search.setPlaceholderText("Search name...")
        self.search.setFixedHeight(34); self.search.returnPressed.connect(self._load_data)
        fr.addWidget(self.search); fr.addStretch()
        ref = QPushButton("🔄 Refresh"); ref.setObjectName("btnSecondary"); ref.setFixedHeight(34)
        ref.clicked.connect(self._load_data); fr.addWidget(ref)
        main.addWidget(fbar)

        cols = ["ID","Name","Category","Qty","Price (Rs.)","Status","Branch","Actions"]
        self.table = DataTable(cols)
        tc = QFrame()
        tc.setStyleSheet("background:rgba(255,255,255,0.04);border:1px solid rgba(0, 102, 255, 0.2);border-radius:16px;")
        tcl = QVBoxLayout(tc); tcl.setContentsMargins(16,16,16,16); tcl.addWidget(self.table)
        main.addWidget(tc)

        self._overlay = LoadingOverlay(self)
        scroll.setWidget(container)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

    def _load_data(self):
        self._overlay.show_loading("Loading inventory...")
        cat  = self.cat_filter.currentData()
        status = self.status_filter.currentData()
        srch = self.search.text().strip() or None
        self._worker = Worker(self._fetch, cat, status, srch)
        self._worker.result.connect(self._on_loaded)
        self._worker.error.connect(lambda e: self._overlay.hide_loading())
        self._worker.start()

    def _fetch(self, cat, status, srch):
        items = equip_svc.get_all_equipment(self._branch_id, cat, status, srch)
        stats = equip_svc.get_equipment_stats(self._branch_id)
        return {"items": items, "stats": stats}

    def _on_loaded(self, data):
        self._overlay.hide_loading()
        s = data["stats"]
        self._kpi_total.set_value(str(s.get("total_items", 0)))
        
        # Calculate active/maintenance manually from items for now since stats schema might differ
        active_count = sum(1 for i in data["items"] if i[6] == "Active")
        maint_count = sum(1 for i in data["items"] if i[6] == "Maintenance")
        
        self._kpi_active.set_value(str(active_count))
        self._kpi_maint.set_value(str(maint_count))
        self._kpi_value.set_value(f"Rs. {s.get('total_value', 0):,.0f}")

        items = data["items"]
        rows = []
        for e in items:
            # e[0]=id, e[1]=name, e[2]=category, e[3]=qty, e[4]=purch_date, e[5]=purch_price, e[6]=status, e[7]=branch_name, e[8]=branch_id
            price_str = f"{float(e[5]):,.0f}" if e[5] else "—"
            rows.append([e[0], e[1], e[2], e[3], price_str, e[6], e[7], ""])
        self.table.set_data(rows)
        self._inject_buttons(items)

    def _inject_buttons(self, items):
        tw = self.table.table
        visible = items[
            self.table._current_page*self.table._page_size:
            (self.table._current_page+1)*self.table._page_size
        ]
        for r_idx, e in enumerate(visible):
            eid = e[0]
            cell = QWidget(); bl = QHBoxLayout(cell)
            bl.setContentsMargins(4,2,4,2); bl.setSpacing(4)
            for label, bg1, bg2, txt_color, hover1, hover2 in [
                ("✏ Edit",   "#0066FF", "#004BCC", "#FFFFFF", "#3B82F6", "#0066FF"),
                ("🗑 Del",   "#FF2D78", "#C0155A", "#FFFFFF", "#FF5294", "#FF2D78"),
            ]:
                btn = QPushButton(label); btn.setFixedHeight(32)
                btn.setStyleSheet(
                    f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                    f"stop:0 {bg1},stop:1 {bg2});"
                    f"border:none;border-radius:6px;color:{txt_color};"
                    f"font-size: 13px;font-weight:600;padding:0 8px;}}"
                    f"QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                    f"stop:0 {hover1},stop:1 {hover2});}}"
                )
                bl.addWidget(btn)
            # wire up buttons by index
            btns_in_cell = [bl.itemAt(i).widget() for i in range(bl.count())]
            btns_in_cell[0].clicked.connect(lambda _, i=eid: self.open_edit.emit(i))
            btns_in_cell[1].clicked.connect(lambda _, i=eid, n=e[1]: self._confirm_delete(i,n))
            tw.setCellWidget(r_idx, 7, cell)
            # Status badge
            stat_badge = StatusBadge(e[6])
            tw.setCellWidget(r_idx, 5, stat_badge)

    def _confirm_delete(self, eid, name):
        dlg = ConfirmDialog("Delete Equipment", f"Delete '{name}'?", "Delete","danger",self)
        if dlg.exec():
            result = equip_svc.delete_equipment(eid, self._session.user_id)
            InfoDialog("Result", result["message"],
                       "success" if result["success"] else "error", self).exec()
            if result["success"]: self._load_data()

    def refresh(self): self._load_data()


# ── Equipment Form ─────────────────────────────────────────────────────────────
class EquipmentForm(QWidget):
    saved     = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, session, equip_id=None, parent=None):
        super().__init__(parent)
        self._session = session
        self._equip_id = equip_id
        self._is_edit  = equip_id is not None
        self.setStyleSheet("background:transparent;")
        self._setup_ui()
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
        hdr.addWidget(QLabel(f"{'✏️ Edit' if self._is_edit else '➕ Add'} Equipment"))
        hdr.addStretch()
        save = QPushButton("💾 Save"); save.setObjectName("btnPrimary")
        save.setMinimumHeight(40); save.clicked.connect(self._save); hdr.addWidget(save)
        main.addLayout(hdr)

        card = QFrame()
        card.setStyleSheet("background:rgba(255,255,255,0.05);border:1px solid rgba(0, 102, 255, 0.25);border-radius:16px;")
        grid = QGridLayout(card); grid.setContentsMargins(28,24,28,28); grid.setSpacing(14)
        grid.setColumnStretch(1,1); grid.setColumnStretch(3,1); r=0

        grid.addWidget(self._lbl("Equipment Name",True),r,0)
        self.name = self._inp("e.g. Treadmill Pro X"); grid.addWidget(self.name,r,1)
        grid.addWidget(self._lbl("Category",True),r,2)
        self.cat_cb = QComboBox(); self.cat_cb.setMinimumHeight(38)
        for c in EQUIPMENT_CATEGORIES: self.cat_cb.addItem(c,c)
        grid.addWidget(self.cat_cb,r,3); r+=1

        grid.addWidget(self._lbl("Quantity"),r,0)
        self.qty = QSpinBox(); self.qty.setRange(1,999); self.qty.setValue(1); self.qty.setMinimumHeight(38)
        grid.addWidget(self.qty,r,1)
        grid.addWidget(self._lbl("Status"),r,2)
        self.status_cb = QComboBox(); self.status_cb.setMinimumHeight(38)
        self.status_cb.addItems(["Active", "Inactive", "Maintenance"])
        grid.addWidget(self.status_cb,r,3); r+=1

        grid.addWidget(self._lbl("Purchase Price (Rs.)"),r,0)
        self.price = QDoubleSpinBox(); self.price.setRange(0,9999999); self.price.setValue(0)
        self.price.setPrefix("Rs. "); self.price.setMinimumHeight(38)
        grid.addWidget(self.price,r,1)
        grid.addWidget(self._lbl("Purchase Date"),r,2)
        self.purchase_date = QDateEdit(); self.purchase_date.setCalendarPopup(True)
        self.purchase_date.setDisplayFormat("dd/MM/yyyy"); self.purchase_date.setDate(QDate.currentDate())
        self.purchase_date.setMinimumHeight(38); grid.addWidget(self.purchase_date,r,3); r+=1

        grid.addWidget(self._lbl("Branch",True),r,0)
        self.branch_cb = QComboBox(); self.branch_cb.setMinimumHeight(38)
        for bid, bname in branch_svc.get_all_branches_dropdown():
            self.branch_cb.addItem(bname,bid)
        if self._session.branch_id:
            idx = self.branch_cb.findData(self._session.branch_id)
            if idx>=0: self.branch_cb.setCurrentIndex(idx)
            if self._session.role == ROLE_MANAGER: self.branch_cb.setEnabled(False)
        grid.addWidget(self.branch_cb,r,1, 1, 3); r+=1

        main.addWidget(card); main.addStretch()
        scroll.setWidget(container)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

    def _load_data(self):
        # schema: e.id, e.branch_id, e.name, e.category, e.quantity, e.purchase_date, e.purchase_price, e.status, e.condition, e.next_maintenance_date, b.branch_name
        e = equip_svc.get_equipment_by_id(self._equip_id)
        if not e: return
        self.name.setText(e[2] or "")
        idx=self.cat_cb.findData(e[3]); self.cat_cb.setCurrentIndex(max(0,idx))
        self.qty.setValue(int(e[4] or 1))
        if e[5]: self.purchase_date.setDate(QDate(e[5].year,e[5].month,e[5].day))
        if e[6]: self.price.setValue(float(e[6]))
        idx=self.status_cb.findText(e[7] or "Active"); self.status_cb.setCurrentIndex(max(0,idx))
        idx=self.branch_cb.findData(e[1]); self.branch_cb.setCurrentIndex(max(0,idx))

    def _save(self):
        if not self.name.text().strip():
            InfoDialog("Error","Equipment name required.","error",self).exec(); return
        if not self.branch_cb.currentData():
            InfoDialog("Error","Branch required.","error",self).exec(); return
        data = {
            "branch_id":        self.branch_cb.currentData(),
            "name":             self.name.text().strip(),
            "category":         self.cat_cb.currentData(),
            "status":           self.status_cb.currentText(),
            "purchase_date":    self.purchase_date.date().toPyDate(),
            "purchase_price":   self.price.value(),
            "quantity":         self.qty.value(),
        }
        if self._is_edit:
            result = equip_svc.update_equipment(self._equip_id, data, self._session.user_id)
        else:
            result = equip_svc.create_equipment(data, self._session.user_id)
        InfoDialog("Result", result["message"],
                   "success" if result["success"] else "error", self).exec()
        if result["success"]: self.saved.emit()


# ── Module Container ──────────────────────────────────────────────────────────
class EquipmentModule(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setStyleSheet("background:transparent;")
        self._stack = QStackedWidget(); self._stack.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.addWidget(self._stack)
        self._list = EquipmentScreen(session)
        self._list.open_add.connect(self._show_add)
        self._list.open_edit.connect(self._show_edit)
        self._stack.addWidget(self._list); self._stack.setCurrentWidget(self._list)

    def _show_add(self):
        form = EquipmentForm(self._session)
        form.saved.connect(self._back); form.cancelled.connect(self._back)
        self._stack.addWidget(form); self._stack.setCurrentWidget(form)

    def _show_edit(self, eid):
        form = EquipmentForm(self._session, equip_id=eid)
        form.saved.connect(self._back); form.cancelled.connect(self._back)
        self._stack.addWidget(form); self._stack.setCurrentWidget(form)

    def _back(self):
        while self._stack.count() > 1:
            w = self._stack.widget(1); self._stack.removeWidget(w); w.deleteLater()
        self._stack.setCurrentWidget(self._list); self._list.refresh()

    def refresh(self):
        if hasattr(self._stack.currentWidget(), "refresh"):
            self._stack.currentWidget().refresh()


# ── Maintenance Log Dialog ─────────────────────────────────────────────────────
from PyQt6.QtWidgets import QDialog

class MaintenanceLogDialog(QDialog):
    def __init__(self, equip_id, user_id, parent=None):
        super().__init__(parent)
        self._equip_id = equip_id
        self._user_id  = user_id
        self.setWindowTitle("Log Maintenance")
        self.setMinimumWidth(420)
        self.setStyleSheet("background:#0D1B2A; color:#F0F4FF;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24,20,24,20); layout.setSpacing(14)
        layout.addWidget(QLabel("🔧  Log Equipment Maintenance"))

        grid = QGridLayout(); grid.setSpacing(12); grid.setColumnStretch(1,1)
        grid.addWidget(QLabel("Maintenance Date:"),0,0)
        self.maint_date = QDateEdit(); self.maint_date.setCalendarPopup(True)
        self.maint_date.setDisplayFormat("dd/MM/yyyy")
        self.maint_date.setDate(QDate.currentDate()); self.maint_date.setMinimumHeight(38)
        grid.addWidget(self.maint_date,0,1)

        grid.addWidget(QLabel("Notes:"),1,0)
        self.notes = QLineEdit(); self.notes.setPlaceholderText("What was serviced?")
        self.notes.setMinimumHeight(36); grid.addWidget(self.notes,1,1)
        layout.addLayout(grid)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        cancel = QPushButton("Cancel"); cancel.setFixedHeight(36)
        cancel.clicked.connect(self.reject); btn_row.addWidget(cancel)
        save = QPushButton("✅ Log Maintenance")
        save.setStyleSheet("QPushButton{background:#0066FF;border:none;border-radius:10px;color:#fff;font-size:14px;padding:0 20px;}QPushButton:hover{background:#3B82F6;}")
        save.setFixedHeight(36); save.clicked.connect(self._save); btn_row.addWidget(save)
        layout.addLayout(btn_row)

    def _save(self):
        result = equip_svc.log_maintenance(
            self._equip_id,
            self.maint_date.date().toPyDate(),
            self.notes.text().strip(),
            self._user_id
        )
        InfoDialog("Result", result["message"],
                   "success" if result["success"] else "error", self).exec()
        if result["success"]: self.accept()
