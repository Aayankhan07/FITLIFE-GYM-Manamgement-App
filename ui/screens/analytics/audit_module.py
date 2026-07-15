"""FitLife — Audit Logs Module (Phase 6)"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QDateEdit, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QDate

from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
from database.connection import DatabaseConnection
import logging

logger = logging.getLogger(__name__)

AUDIT_ACTIONS = ["All", "LOGIN", "LOGOUT", "CREATE", "UPDATE", "DELETE",
                 "PAYMENT", "SALARY", "PLAN_APPROVE", "PLAN_REJECT",
                 "LOGIN_FAILED", "TOGGLE_ACTIVATED", "TOGGLE_DEACTIVATED"]
AUDIT_MODULES = ["All", "Members", "Trainers", "Branches", "Billing", "Attendance",
                 "Workout Plans", "Diet Plans", "Equipment", "Staff", "Scheduling",
                 "Progress", "Salary"]


def _get_audit_logs(date_from, date_to, action=None, module=None, search=None, limit=500):
    try:
        sql = """
            SELECT TOP (?) al.id, u.full_name, u.username, al.action,
                   al.module, al.record_id, al.old_value, al.new_value,
                   al.timestamp
            FROM   audit_logs al
            LEFT JOIN users u ON al.user_id=u.id
            WHERE  al.timestamp BETWEEN ? AND DATEADD(day,1,?)
        """
        params = [limit, date_from, date_to]
        if action and action != "All":
            sql += " AND al.action=?"; params.append(action)
        if module and module != "All":
            sql += " AND al.module=?"; params.append(module)
        if search:
            sql += " AND (u.full_name LIKE ? OR u.username LIKE ? OR al.new_value LIKE ?)"
            s = f"%{search}%"; params += [s, s, s]
        sql += " ORDER BY al.timestamp DESC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"audit logs error: {e}"); return []


class AuditLogsModule(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setStyleSheet("background:transparent;")
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QWidget { border:none;background:transparent; }")
        c = QWidget(); c.setStyleSheet("background:transparent;")
        m = QVBoxLayout(c); m.setContentsMargins(28,24,28,28); m.setSpacing(16)

        hdr = QHBoxLayout()
        t = QLabel("🔍  Audit Logs"); t.setStyleSheet("QWidget { font-size:26px;font-weight:900;color:#F0F4FF; }")
        hdr.addWidget(t); hdr.addStretch(); m.addLayout(hdr)

        # Filters
        ff = QFrame(); ff.setStyleSheet("QFrame { background:rgba(255,255,255,0.04);border:1px solid rgba(0, 102, 255, 0.2);border-radius:12px; }")
        fr = QHBoxLayout(ff); fr.setContentsMargins(16,10,16,10); fr.setSpacing(10)

        fr.addWidget(QLabel("From:"))
        self._df = QDateEdit(); self._df.setCalendarPopup(True); self._df.setDisplayFormat("dd/MM/yyyy")
        self._df.setDate(QDate.currentDate().addDays(-30)); self._df.setFixedHeight(34); fr.addWidget(self._df)

        fr.addWidget(QLabel("To:"))
        self._dt = QDateEdit(); self._dt.setCalendarPopup(True); self._dt.setDisplayFormat("dd/MM/yyyy")
        self._dt.setDate(QDate.currentDate()); self._dt.setFixedHeight(34); fr.addWidget(self._dt)

        fr.addWidget(QLabel("Action:"))
        self._af = QComboBox(); self._af.setFixedHeight(34)
        for a in AUDIT_ACTIONS: self._af.addItem(a, a)
        fr.addWidget(self._af)

        fr.addWidget(QLabel("Module:"))
        self._mf = QComboBox(); self._mf.setFixedHeight(34)
        for mod in AUDIT_MODULES: self._mf.addItem(mod, mod)
        fr.addWidget(self._mf)

        self._srch = QLineEdit(); self._srch.setPlaceholderText("Search user / value...")
        self._srch.setFixedHeight(34); self._srch.setMaximumWidth(200); fr.addWidget(self._srch)
        fr.addStretch()
        rb = QPushButton("🔄 Load"); rb.setObjectName("btnPrimary"); rb.setFixedHeight(34)
        rb.clicked.connect(self._load); fr.addWidget(rb)
        m.addWidget(ff)

        # Count label
        self._cnt = QLabel(""); self._cnt.setStyleSheet("QWidget { color:#9CA3AF;font-size: 13px; }"); m.addWidget(self._cnt)

        # Table
        self._tbl = QTableWidget()
        self._tbl.setColumnCount(9)
        self._tbl.setHorizontalHeaderLabels(["ID","User","Username","Action","Module","Record ID","Old Value","New Value","Timestamp"])
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.horizontalHeader().setStretchLastSection(True)
        self._tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tbl.setStyleSheet("""
            QTableWidget{background:transparent;border:none;color:#F0F4FF;}
            QTableWidget::item{padding:8px;border-bottom:1px solid rgba(0, 102, 255, 0.12);}
            QTableWidget::item:hover{background:rgba(0, 102, 255, 0.08);}
            QHeaderView::section{background:rgba(0, 102, 255, 0.2);color:#00F5FF;padding:10px;border:none;font-weight:bold;}
        """)
        tc = QFrame(); tc.setStyleSheet("QFrame { background:rgba(255,255,255,0.04);border:1px solid rgba(0, 102, 255, 0.2);border-radius:14px; }")
        QVBoxLayout(tc).addWidget(self._tbl); m.addWidget(tc)

        self._overlay = LoadingOverlay(self)
        scroll.setWidget(c)
        QVBoxLayout(self).addWidget(scroll); self.layout().setContentsMargins(0,0,0,0)

    # Colors for action badges
    _ACTION_COLORS = {
        "CREATE": "#00E676", "UPDATE": "#00F5FF", "DELETE": "#FF2D78",
        "LOGIN": "#0066FF", "LOGOUT": "#9CA3AF", "PAYMENT": "#FFB800",
        "PLAN_APPROVE": "#00E676", "PLAN_REJECT": "#FF2D78",
        "LOGIN_FAILED": "#FF2D78",
    }

    def _load(self):
        self._overlay.show_loading("Loading audit trail...")
        df   = self._df.date().toPyDate()
        dt   = self._dt.date().toPyDate()
        act  = self._af.currentData()
        mod  = self._mf.currentData()
        srch = self._srch.text().strip() or None
        self._w = Worker(_get_audit_logs, df, dt, act, mod, srch)
        self._w.result.connect(self._on_data)
        self._w.error.connect(lambda e: self._overlay.hide_loading())
        self._w.start()

    def _on_data(self, logs):
        self._overlay.hide_loading()
        self._cnt.setText(f"{len(logs)} entries")
        self._tbl.setRowCount(0)
        for log in logs:
            r = self._tbl.rowCount(); self._tbl.insertRow(r)
            vals = [str(log[0]), log[1] or "—", log[2] or "—",
                    log[3], log[4] or "—", str(log[5]) if log[5] else "—",
                    (log[6] or "")[:80], (log[7] or "")[:80],
                    str(log[8])[:19] if log[8] else "—"]
            for ci, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if ci == 3:  # Action column — color
                    clr = self._ACTION_COLORS.get(v, "#9CA3AF")
                    item.setForeground(__import__("PyQt6.QtGui", fromlist=["QColor"]).QColor(clr))
                self._tbl.setItem(r, ci, item)

    def refresh(self): self._load()
