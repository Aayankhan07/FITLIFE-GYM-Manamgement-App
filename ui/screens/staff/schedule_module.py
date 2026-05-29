"""FitLife — Scheduling Module (Phase 5)
Trainer schedule: create slots, book members, mark complete, cancel."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QLineEdit, QGridLayout,
    QTimeEdit, QDateEdit, QTextEdit, QStackedWidget, QDialog
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal

from ui.components.glass_card import KPICard, StatusBadge, SectionHeader
from ui.components.data_table import DataTable
from ui.components.confirm_dialog import ConfirmDialog, InfoDialog
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
import services.schedule_service as sched_svc
import services.trainer_service as trainer_svc
import services.member_service as member_svc
import services.branch_service as branch_svc
from services.schedule_service import SLOT_STATUSES, CLASS_TYPES
from config.constants import ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER

_P = lambda c: (f"QPushButton{{background:rgba(0,0,0,0.2);border:1px solid {c};"
                f"border-radius:6px;color:{c};font-size: 13px;padding:0 8px;min-height:28px;}}"
                f"QPushButton:hover{{background:{c}22;}}")


class ScheduleModule(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setStyleSheet("background:transparent;")
        self._stack = QStackedWidget(); self._stack.setStyleSheet("background:transparent;")
        QVBoxLayout(self).addWidget(self._stack); self.layout().setContentsMargins(0,0,0,0)
        self._list = _ScheduleList(session)
        self._list.open_add.connect(self._show_add)
        self._list.open_edit.connect(self._show_edit)
        self._stack.addWidget(self._list); self._stack.setCurrentWidget(self._list)

    def _show_add(self):
        w = _SlotForm(self._session)
        w.saved.connect(self._back); w.cancelled.connect(self._back)
        self._stack.addWidget(w); self._stack.setCurrentWidget(w)

    def _show_edit(self, sid):
        w = _SlotForm(self._session, slot_id=sid)
        w.saved.connect(self._back); w.cancelled.connect(self._back)
        self._stack.addWidget(w); self._stack.setCurrentWidget(w)

    def _back(self):
        while self._stack.count() > 1:
            w = self._stack.widget(1); self._stack.removeWidget(w); w.deleteLater()
        self._stack.setCurrentWidget(self._list); self._list.refresh()

    def refresh(self):
        if hasattr(self._stack.currentWidget(), "refresh"):
            self._stack.currentWidget().refresh()


class _ScheduleList(QWidget):
    open_add  = pyqtSignal()
    open_edit = pyqtSignal(int)

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session; self._branch_id = session.branch_id
        self.setStyleSheet("background:transparent;")
        self._build_ui(); self._load()

    def _build_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;background:transparent;")
        c = QWidget(); c.setStyleSheet("background:transparent;")
        m = QVBoxLayout(c); m.setContentsMargins(28,24,28,24); m.setSpacing(18)

        # Header
        hdr = QHBoxLayout()
        t = QLabel("📅  Training Schedule"); t.setStyleSheet("font-size:26px;font-weight:900;color:#F0F4FF;")
        hdr.addWidget(t); hdr.addStretch()
        if self._session.role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER):
            b = QPushButton("➕ New Slot"); b.setObjectName("btnPrimary"); b.setMinimumHeight(40)
            b.clicked.connect(self.open_add.emit); hdr.addWidget(b)
        m.addLayout(hdr)

        # KPIs
        kr = QHBoxLayout(); kr.setSpacing(14)
        self._k_total  = KPICard("Total Slots","—","📋","","#7C3AED")
        self._k_booked = KPICard("Booked","—","✅","","#00E676")
        self._k_avail  = KPICard("Available","—","🕐","","#00F5FF")
        self._k_done   = KPICard("Completed","—","🏆","","#FFB800")
        for k in [self._k_total,self._k_booked,self._k_avail,self._k_done]: kr.addWidget(k)
        m.addLayout(kr)

        # Date + status filters
        ff = QFrame(); ff.setStyleSheet("background:rgba(255,255,255,0.04);border:1px solid rgba(124,58,237,0.2);border-radius:12px;")
        fr = QHBoxLayout(ff); fr.setContentsMargins(16,10,16,10); fr.setSpacing(10)
        fr.addWidget(QLabel("Date:"))
        self._date = QDateEdit(); self._date.setCalendarPopup(True)
        self._date.setDisplayFormat("dd/MM/yyyy"); self._date.setDate(QDate.currentDate())
        self._date.setFixedHeight(34); self._date.dateChanged.connect(self._load)
        fr.addWidget(self._date)
        all_date = QPushButton("All Dates"); all_date.setFixedHeight(34); all_date.setObjectName("btnSecondary")
        all_date.clicked.connect(lambda: [self._date.setDate(QDate(1900,1,1)), self._load_all()]); fr.addWidget(all_date)
        fr.addWidget(QLabel("Status:"))
        self._sf = QComboBox(); self._sf.setFixedHeight(34); self._sf.addItem("All",None)
        for s in SLOT_STATUSES: self._sf.addItem(s,s)
        self._sf.currentIndexChanged.connect(self._load); fr.addWidget(self._sf)

        # Trainer filter (admin/manager)
        if self._session.role in (ROLE_ADMIN, ROLE_MANAGER):
            fr.addWidget(QLabel("Trainer:"))
            self._tf = QComboBox(); self._tf.setFixedHeight(34); self._tf.addItem("All Trainers",None)
            if self._branch_id:
                for t in trainer_svc.get_trainers_for_branch(self._branch_id):
                    self._tf.addItem(t[1],t[0])
            self._tf.currentIndexChanged.connect(self._load); fr.addWidget(self._tf)
        else:
            self._tf = None

        fr.addStretch()
        rb = QPushButton("🔄"); rb.setObjectName("btnSecondary"); rb.setFixedHeight(34)
        rb.clicked.connect(self._load); fr.addWidget(rb)
        m.addWidget(ff)

        cols = ["ID","Trainer","Member","Date","Start","End","Type","Status","Notes","Actions"]
        self.table = DataTable(cols)
        tc = QFrame(); tc.setStyleSheet("background:rgba(255,255,255,0.04);border:1px solid rgba(124,58,237,0.2);border-radius:16px;")
        QVBoxLayout(tc).addWidget(self.table); m.addWidget(tc)

        self._overlay = LoadingOverlay(self)
        scroll.setWidget(c); QVBoxLayout(self).addWidget(scroll); self.layout().setContentsMargins(0,0,0,0)

    def _load(self):
        self._overlay.show_loading("Loading schedule...")
        d = self._date.date()
        slot_date = d.toPyDate() if d.year() > 1900 else None
        status = self._sf.currentData()
        tid = self._tf.currentData() if self._tf else None
        if self._session.role == ROLE_TRAINER:
            t = trainer_svc.get_trainer_by_user_id(self._session.user_id)
            tid = t[0] if t else None
        self._w = Worker(sched_svc.get_schedule, self._branch_id, tid, slot_date, status)
        self._w.result.connect(self._on_data)
        self._w.error.connect(lambda e: self._overlay.hide_loading())
        self._w.start()

    def _load_all(self): self._load()

    def _on_data(self, slots):
        self._overlay.hide_loading()
        d = self._date.date()
        sd = d.toPyDate() if d.year() > 1900 else None
        stats = sched_svc.get_schedule_stats(self._branch_id, sd)
        self._k_total.set_value(str(stats["total"]))
        self._k_booked.set_value(str(stats["booked"]))
        self._k_avail.set_value(str(stats["available"]))
        self._k_done.set_value(str(stats["completed"]))

        rows = [[s[0],s[1],s[2] or "—",str(s[3]),
                 str(s[4])[:5], str(s[5])[:5],
                 s[6],s[7],s[8] or "",""] for s in slots]
        self.table.set_data(rows)
        tw = self.table.table
        vis = slots[self.table._current_page*self.table._page_size:(self.table._current_page+1)*self.table._page_size]
        role = self._session.role
        for ri, s in enumerate(vis):
            sid, status = s[0], s[7]
            cell = QWidget(); bl = QHBoxLayout(cell); bl.setContentsMargins(4,2,4,2); bl.setSpacing(4)

            if role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER):
                eb = QPushButton("✏️"); eb.setStyleSheet(_P("#7C3AED")); eb.setFixedWidth(32)
                eb.clicked.connect(lambda _, i=sid: self.open_edit.emit(i)); bl.addWidget(eb)

            if status in ("Available","Booked") and role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER):
                done_btn = QPushButton("✅ Done"); done_btn.setStyleSheet(_P("#00E676"))
                done_btn.clicked.connect(lambda _, i=sid: self._complete(i)); bl.addWidget(done_btn)

            if status not in ("Cancelled","Completed"):
                c_btn = QPushButton("🚫 Cancel"); c_btn.setStyleSheet(_P("#FF2D78"))
                c_btn.clicked.connect(lambda _, i=sid: self._cancel(i)); bl.addWidget(c_btn)

            tw.setCellWidget(ri,9,cell)
            tw.setCellWidget(ri,7,StatusBadge(status))

    def _complete(self, sid):
        dlg = ConfirmDialog("Complete Session","Mark this session as completed?","Confirm","primary",self)
        if dlg.exec():
            r = sched_svc.mark_slot_complete(sid, self._session.user_id)
            InfoDialog("Result",r["message"],"success" if r["success"] else "error",self).exec()
            if r["success"]: self._load()

    def _cancel(self, sid):
        dlg = ConfirmDialog("Cancel Slot","Cancel this scheduled slot?","Cancel Slot","danger",self)
        if dlg.exec():
            r = sched_svc.cancel_slot(sid, self._session.user_id)
            InfoDialog("Result",r["message"],"success" if r["success"] else "error",self).exec()
            if r["success"]: self._load()

    def refresh(self): self._load()


class _SlotForm(QWidget):
    saved = pyqtSignal(); cancelled = pyqtSignal()

    def __init__(self, session, slot_id=None, parent=None):
        super().__init__(parent)
        self._session = session; self._slot_id = slot_id; self._is_edit = slot_id is not None
        self.setStyleSheet("background:transparent;")
        self._build_ui()
        if self._is_edit: self._load()

    def _lbl(self, t): l=QLabel(t); l.setStyleSheet("color:#9CA3AF;font-size:13px;"); return l

    def _build_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;background:transparent;")
        c = QWidget(); c.setStyleSheet("background:transparent;")
        m = QVBoxLayout(c); m.setContentsMargins(28,24,28,28); m.setSpacing(18)

        hdr = QHBoxLayout()
        back = QPushButton("← Back"); back.setObjectName("btnSecondary"); back.setFixedHeight(36)
        back.clicked.connect(self.cancelled.emit); hdr.addWidget(back)
        hdr.addWidget(QLabel(f"{'✏️ Edit' if self._is_edit else '➕ New'} Schedule Slot")); hdr.addStretch()
        sv = QPushButton("💾 Save Slot"); sv.setObjectName("btnPrimary"); sv.setMinimumHeight(40)
        sv.clicked.connect(self._save); hdr.addWidget(sv)
        m.addLayout(hdr)

        card = QFrame(); card.setStyleSheet("background:rgba(255,255,255,0.05);border:1px solid rgba(124,58,237,0.25);border-radius:16px;")
        g = QGridLayout(card); g.setContentsMargins(28,24,28,28); g.setSpacing(14)
        g.setColumnStretch(1,1); g.setColumnStretch(3,1)

        # Branch
        g.addWidget(self._lbl("Branch *"),0,0)
        self._branch = QComboBox(); self._branch.setMinimumHeight(38)
        for bid, bn in branch_svc.get_all_branches_dropdown(): self._branch.addItem(bn,bid)
        if self._session.branch_id:
            idx=self._branch.findData(self._session.branch_id); self._branch.setCurrentIndex(max(0,idx))
            if self._session.role in (ROLE_MANAGER, ROLE_TRAINER): self._branch.setEnabled(False)
        self._branch.currentIndexChanged.connect(self._refresh_trainers)
        g.addWidget(self._branch,0,1)

        # Class type
        g.addWidget(self._lbl("Class Type"),0,2)
        self._type = QComboBox(); self._type.setMinimumHeight(38)
        for ct in CLASS_TYPES: self._type.addItem(ct,ct)
        g.addWidget(self._type,0,3)

        # Trainer
        g.addWidget(self._lbl("Trainer *"),1,0)
        self._trainer = QComboBox(); self._trainer.setMinimumHeight(38); g.addWidget(self._trainer,1,1)
        if self._session.role == ROLE_TRAINER: self._trainer.setEnabled(False)

        # Member
        g.addWidget(self._lbl("Member"),1,2)
        self._member = QComboBox(); self._member.setMinimumHeight(38)
        self._member.addItem("— No Member —",None)
        if self._session.role == ROLE_TRAINER:
            t_record = trainer_svc.get_trainer_by_user_id(self._session.user_id)
            if t_record:
                for mm in trainer_svc.get_assigned_members(t_record[0]):
                    # m[0]=id, m[1]=full_name, m[2]=phone
                    self._member.addItem(f"{mm[1]} ({mm[2]})", mm[0])
        else:
            for mm in member_svc.get_all_members(branch_id=self._session.branch_id, status="Active"):
                self._member.addItem(f"{mm[1]} ({mm[2]})",mm[0])
        g.addWidget(self._member,1,3)

        # Date
        g.addWidget(self._lbl("Date *"),2,0)
        self._date = QDateEdit(); self._date.setCalendarPopup(True)
        self._date.setDisplayFormat("dd/MM/yyyy"); self._date.setDate(QDate.currentDate())
        self._date.setMinimumHeight(38); g.addWidget(self._date,2,1)

        # Status
        g.addWidget(self._lbl("Status"),2,2)
        self._status = QComboBox(); self._status.setMinimumHeight(38)
        for s in SLOT_STATUSES: self._status.addItem(s,s)
        g.addWidget(self._status,2,3)

        # Times
        g.addWidget(self._lbl("Start Time *"),3,0)
        self._start = QTimeEdit(); self._start.setDisplayFormat("HH:mm")
        self._start.setTime(QTime(8,0)); self._start.setMinimumHeight(38); g.addWidget(self._start,3,1)

        g.addWidget(self._lbl("End Time *"),3,2)
        self._end = QTimeEdit(); self._end.setDisplayFormat("HH:mm")
        self._end.setTime(QTime(9,0)); self._end.setMinimumHeight(38); g.addWidget(self._end,3,3)

        # Notes
        g.addWidget(self._lbl("Notes"),4,0)
        self._notes = QLineEdit(); self._notes.setPlaceholderText("Session notes...")
        self._notes.setMinimumHeight(38); g.addWidget(self._notes,4,1,1,3)

        m.addWidget(card); m.addStretch(); scroll.setWidget(c)
        QVBoxLayout(self).addWidget(scroll); self.layout().setContentsMargins(0,0,0,0)
        self._refresh_trainers()

    def _refresh_trainers(self):
        bid = self._branch.currentData()
        self._trainer.clear(); self._trainer.addItem("— Select Trainer —",None)
        if bid:
            for t in trainer_svc.get_trainers_for_branch(bid):
                self._trainer.addItem(f"{t[1]} ({t[2]})",t[0])
        
        if self._session.role == ROLE_TRAINER:
            t_record = trainer_svc.get_trainer_by_user_id(self._session.user_id)
            if t_record:
                idx = self._trainer.findData(t_record[0])
                if idx >= 0:
                    self._trainer.setCurrentIndex(idx)

    def _load(self):
        # fetch from DB — slots are lightweight so we query inline
        slots = sched_svc.get_schedule(branch_id=None, trainer_id=None, slot_date=None, status=None)
        slot = next((s for s in slots if s[0]==self._slot_id), None)
        if not slot: return
        idx=self._branch.findData(slot[12]); self._branch.setCurrentIndex(max(0,idx))
        self._refresh_trainers()
        idx=self._trainer.findData(slot[10]); self._trainer.setCurrentIndex(max(0,idx))
        if slot[11]:
            idx=self._member.findData(slot[11]); self._member.setCurrentIndex(max(0,idx))
        d=slot[3]; self._date.setDate(QDate(d.year,d.month,d.day))
        st=slot[4]; self._start.setTime(QTime(st.hour if hasattr(st,"hour") else 8, getattr(st,"minute",0)))
        et=slot[5]; self._end.setTime(QTime(et.hour if hasattr(et,"hour") else 9, getattr(et,"minute",0)))
        idx=self._type.findData(slot[6]); self._type.setCurrentIndex(max(0,idx))
        idx=self._status.findData(slot[7]); self._status.setCurrentIndex(max(0,idx))
        self._notes.setText(slot[8] or "")

    def _save(self):
        if not self._trainer.currentData():
            InfoDialog("Error","Please select a trainer.","error",self).exec(); return
        if not self._branch.currentData():
            InfoDialog("Error","Please select a branch.","error",self).exec(); return
        if self._start.time() >= self._end.time():
            InfoDialog("Error","End time must be after start time.","error",self).exec(); return
        data = {
            "branch_id":  self._branch.currentData(),
            "trainer_id": self._trainer.currentData(),
            "member_id":  self._member.currentData(),
            "slot_date":  self._date.date().toPyDate(),
            "start_time": self._start.time().toPyTime(),
            "end_time":   self._end.time().toPyTime(),
            "class_type": self._type.currentData(),
            "status":     self._status.currentData(),
            "notes":      self._notes.text().strip(),
        }
        result = sched_svc.update_slot(self._slot_id, data, self._session.user_id) \
                 if self._is_edit else sched_svc.create_slot(data, self._session.user_id)
        InfoDialog("Result",result["message"],"success" if result["success"] else "error",self).exec()
        if result["success"]: self.saved.emit()
