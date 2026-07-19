"""FitLife — Reports Module (Phase 6)"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QDateEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QTabWidget, QHeaderView
)
from PyQt6.QtCore import Qt, QDate

from ui.components.glass_card import KPICard, SectionHeader
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
import services.reports_service as rep_svc
import services.branch_service as branch_svc
from config.constants import ROLE_ADMIN, MEMBER_STATUSES
from ui.components.confirm_dialog import InfoDialog


class ReportsModule(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setStyleSheet("background:transparent;")
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QWidget { border:none;background:transparent; }")
        c = QWidget(); c.setStyleSheet("background:transparent;")
        m = QVBoxLayout(c); m.setContentsMargins(28,24,28,28); m.setSpacing(18)

        hdr = QHBoxLayout()
        t = QLabel("📋  Reports"); t.setStyleSheet("QWidget { font-size:26px;font-weight:900;color:#F0F4FF; }")
        hdr.addWidget(t); hdr.addStretch(); m.addLayout(hdr)

        # Common filter bar
        ff = QFrame(); ff.setStyleSheet("QFrame { background:rgba(255,255,255,0.04);border:1px solid rgba(0, 102, 255, 0.2);border-radius:12px; }")
        fr = QHBoxLayout(ff); fr.setContentsMargins(16,10,16,10); fr.setSpacing(12)
        fr.addWidget(QLabel("Branch:"))
        self._bf = QComboBox(); self._bf.setFixedHeight(34)
        if self._session.role == ROLE_ADMIN:
            self._bf.addItem("All Branches", None)
            for bid, bn in branch_svc.get_all_branches_dropdown(): self._bf.addItem(bn, bid)
        else:
            self._bf.addItem("My Branch", self._session.branch_id)
        fr.addWidget(self._bf)
        fr.addWidget(QLabel("From:"))
        self._df = QDateEdit(); self._df.setCalendarPopup(True); self._df.setDisplayFormat("dd/MM/yyyy")
        self._df.setDate(QDate.currentDate().addMonths(-1)); self._df.setFixedHeight(34); fr.addWidget(self._df)
        fr.addWidget(QLabel("To:"))
        self._dt = QDateEdit(); self._dt.setCalendarPopup(True); self._dt.setDisplayFormat("dd/MM/yyyy")
        self._dt.setDate(QDate.currentDate()); self._dt.setFixedHeight(34); fr.addWidget(self._dt)
        fr.addStretch()
        m.addWidget(ff)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane{background:rgba(255,255,255,0.04);border:1px solid rgba(0, 102, 255, 0.2);border-radius:12px;}
            QTabBar::tab{background:rgba(0,0,0,0.2);color:#9CA3AF;padding:10px 20px;border-radius:8px;margin-right:4px;}
            QTabBar::tab:selected{background:rgba(0, 102, 255, 0.3);color:#0066FF;font-weight:bold;}
        """)

        reports = [
            ("👥 Members",      self._build_tab_members),
            ("💰 Payments",     self._build_tab_payments),
            ("📅 Attendance",   self._build_tab_attendance),
            ("💪 Trainers",     self._build_tab_trainers),
            ("🏋️ Equipment",    self._build_tab_equipment),
        ]
        self._tables = {}
        for label, builder in reports:
            w, table = builder()
            self._tabs.addTab(w, label)
            self._tables[label] = table
        m.addWidget(self._tabs)

        self._overlay = LoadingOverlay(self)
        scroll.setWidget(c)
        QVBoxLayout(self).addWidget(scroll); self.layout().setContentsMargins(0,0,0,0)

    def _make_table(self, cols: list) -> QTableWidget:
        t = QTableWidget(); t.setColumnCount(len(cols))
        t.setHorizontalHeaderLabels(cols)
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setStyleSheet("""
            QTableWidget{background:transparent;border:none;color:#F0F4FF;}
            QTableWidget::item{padding:8px;border-bottom:1px solid rgba(0, 102, 255, 0.12);}
            QTableWidget::item:hover{background:rgba(0, 102, 255, 0.08);}
            QHeaderView::section{background:rgba(0, 102, 255, 0.2);color:#00F5FF;padding:10px;border:none;font-weight:bold;}
        """)
        header = t.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(len(cols) - 1):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        return t

    def _tab_shell(self, title: str, cols: list):
        w = QWidget(); w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w); lay.setContentsMargins(12,12,12,12); lay.setSpacing(10)
        top = QHBoxLayout()
        top.addWidget(QLabel(title))
        top.addStretch()
        gen = QPushButton("🔄 Generate"); gen.setObjectName("btnPrimary"); gen.setFixedHeight(34)
        exp = QPushButton("💾 Export Data"); exp.setObjectName("btnSecondary"); exp.setFixedHeight(34)
        top.addWidget(gen); top.addWidget(exp)
        lay.addLayout(top)
        cnt = QLabel(""); cnt.setStyleSheet("QWidget { color:#9CA3AF;font-size: 13px; }"); lay.addWidget(cnt)
        tbl = self._make_table(cols)
        lay.addWidget(tbl)
        return w, tbl, gen, exp, cnt

    def _fill_table(self, tbl, rows):
        tbl.setRowCount(0)
        for row in rows:
            r = tbl.rowCount(); tbl.insertRow(r)
            for ci, v in enumerate(row): tbl.setItem(r, ci, QTableWidgetItem(str(v) if v is not None else ""))

    def _export_report_flow(self, report_name: str, cols: list, data_func):
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            f"Export {report_name}",
            report_name.lower().replace(" ", "_"),
            "CSV File (*.csv);;Excel Workbook (*.xlsx);;PDF Document (*.pdf)"
        )
        if not path:
            return
            
        data = data_func()
        rows = [list(row) for row in data]
        
        if path.endswith(".xlsx"):
            r = rep_svc.export_to_excel(report_name, cols, rows, path)
        elif path.endswith(".pdf"):
            r = rep_svc.export_to_pdf(report_name, cols, rows, path)
        else:
            if not path.endswith(".csv"):
                path += ".csv"
            r = rep_svc.export_to_csv(cols, rows, path)
            
        InfoDialog("Export Status", r["message"], "success" if r["success"] else "error", self).exec()

    def _build_tab_members(self):
        cols = ["Name","CNIC","Phone","Email","Branch","Trainer","Plan","Join","Expiry","Status","Goal","Weight","BMI"]
        w, tbl, gen, exp, cnt = self._tab_shell("Member Report", cols)
        def _gen():
            bid = self._bf.currentData()
            data = rep_svc.get_member_report(bid)
            self._fill_table(tbl, data); cnt.setText(f"{len(data)} records")
        def _exp():
            self._export_report_flow("Member Report", cols, lambda: rep_svc.get_member_report(self._bf.currentData()))
        gen.clicked.connect(_gen); exp.clicked.connect(_exp)
        return w, tbl

    def _build_tab_payments(self):
        cols = ["Member","Phone","Branch","Invoice","Amount","Date","Method","Status","Notes"]
        w, tbl, gen, exp, cnt = self._tab_shell("Payment Report", cols)
        def _gen():
            bid  = self._bf.currentData()
            df   = self._df.date().toPyDate()
            dt   = self._dt.date().toPyDate()
            data = rep_svc.get_payment_report(bid, df, dt)
            self._fill_table(tbl, data); cnt.setText(f"{len(data)} records")
        def _exp():
            self._export_report_flow("Payment Report", cols, lambda: rep_svc.get_payment_report(self._bf.currentData(), self._df.date().toPyDate(), self._dt.date().toPyDate()))
        gen.clicked.connect(_gen); exp.clicked.connect(_exp)
        return w, tbl

    def _build_tab_attendance(self):
        cols = ["Member","Branch","Date","Check-in","Check-out","Status"]
        w, tbl, gen, exp, cnt = self._tab_shell("Attendance Report", cols)
        def _gen():
            bid  = self._bf.currentData()
            df   = self._df.date().toPyDate()
            dt   = self._dt.date().toPyDate()
            data = rep_svc.get_attendance_report(bid, df, dt)
            self._fill_table(tbl, data); cnt.setText(f"{len(data)} records")
        def _exp():
            self._export_report_flow("Attendance Report", cols, lambda: rep_svc.get_attendance_report(self._bf.currentData(), self._df.date().toPyDate(), self._dt.date().toPyDate()))
        gen.clicked.connect(_gen); exp.clicked.connect(_exp)
        return w, tbl

    def _build_tab_trainers(self):
        cols = ["Name","Branch","Specialization","Active Members","Rating","Salary","Hire Date","Status"]
        w, tbl, gen, exp, cnt = self._tab_shell("Trainer Performance", cols)
        def _gen():
            data = rep_svc.get_trainer_performance_report(self._bf.currentData())
            self._fill_table(tbl, data); cnt.setText(f"{len(data)} trainers")
        def _exp():
            self._export_report_flow("Trainer Performance Report", cols, lambda: rep_svc.get_trainer_performance_report(self._bf.currentData()))
        gen.clicked.connect(_gen); exp.clicked.connect(_exp)
        return w, tbl

    def _build_tab_equipment(self):
        cols = ["Name","Category","Brand","Model","Serial #","Condition","Qty","Price","Purchase Date","Last Maint.","Branch"]
        w, tbl, gen, exp, cnt = self._tab_shell("Equipment Report", cols)
        def _gen():
            data = rep_svc.get_equipment_report(self._bf.currentData())
            self._fill_table(tbl, data); cnt.setText(f"{len(data)} items")
        def _exp():
            self._export_report_flow("Equipment Report", cols, lambda: rep_svc.get_equipment_report(self._bf.currentData()))
        gen.clicked.connect(_gen); exp.clicked.connect(_exp)
        return w, tbl
