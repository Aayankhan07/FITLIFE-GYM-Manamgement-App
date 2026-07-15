"""FitLife — Diet Plans Module"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QLineEdit, QGridLayout,
    QDoubleSpinBox, QSpinBox, QTextEdit, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.components.glass_card import KPICard, StatusBadge, SectionHeader
from ui.components.data_table import DataTable
from ui.components.confirm_dialog import ConfirmDialog, InfoDialog
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
import services.diet_service as diet_svc
import services.member_service as member_svc
import services.trainer_service as trainer_svc
from config.constants import (
    PLAN_STATUSES, FITNESS_GOALS, MEAL_TYPES,
    ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER
)

_BTN = lambda label, color: f"""
    QPushButton{{background:rgba(0,0,0,0.2);border:1px solid {color};
    border-radius:6px;color:{color};font-size: 13px;padding:0 8px;min-height:28px;}}
    QPushButton:hover{{background:{color}22;}}"""


class DietPlansModule(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setStyleSheet("background:transparent;")
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background:transparent;")
        QVBoxLayout(self).addWidget(self._stack)
        self.layout().setContentsMargins(0,0,0,0)
        self._list = _DietList(session)
        self._list.open_add.connect(self._show_add)
        self._list.open_edit.connect(self._show_edit)
        self._list.open_detail.connect(self._show_detail)
        self._stack.addWidget(self._list)
        self._stack.setCurrentWidget(self._list)

    def _show_add(self):
        w = _DietForm(self._session)
        w.saved.connect(self._back); w.cancelled.connect(self._back)
        self._stack.addWidget(w); self._stack.setCurrentWidget(w)

    def _show_edit(self, pid):
        w = _DietForm(self._session, plan_id=pid)
        w.saved.connect(self._back); w.cancelled.connect(self._back)
        self._stack.addWidget(w); self._stack.setCurrentWidget(w)

    def _show_detail(self, pid):
        w = _DietDetail(self._session, pid)
        w.go_back.connect(self._back); w.go_edit.connect(self._show_edit)
        self._stack.addWidget(w); self._stack.setCurrentWidget(w)

    def _back(self):
        while self._stack.count() > 1:
            w = self._stack.widget(1); self._stack.removeWidget(w); w.deleteLater()
        self._stack.setCurrentWidget(self._list); self._list.refresh()

    def refresh(self):
        if hasattr(self._stack.currentWidget(), "refresh"):
            self._stack.currentWidget().refresh()


class _DietList(QWidget):
    open_add    = pyqtSignal()
    open_edit   = pyqtSignal(int)
    open_detail = pyqtSignal(int)

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self._branch_id = session.branch_id
        self.setStyleSheet("background:transparent;")
        self._build_ui()
        self._load()

    def _build_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;background:transparent;")
        c = QWidget(); c.setStyleSheet("background:transparent;")
        m = QVBoxLayout(c); m.setContentsMargins(28,24,28,24); m.setSpacing(18)

        hdr = QHBoxLayout()
        t = QLabel("🥗  Diet Plans"); t.setStyleSheet("font-size:26px;font-weight:900;color:#F0F4FF;")
        hdr.addWidget(t); hdr.addStretch()
        if self._session.role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER):
            b = QPushButton("➕ New Plan"); b.setObjectName("btnPrimary"); b.setMinimumHeight(40)
            b.clicked.connect(self.open_add.emit); hdr.addWidget(b)
        m.addLayout(hdr)

        krow = QHBoxLayout(); krow.setSpacing(14)
        self._k_total   = KPICard("Total Plans","—","📋","","#0066FF")
        self._k_active  = KPICard("Active","—","✅","","#00E676")
        self._k_pending = KPICard("Pending Review","—","⏳","","#FFB800")
        for k in [self._k_total, self._k_active, self._k_pending]: krow.addWidget(k)
        krow.addStretch(); m.addLayout(krow)

        ff = QFrame(); ff.setStyleSheet("background:rgba(255,255,255,0.04);border:1px solid rgba(0, 102, 255, 0.2);border-radius:12px;")
        fr = QHBoxLayout(ff); fr.setContentsMargins(16,10,16,10); fr.setSpacing(10)
        fr.addWidget(QLabel("Status:"))
        self._sf = QComboBox(); self._sf.setFixedHeight(34); self._sf.addItem("All",None)
        for s in PLAN_STATUSES: self._sf.addItem(s,s)
        self._sf.currentIndexChanged.connect(self._load); fr.addWidget(self._sf)
        fr.addStretch()
        rb = QPushButton("🔄"); rb.setObjectName("btnSecondary"); rb.setFixedHeight(34)
        rb.clicked.connect(self._load); fr.addWidget(rb)
        m.addWidget(ff)

        cols = ["ID","Member","Trainer","Plan Name","Goal","Calories/day","Status","Actions"]
        self.table = DataTable(cols)
        self.table.row_double_clicked.connect(
            lambda r: self.open_detail.emit(self.table._filtered_data[r][0])
            if r < len(self.table._filtered_data) else None)
        tc = QFrame(); tc.setStyleSheet("background:rgba(255,255,255,0.04);border:1px solid rgba(0, 102, 255, 0.2);border-radius:16px;")
        QVBoxLayout(tc).addWidget(self.table)
        m.addWidget(tc)

        self._overlay = LoadingOverlay(self)
        scroll.setWidget(c)
        QVBoxLayout(self).addWidget(scroll)
        self.layout().setContentsMargins(0,0,0,0)

    def _load(self):
        self._overlay.show_loading("Loading diet plans...")
        status = self._sf.currentData()
        role = self._session.role
        mid = None
        if role == ROLE_MEMBER:
            member = member_svc.get_member_by_user_id(self._session.user_id)
            mid = member[0] if member else None
        
        self._w = Worker(diet_svc.get_all_diet_plans, self._branch_id, mid, status)
        self._w.result.connect(self._on_data)
        self._w.error.connect(lambda e: self._overlay.hide_loading())
        self._w.start()

    def _on_data(self, plans):
        self._overlay.hide_loading()
        role = self._session.role
        mid = None
        if role == ROLE_MEMBER:
            member = member_svc.get_member_by_user_id(self._session.user_id)
            mid = member[0] if member else None
            
        stats = diet_svc.get_diet_plan_stats(self._branch_id, mid)
        self._k_total.set_value(str(stats["total"]))
        self._k_active.set_value(str(stats["active"]))
        self._k_pending.set_value(str(stats["pending"]))
        rows = [[p[0],p[1],p[2] or "—",p[3],p[4],f"{p[5]} kcal",p[6],""] for p in plans]
        self.table.set_data(rows)
        tw = self.table.table
        vis = plans[self.table._current_page*self.table._page_size:(self.table._current_page+1)*self.table._page_size]
        for ri, p in enumerate(vis):
            pid, st = p[0], p[6]
            cell = QWidget(); bl = QHBoxLayout(cell); bl.setContentsMargins(4,2,4,2); bl.setSpacing(4)
            for lbl, clr, fn in [
                ("👁 View","#00F5FF", lambda _, i=pid: self.open_detail.emit(i)),
                ("✏️ Edit","#0066FF", lambda _, i=pid: self.open_edit.emit(i)),
            ]:
                btn = QPushButton(lbl); btn.setStyleSheet(_BTN(lbl,clr)); btn.clicked.connect(fn); bl.addWidget(btn)
            tw.setCellWidget(ri,7,cell); tw.setCellWidget(ri,6,StatusBadge(st))

    def refresh(self): self._load()


class _DietDetail(QWidget):
    go_back = pyqtSignal()
    go_edit = pyqtSignal(int)

    def __init__(self, session, plan_id, parent=None):
        super().__init__(parent)
        self._session = session; self._plan_id = plan_id
        self.setStyleSheet("background:transparent;")
        self._build_ui(); self._load()

    def _build_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;background:transparent;")
        c = QWidget(); c.setStyleSheet("background:transparent;")
        m = QVBoxLayout(c); m.setContentsMargins(28,24,28,28); m.setSpacing(18)

        hdr = QHBoxLayout()
        back = QPushButton("← Back"); back.setObjectName("btnSecondary"); back.setFixedHeight(36)
        back.clicked.connect(self.go_back.emit); hdr.addWidget(back); hdr.addStretch()
        if self._session.role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER):
            edit = QPushButton("✏️ Edit Plan"); edit.setObjectName("btnPrimary"); edit.setFixedHeight(36)
            edit.clicked.connect(lambda: self.go_edit.emit(self._plan_id)); hdr.addWidget(edit)
        m.addLayout(hdr)

        hc = QFrame(); hc.setStyleSheet("background:rgba(0, 102, 255, 0.1);border:1px solid rgba(0, 102, 255, 0.4);border-radius:16px;")
        hl = QHBoxLayout(hc); hl.setContentsMargins(24,18,24,18); hl.setSpacing(20)
        iv = QVBoxLayout(); iv.setSpacing(4)
        self._title = QLabel("—"); self._title.setStyleSheet("font-size:20px;font-weight:900;color:#F0F4FF;")
        self._sub   = QLabel("—"); self._sub.setStyleSheet("font-size:13px;color:#9CA3AF;")
        self._badge = StatusBadge("Draft")
        for w in [self._title, self._sub, self._badge]: iv.addWidget(w)
        hl.addLayout(iv); hl.addStretch()
        kr = QHBoxLayout()
        self._k_cal   = KPICard("Calories","—","🔥","","#FF2D78")
        self._k_prot  = KPICard("Protein","—","💪","","#0066FF")
        self._k_carbs = KPICard("Carbs","—","🌾","","#FFB800")
        self._k_fat   = KPICard("Fat","—","🥑","","#00E676")
        for k in [self._k_cal,self._k_prot,self._k_carbs,self._k_fat]: k.setFixedWidth(150); kr.addWidget(k)
        hl.addLayout(kr); m.addWidget(hc)

        # Add meal row
        if self._session.role in (ROLE_ADMIN,ROLE_MANAGER,ROLE_TRAINER):
            af = QFrame(); af.setStyleSheet("background:rgba(0,230,118,0.05);border:1px solid rgba(0,230,118,0.2);border-radius:12px;")
            ag = QGridLayout(af); ag.setContentsMargins(16,12,16,12); ag.setSpacing(10)
            self._meal_type = QComboBox(); self._meal_type.setMinimumHeight(36)
            for mt in MEAL_TYPES: self._meal_type.addItem(mt,mt)
            self._food_item = QLineEdit(); self._food_item.setPlaceholderText("Food item*"); self._food_item.setMinimumHeight(36)
            self._qty    = QSpinBox(); self._qty.setRange(1,2000); self._qty.setValue(100); self._qty.setSuffix("g"); self._qty.setMinimumHeight(36)
            self._kcal   = QSpinBox(); self._kcal.setRange(0,5000); self._kcal.setValue(0); self._kcal.setSuffix(" kcal"); self._kcal.setMinimumHeight(36)
            self._prot   = QDoubleSpinBox(); self._prot.setRange(0,500); self._prot.setSuffix("g"); self._prot.setMinimumHeight(36)
            self._carbs  = QDoubleSpinBox(); self._carbs.setRange(0,500); self._carbs.setSuffix("g"); self._carbs.setMinimumHeight(36)
            self._fat    = QDoubleSpinBox(); self._fat.setRange(0,200); self._fat.setSuffix("g"); self._fat.setMinimumHeight(36)
            ag.addWidget(QLabel("Meal:"),0,0); ag.addWidget(self._meal_type,0,1)
            ag.addWidget(QLabel("Food:"),0,2); ag.addWidget(self._food_item,0,3)
            ag.addWidget(QLabel("Qty:"),0,4); ag.addWidget(self._qty,0,5)
            ag.addWidget(QLabel("kcal:"),1,0); ag.addWidget(self._kcal,1,1)
            ag.addWidget(QLabel("Protein:"),1,2); ag.addWidget(self._prot,1,3)
            ag.addWidget(QLabel("Carbs:"),1,4); ag.addWidget(self._carbs,1,5)
            ag.addWidget(QLabel("Fat:"),2,0); ag.addWidget(self._fat,2,1)
            ab = QPushButton("➕ Add Meal"); ab.setObjectName("btnPrimary"); ab.setFixedHeight(34)
            ab.clicked.connect(self._add_meal); ag.addWidget(ab,2,2,1,4)
            m.addWidget(af)

        m.addWidget(SectionHeader("🍽️  Meal Schedule"))
        self._meal_table = QTableWidget()
        self._meal_table.setColumnCount(7)
        self._meal_table.setHorizontalHeaderLabels(["Meal Type","Food Item","Qty","Calories","Protein","Carbs","Fat"])
        self._meal_table.verticalHeader().setVisible(False)
        self._meal_table.horizontalHeader().setStretchLastSection(True)
        self._meal_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._meal_table.setStyleSheet("QTableWidget{background:transparent;border:none;color:#F0F4FF;}QTableWidget::item{padding:8px;border-bottom:1px solid rgba(0, 102, 255, 0.15);}QHeaderView::section{background:rgba(0, 102, 255, 0.2);color:#00F5FF;padding:8px;border:none;font-weight:bold;}")
        m.addWidget(self._meal_table)
        m.addStretch(); scroll.setWidget(c)
        QVBoxLayout(self).addWidget(scroll); self.layout().setContentsMargins(0,0,0,0)

    def _load(self):
        p = diet_svc.get_diet_plan_by_id(self._plan_id)
        if not p: return
        self._title.setText(p[3])
        self._sub.setText(f"Member: {p[12]}  |  Trainer: {p[13] or '—'}  |  Goal: {p[4]}")
        self._badge.set_status(p[9])
        self._k_cal.set_value(f"{p[5]} kcal")
        self._k_prot.set_value(f"{p[6] or 0}g")
        self._k_carbs.set_value(f"{p[7] or 0}g")
        self._k_fat.set_value(f"{p[8] or 0}g")
        meals = diet_svc.get_meals(self._plan_id)
        self._meal_table.setRowCount(0)
        for meal in meals:
            r = self._meal_table.rowCount(); self._meal_table.insertRow(r)
            for ci, v in enumerate([meal[1],meal[2],f"{meal[3]}g",f"{meal[4]} kcal",f"{meal[5] or 0}g",f"{meal[6] or 0}g",f"{meal[7] or 0}g"]):
                self._meal_table.setItem(r,ci,QTableWidgetItem(str(v)))

    def _add_meal(self):
        food = self._food_item.text().strip()
        if not food: InfoDialog("Error","Food item required.","error",self).exec(); return
        result = diet_svc.add_meal(self._plan_id, {
            "meal_type": self._meal_type.currentData(),
            "food_item": food, "quantity_g": self._qty.value(),
            "calories":  self._kcal.value(), "protein_g": self._prot.value(),
            "carbs_g":   self._carbs.value(), "fat_g": self._fat.value(),
        })
        if result["success"]: self._food_item.clear(); self._load()
        else: InfoDialog("Error",result["message"],"error",self).exec()


class _DietForm(QWidget):
    saved = pyqtSignal(); cancelled = pyqtSignal()

    def __init__(self, session, plan_id=None, parent=None):
        super().__init__(parent)
        self._session = session; self._plan_id = plan_id; self._is_edit = plan_id is not None
        self.setStyleSheet("background:transparent;")
        self._build_ui(); self._populate()
        if self._is_edit: self._load()

    def _inp(self, ph=""): f=QLineEdit(); f.setPlaceholderText(ph); f.setMinimumHeight(38); return f
    def _lbl(self, t): l=QLabel(t); l.setStyleSheet("color:#9CA3AF;font-size:13px;"); return l

    def _build_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;background:transparent;")
        c = QWidget(); c.setStyleSheet("background:transparent;")
        m = QVBoxLayout(c); m.setContentsMargins(28,24,28,28); m.setSpacing(18)

        hdr = QHBoxLayout()
        back = QPushButton("← Back"); back.setObjectName("btnSecondary"); back.setFixedHeight(36)
        back.clicked.connect(self.cancelled.emit); hdr.addWidget(back)
        hdr.addWidget(QLabel(f"{'✏️ Edit' if self._is_edit else '➕ New'} Diet Plan")); hdr.addStretch()
        sv = QPushButton("💾 Save Plan"); sv.setObjectName("btnPrimary"); sv.setMinimumHeight(40)
        sv.clicked.connect(self._save); hdr.addWidget(sv)
        m.addLayout(hdr)

        card = QFrame(); card.setStyleSheet("background:rgba(255,255,255,0.05);border:1px solid rgba(0, 102, 255, 0.25);border-radius:16px;")
        g = QGridLayout(card); g.setContentsMargins(28,24,28,28); g.setSpacing(14)
        g.setColumnStretch(1,1); g.setColumnStretch(3,1)

        g.addWidget(self._lbl("Plan Name *"),0,0); self._name=self._inp("e.g. High-Protein Lean Cut"); g.addWidget(self._name,0,1)
        g.addWidget(self._lbl("Goal"),0,2); self._goal=QComboBox(); self._goal.setMinimumHeight(38)
        for gg in FITNESS_GOALS: self._goal.addItem(gg,gg)
        g.addWidget(self._goal,0,3)

        g.addWidget(self._lbl("Daily Calories (kcal)"),1,0)
        self._cal=QSpinBox(); self._cal.setRange(500,10000); self._cal.setValue(2000); self._cal.setMinimumHeight(38); g.addWidget(self._cal,1,1)
        g.addWidget(self._lbl("Status"),1,2); self._status=QComboBox(); self._status.setMinimumHeight(38)
        for s in PLAN_STATUSES: self._status.addItem(s,s)
        if self._session.role in (ROLE_ADMIN, ROLE_MANAGER):
            idx = self._status.findData("Pending Verification")
            if idx >= 0: self._status.setCurrentIndex(idx)
        g.addWidget(self._status,1,3)

        g.addWidget(self._lbl("Protein (g/day)"),2,0)
        self._prot=QSpinBox(); self._prot.setRange(0,500); self._prot.setValue(150); self._prot.setMinimumHeight(38); g.addWidget(self._prot,2,1)
        g.addWidget(self._lbl("Carbs (g/day)"),2,2)
        self._carbs=QSpinBox(); self._carbs.setRange(0,1000); self._carbs.setValue(200); self._carbs.setMinimumHeight(38); g.addWidget(self._carbs,2,3)

        g.addWidget(self._lbl("Fat (g/day)"),3,0)
        self._fat=QSpinBox(); self._fat.setRange(0,300); self._fat.setValue(65); self._fat.setMinimumHeight(38); g.addWidget(self._fat,3,1)

        g.addWidget(self._lbl("Member *"),4,0); self._member=QComboBox(); self._member.setMinimumHeight(38); g.addWidget(self._member,4,1)
        g.addWidget(self._lbl("Assigned Trainer"),4,2); self._trainer=QComboBox(); self._trainer.setMinimumHeight(38)
        self._trainer.addItem("— None —",None); g.addWidget(self._trainer,4,3)

        g.addWidget(self._lbl("Notes"),5,0); self._notes=QTextEdit(); self._notes.setFixedHeight(80); g.addWidget(self._notes,5,1,1,3)

        m.addWidget(card); m.addStretch(); scroll.setWidget(c)
        QVBoxLayout(self).addWidget(scroll); self.layout().setContentsMargins(0,0,0,0)

    def _populate(self):
        bid = self._session.branch_id
        self._member.clear(); self._member.addItem("— Select —",None)
        for mm in member_svc.get_all_members(branch_id=bid,status="Active"):
            self._member.addItem(f"{mm[1]} ({mm[2]})",mm[0])
        if bid:
            for t in trainer_svc.get_trainers_for_branch(bid):
                self._trainer.addItem(f"{t[1]} ({t[2]})",t[0])

    def _load(self):
        p = diet_svc.get_diet_plan_by_id(self._plan_id)
        if not p: return
        self._name.setText(p[3] or "")
        idx=self._goal.findData(p[4]); self._goal.setCurrentIndex(max(0,idx))
        self._cal.setValue(p[5] or 2000); self._prot.setValue(p[6] or 150)
        self._carbs.setValue(p[7] or 200); self._fat.setValue(p[8] or 65)
        idx=self._status.findData(p[9]); self._status.setCurrentIndex(max(0,idx))
        idx=self._member.findData(p[1]); self._member.setCurrentIndex(max(0,idx))
        if p[2]:
            idx=self._trainer.findData(p[2]); self._trainer.setCurrentIndex(max(0,idx))
        self._notes.setPlainText(p[10] or "")

    def _save(self):
        if not self._name.text().strip(): InfoDialog("Error","Plan name required.","error",self).exec(); return
        if not self._member.currentData(): InfoDialog("Error","Select a member.","error",self).exec(); return
        data = {
            "plan_name": self._name.text().strip(), "goal": self._goal.currentData(),
            "daily_calories": self._cal.value(), "protein_g": self._prot.value(),
            "carbs_g": self._carbs.value(), "fat_g": self._fat.value(),
            "status": self._status.currentData(), "member_id": self._member.currentData(),
            "trainer_id": self._trainer.currentData(), "notes": self._notes.toPlainText().strip(),
        }
        result = diet_svc.update_diet_plan(self._plan_id,data,self._session.user_id) if self._is_edit \
                 else diet_svc.create_diet_plan(data,self._session.user_id)
        InfoDialog("Result",result["message"],"success" if result["success"] else "error",self).exec()
        if result["success"]: self.saved.emit()
