"""FitLife — Progress Tracking Module"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QDoubleSpinBox,
    QGridLayout, QDateEdit, QLineEdit, QTableWidget,
    QTableWidgetItem, QStackedWidget, QTextEdit
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from ui.components.glass_card import KPICard, SectionHeader
from ui.components.confirm_dialog import ConfirmDialog, InfoDialog
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
import services.progress_service as prog_svc
import services.member_service as member_svc
from config.constants import ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER


class ProgressModule(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setStyleSheet("background:transparent;")
        self._stack = QStackedWidget(); self._stack.setStyleSheet("background:transparent;")
        QVBoxLayout(self).addWidget(self._stack); self.layout().setContentsMargins(0,0,0,0)
        self._list = _ProgressOverview(session)
        self._list.open_member.connect(self._show_member)
        self._stack.addWidget(self._list); self._stack.setCurrentWidget(self._list)

    def _show_member(self, mid):
        w = _MemberProgress(self._session, mid)
        w.go_back.connect(self._back)
        self._stack.addWidget(w); self._stack.setCurrentWidget(w)

    def _back(self):
        while self._stack.count() > 1:
            w = self._stack.widget(1); self._stack.removeWidget(w); w.deleteLater()
        self._stack.setCurrentWidget(self._list); self._list.refresh()

    def refresh(self):
        if hasattr(self._stack.currentWidget(), "refresh"):
            self._stack.currentWidget().refresh()


class _ProgressOverview(QWidget):
    open_member = pyqtSignal(int)

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session; self._branch_id = session.branch_id
        self.setStyleSheet("background:transparent;")
        self._build_ui(); self._load()

    def _build_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QWidget { border:none;background:transparent; }")
        c = QWidget(); c.setStyleSheet("background:transparent;")
        m = QVBoxLayout(c); m.setContentsMargins(28,24,28,24); m.setSpacing(18)

        hdr = QHBoxLayout()
        t = QLabel("📈  Progress Tracking"); t.setStyleSheet("QWidget { font-size:26px;font-weight:900;color:#F0F4FF; }")
        hdr.addWidget(t); hdr.addStretch()
        rb = QPushButton("🔄 Refresh"); rb.setObjectName("btnSecondary"); rb.setMinimumHeight(38)
        rb.clicked.connect(self._load); hdr.addWidget(rb)
        m.addLayout(hdr)

        m.addWidget(SectionHeader("👥  Member Progress Overview"))

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(["Member","Current Weight","Fitness Goal","Last Log","Total Logs","View Progress"])
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setStyleSheet("""
            QTableWidget{background:transparent;border:none;color:#F0F4FF;}
            QTableWidget::item{padding:10px;border-bottom:1px solid rgba(0, 102, 255, 0.15);}
            QTableWidget::item:hover{background:rgba(0, 102, 255, 0.1);}
            QHeaderView::section{background:rgba(0, 102, 255, 0.2);color:#00F5FF;
            padding:10px;border:none;font-weight:bold;}
        """)
        tc = QFrame(); tc.setStyleSheet("QFrame { background:rgba(255,255,255,0.04);border:1px solid rgba(0, 102, 255, 0.2);border-radius:16px; }")
        QVBoxLayout(tc).addWidget(self._table)
        m.addWidget(tc)

        self._overlay = LoadingOverlay(self)
        scroll.setWidget(c)
        QVBoxLayout(self).addWidget(scroll); self.layout().setContentsMargins(0,0,0,0)

    def _load(self):
        self._overlay.show_loading("Loading progress data...")
        branch_id = self._branch_id  # None for Admin = all branches
        mid = None
        tid = None
        if self._session.role == ROLE_MEMBER:
            member = member_svc.get_member_by_user_id(self._session.user_id)
            mid = member[0] if member else None
        elif self._session.role == ROLE_TRAINER:
            import services.trainer_service as t_svc
            trainer = t_svc.get_trainer_by_user_id(self._session.user_id)
            tid = trainer[0] if trainer else None
            
        self._w = Worker(prog_svc.get_all_progress_overview, branch_id, mid, tid)
        self._w.result.connect(self._on_data)
        self._w.error.connect(lambda e: self._overlay.hide_loading())
        self._w.start()

    def _on_data(self, members):
        self._overlay.hide_loading()
        self._table.setRowCount(0)
        if not members:
            # Show empty state row
            self._table.setRowCount(1)
            self._table.setItem(0, 0, QTableWidgetItem("No active members found"))
            return
        for row in members:
            r = self._table.rowCount(); self._table.insertRow(r)
            mid, name, weight, goal, last_log, total = row[0],row[1],row[2],row[3],row[4],row[5]
            self._table.setItem(r,0,QTableWidgetItem(str(name or "—")))
            self._table.setItem(r,1,QTableWidgetItem(f"{weight} kg" if weight else "—"))
            self._table.setItem(r,2,QTableWidgetItem(str(goal or "—")))
            self._table.setItem(r,3,QTableWidgetItem(str(last_log) if last_log else "Never"))
            self._table.setItem(r,4,QTableWidgetItem(str(total or "0")))
            btn = QPushButton("📈 View Progress")
            btn.setFixedHeight(32)
            btn.setStyleSheet(
                "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #0097B2,stop:1 #00D4E8);"
                "border:none;border-radius:6px;color:#001A1F;"
                "font-size: 13px;font-weight:600;padding:0 10px;}"
                "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #00B8D9,stop:1 #00F5FF);}"
            )
            btn.clicked.connect(lambda _, i=mid: self.open_member.emit(i))
            self._table.setCellWidget(r,5,btn)

    def refresh(self): self._load()


class _MemberProgress(QWidget):
    go_back = pyqtSignal()

    def __init__(self, session, member_id, parent=None):
        super().__init__(parent)
        self._session = session; self._member_id = member_id
        self.setStyleSheet("background:transparent;")
        self._build_ui(); self._load()

    def _build_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QWidget { border:none;background:transparent; }")
        c = QWidget(); c.setStyleSheet("background:transparent;")
        m = QVBoxLayout(c); m.setContentsMargins(28,24,28,28); m.setSpacing(18)

        hdr = QHBoxLayout()
        back = QPushButton("← Back"); back.setObjectName("btnSecondary"); back.setFixedHeight(36)
        back.clicked.connect(self.go_back.emit); hdr.addWidget(back); hdr.addStretch()
        m.addLayout(hdr)

        # Summary KPIs
        kr = QHBoxLayout(); kr.setSpacing(14)
        self._k_logs    = KPICard("Total Logs","—","📋","","#0066FF")
        self._k_change  = KPICard("Weight Change","—","⚖️","","#00E676")
        self._k_first   = KPICard("First Log","—","📅","","#00F5FF")
        self._k_latest  = KPICard("Latest Log","—","🕐","","#FFB800")
        for k in [self._k_logs,self._k_change,self._k_first,self._k_latest]: kr.addWidget(k)
        m.addLayout(kr)

        # Log entry form
        if self._session.role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER):
            lf = QFrame(); lf.setStyleSheet("QWidget { background:rgba(0,245,255,0.05);border:1px solid rgba(0,245,255,0.2);border-radius:12px; }")
            lg = QGridLayout(lf); lg.setContentsMargins(20,16,20,16); lg.setSpacing(12)

            lg.addWidget(QLabel("Log Date:"),0,0)
            self._log_date = QDateEdit(); self._log_date.setCalendarPopup(True)
            self._log_date.setDisplayFormat("dd/MM/yyyy"); self._log_date.setDate(QDate.currentDate())
            self._log_date.setMinimumHeight(36); lg.addWidget(self._log_date,0,1)

            lg.addWidget(QLabel("Weight (kg):"),0,2)
            self._weight = QDoubleSpinBox(); self._weight.setRange(0,300); self._weight.setDecimals(1)
            self._weight.setSuffix(" kg"); self._weight.setMinimumHeight(36); lg.addWidget(self._weight,0,3)

            lg.addWidget(QLabel("Body Fat %:"),0,4)
            self._fat = QDoubleSpinBox(); self._fat.setRange(0,60); self._fat.setDecimals(1)
            self._fat.setSuffix(" %"); self._fat.setMinimumHeight(36); lg.addWidget(self._fat,0,5)

            lg.addWidget(QLabel("Chest (cm):"),1,0)
            self._chest = QDoubleSpinBox(); self._chest.setRange(0,200); self._chest.setMinimumHeight(36); lg.addWidget(self._chest,1,1)
            lg.addWidget(QLabel("Waist (cm):"),1,2)
            self._waist = QDoubleSpinBox(); self._waist.setRange(0,200); self._waist.setMinimumHeight(36); lg.addWidget(self._waist,1,3)
            lg.addWidget(QLabel("Arms (cm):"),1,4)
            self._arms = QDoubleSpinBox(); self._arms.setRange(0,100); self._arms.setMinimumHeight(36); lg.addWidget(self._arms,1,5)

            lg.addWidget(QLabel("Legs (cm):"),2,0)
            self._legs = QDoubleSpinBox(); self._legs.setRange(0,200); self._legs.setMinimumHeight(36); lg.addWidget(self._legs,2,1)
            lg.addWidget(QLabel("Notes:"),2,2)
            self._notes = QLineEdit(); self._notes.setPlaceholderText("Any observations..."); self._notes.setMinimumHeight(36)
            lg.addWidget(self._notes,2,3)

            save_btn = QPushButton("✅ Log Progress"); save_btn.setObjectName("btnPrimary"); save_btn.setFixedHeight(36)
            save_btn.clicked.connect(self._save_log); lg.addWidget(save_btn,2,4,1,2)
            m.addWidget(lf)

        # History table
        m.addWidget(SectionHeader("📊  Progress History"))
        self._hist = QTableWidget()
        self._hist.setColumnCount(9)
        self._hist.setHorizontalHeaderLabels(["Date","Weight","Body Fat","Chest","Waist","Hips","Arms","Legs","Notes"])
        self._hist.verticalHeader().setVisible(False)
        self._hist.horizontalHeader().setStretchLastSection(True)
        self._hist.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._hist.setStyleSheet("QTableWidget{background:transparent;border:none;color:#F0F4FF;}QTableWidget::item{padding:8px;border-bottom:1px solid rgba(0, 102, 255, 0.15);}QHeaderView::section{background:rgba(0, 102, 255, 0.2);color:#00F5FF;padding:8px;border:none;font-weight:bold;}")
        tc = QFrame(); tc.setStyleSheet("QFrame { background:rgba(255,255,255,0.04);border:1px solid rgba(0, 102, 255, 0.2);border-radius:14px; }")
        QVBoxLayout(tc).addWidget(self._hist)
        m.addWidget(tc); m.addStretch(); scroll.setWidget(c)
        QVBoxLayout(self).addWidget(scroll); self.layout().setContentsMargins(0,0,0,0)

    def _load(self):
        summary = prog_svc.get_member_progress_summary(self._member_id)
        self._k_logs.set_value(str(summary.get("total_logs", 0)))
        delta = summary.get("weight_change", 0)
        sign = "+" if delta > 0 else ""
        self._k_change.set_value(f"{sign}{delta} kg")
        if summary.get("first"):
            self._k_first.set_value(str(summary["first"]["date"]))
        if summary.get("latest"):
            self._k_latest.set_value(str(summary["latest"]["date"]))

        logs = prog_svc.get_progress_logs(self._member_id)
        self._hist.setRowCount(0)
        # progress_logs schema:
        # [0]=id, [1]=member_id, [2]=log_date, [3]=weight_kg,
        # [4]=body_fat_pct, [5]=chest_cm, [6]=waist_cm, [7]=hips_cm,
        # [8]=arms_cm, [9]=legs_cm, [10]=notes
        for log in logs:
            r = self._hist.rowCount(); self._hist.insertRow(r)
            vals = [
                str(log[2]),                                  # Date
                f"{log[3]} kg"  if log[3] else "—",          # Weight
                f"{log[4]}%"    if log[4] else "—",          # Body Fat
                f"{log[5]} cm"  if log[5] else "—",          # Chest
                f"{log[6]} cm"  if log[6] else "—",          # Waist
                f"{log[7]} cm"  if log[7] else "—",          # Hips
                f"{log[8]} cm"  if log[8] else "—",          # Arms
                f"{log[9]} cm"  if log[9] else "—",          # Legs
                str(log[10]) if log[10] else "",             # Notes
            ]
            for ci, v in enumerate(vals):
                self._hist.setItem(r, ci, QTableWidgetItem(v))

    def _save_log(self):
        data = {
            "log_date":     self._log_date.date().toPyDate(),
            "weight_kg":    self._weight.value() or None,
            "body_fat_pct": self._fat.value() or None,
            "chest_cm":     self._chest.value() or None,
            "waist_cm":     self._waist.value() or None,
            "arms_cm":      self._arms.value() or None,
            "legs_cm":      self._legs.value() or None,
            "notes":        self._notes.text().strip(),
        }
        result = prog_svc.log_progress(self._member_id, data, self._session.user_id)
        InfoDialog("Result", result["message"], "success" if result["success"] else "error", self).exec()
        if result["success"]: self._notes.clear(); self._load()
