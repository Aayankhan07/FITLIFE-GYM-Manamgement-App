"""
FitLife — Salary Screen
Monthly salary generation, update (bonus/deduction), mark-paid, slip view.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QDoubleSpinBox,
    QLineEdit, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime

from ui.components.glass_card import KPICard, StatusBadge, SectionHeader
from ui.components.confirm_dialog import ConfirmDialog, InfoDialog
from ui.components.data_table import DataTable
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
import services.salary_service as salary_svc
import services.branch_service as branch_svc
from config.constants import ROLE_ADMIN, ROLE_MANAGER

now = datetime.now()
MONTHS_LABELS = ["","January","February","March","April","May","June",
                 "July","August","September","October","November","December"]


class SalaryScreen(QWidget):
    """Salary management: generate monthly records, update, mark-paid, view slip."""

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self._branch_id = session.branch_id
        self.setStyleSheet("background:transparent;")
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        container = QWidget(); container.setStyleSheet("background:transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(28,24,28,24); main.setSpacing(20)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("💳  Salary Management")
        title.setStyleSheet("font-size:26px; font-weight:900; color:#F0F4FF;")
        hdr.addWidget(title); hdr.addStretch()
        self.gen_btn = QPushButton("⚙️  Generate Monthly Salaries")
        self.gen_btn.setObjectName("btnPrimary")
        self.gen_btn.setMinimumHeight(40)
        self.gen_btn.clicked.connect(self._generate_salaries)
        hdr.addWidget(self.gen_btn)
        main.addLayout(hdr)

        # ── KPI row ───────────────────────────────────────────────────────────
        krow = QHBoxLayout(); krow.setSpacing(14)
        self._kpi_total   = KPICard("Total Records",  "—", "📋","","#7C3AED")
        self._kpi_paid    = KPICard("Paid",           "—", "✅","","#00E676")
        self._kpi_pending = KPICard("Pending",        "—", "⏳","","#FFB800")
        self._kpi_payout  = KPICard("Total Payout",  "—", "💰","","#00F5FF")
        for k in [self._kpi_total, self._kpi_paid, self._kpi_pending, self._kpi_payout]:
            krow.addWidget(k)
        main.addLayout(krow)

        # ── Month/Year Filter ─────────────────────────────────────────────────
        filter_frame = QFrame()
        filter_frame.setStyleSheet(
            "background:rgba(255,255,255,0.04);"
            "border:1px solid rgba(124,58,237,0.2);border-radius:12px;"
        )
        fr = QHBoxLayout(filter_frame)
        fr.setContentsMargins(16,10,16,10); fr.setSpacing(12)

        fr.addWidget(QLabel("Month:"))
        self.month_cb = QComboBox(); self.month_cb.setFixedHeight(34)
        for i, m in enumerate(MONTHS_LABELS[1:], 1):
            self.month_cb.addItem(m, i)
        self.month_cb.setCurrentIndex(now.month - 1)
        fr.addWidget(self.month_cb)

        fr.addWidget(QLabel("Year:"))
        self.year_cb = QComboBox(); self.year_cb.setFixedHeight(34)
        for y in range(now.year - 2, now.year + 1):
            self.year_cb.addItem(str(y), y)
        self.year_cb.setCurrentIndex(2)
        fr.addWidget(self.year_cb)

        if self._session.role == ROLE_ADMIN:
            fr.addWidget(QLabel("Branch:"))
            self.branch_cb = QComboBox(); self.branch_cb.setFixedHeight(34)
            self.branch_cb.addItem("All Branches", None)
            for bid, bname in branch_svc.get_all_branches_dropdown():
                self.branch_cb.addItem(bname, bid)
            fr.addWidget(self.branch_cb)

        fr.addStretch()
        ref_btn = QPushButton("🔄 Refresh")
        ref_btn.setObjectName("btnSecondary"); ref_btn.setFixedHeight(34)
        ref_btn.clicked.connect(self._load_data)
        fr.addWidget(ref_btn)
        main.addWidget(filter_frame)

        # ── Salary Table ──────────────────────────────────────────────────────
        cols = ["ID","Trainer","Branch","Month","Year",
                "Base Salary","Bonus","Deduction","Net Salary","Status","Actions"]
        self.table = DataTable(cols)
        tc = QFrame()
        tc.setStyleSheet(
            "background:rgba(255,255,255,0.04);"
            "border:1px solid rgba(124,58,237,0.2);border-radius:16px;"
        )
        tcl = QVBoxLayout(tc)
        tcl.setContentsMargins(16,16,16,16); tcl.addWidget(self.table)
        main.addWidget(tc)

        self._overlay = LoadingOverlay(self)
        scroll.setWidget(container)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

    # ── Data Loading ──────────────────────────────────────────────────────────
    def _load_data(self):
        self._overlay.show_loading("Loading salary records...")
        month = self.month_cb.currentData()
        year  = self.year_cb.currentData()
        bid   = self._branch_id
        if self._session.role == ROLE_ADMIN and hasattr(self, "branch_cb"):
            bid = self.branch_cb.currentData()
        self._worker = Worker(self._fetch, bid, month, year)
        self._worker.result.connect(self._on_loaded)
        self._worker.error.connect(lambda e: self._overlay.hide_loading())
        self._worker.start()

    def _fetch(self, branch_id, month, year):
        records = salary_svc.get_salary_records(branch_id, month, year)
        stats   = salary_svc.get_salary_stats(branch_id, month, year)
        return {"records": records, "stats": stats}

    def _on_loaded(self, data):
        self._overlay.hide_loading()
        s = data["stats"]
        self._kpi_total.set_value(str(s["total"]))
        self._kpi_paid.set_value(str(s["paid"]))
        self._kpi_pending.set_value(str(s["pending"]))
        self._kpi_payout.set_value(f"Rs. {s['total_payout']:,.0f}")

        records = data["records"]
        rows = []
        for r in records:
            rows.append([
                r[0], r[1], r[2],
                MONTHS_LABELS[r[3]], r[4],
                f"Rs. {float(r[5]):,.0f}",
                f"Rs. {float(r[6] or 0):,.0f}",
                f"Rs. {float(r[7] or 0):,.0f}",
                f"Rs. {float(r[8]):,.0f}",
                r[9], ""
            ])
        self.table.set_data(rows)
        self._inject_actions(records)

    def _inject_actions(self, records):
        tw = self.table.table
        visible = records[
            self.table._current_page * self.table._page_size:
            (self.table._current_page + 1) * self.table._page_size
        ]
        for r_idx, rec in enumerate(visible):
            rid    = rec[0]
            status = rec[9]

            cell = QWidget()
            bl = QHBoxLayout(cell)
            bl.setContentsMargins(4,2,4,2); bl.setSpacing(4)

            # Edit bonus/deduction
            edit_btn = QPushButton("✏ Adjust")
            edit_btn.setFixedHeight(32)
            edit_btn.setStyleSheet(
                "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #7C3AED,stop:1 #5B21B6);"
                "border:none;border-radius:6px;color:#FFFFFF;"
                "font-size: 13px;font-weight:600;padding:0 8px;}"
                "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #8B5CF6,stop:1 #7C3AED);}"
            )
            edit_btn.clicked.connect(
                lambda _, i=rid, base=float(rec[5]), bon=float(rec[6] or 0),
                ded=float(rec[7] or 0), notes=rec[11] if len(rec)>11 else "":
                self._open_adjust(i, base, bon, ded, notes)
            )
            bl.addWidget(edit_btn)

            # Mark paid (only if pending)
            if status == "Pending":
                pay_btn = QPushButton("✅ Mark Paid")
                pay_btn.setFixedHeight(32)
                pay_btn.setStyleSheet(
                    "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                    "stop:0 #00E676,stop:1 #00B248);"
                    "border:none;border-radius:6px;color:#001A0A;"
                    "font-size: 13px;font-weight:600;padding:0 8px;}"
                    "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                    "stop:0 #33FF99,stop:1 #00E676);}"
                )
                pay_btn.clicked.connect(lambda _, i=rid: self._mark_paid(i))
                bl.addWidget(pay_btn)

            # View slip
            slip_btn = QPushButton("🧾 Slip")
            slip_btn.setFixedHeight(32)
            slip_btn.setStyleSheet(
                "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #0097B2,stop:1 #00D4E8);"
                "border:none;border-radius:6px;color:#001A1F;"
                "font-size: 13px;font-weight:600;padding:0 8px;}"
                "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #00B8D9,stop:1 #00F5FF);}"
            )
            slip_btn.clicked.connect(lambda _, i=rid: self._view_slip(i))
            bl.addWidget(slip_btn)

            tw.setCellWidget(r_idx, 10, cell)
            tw.setCellWidget(r_idx, 9, StatusBadge(status))

    # ── Actions ───────────────────────────────────────────────────────────────
    def _generate_salaries(self):
        month = self.month_cb.currentData()
        year  = self.year_cb.currentData()
        bid   = self._branch_id
        if self._session.role == ROLE_ADMIN and hasattr(self, "branch_cb"):
            bid = self.branch_cb.currentData()
        dlg = ConfirmDialog(
            "Generate Salaries",
            f"Generate salary records for {MONTHS_LABELS[month]} {year}?\n"
            "Existing records will be skipped.",
            "Generate", "primary", self
        )
        if dlg.exec():
            result = salary_svc.generate_monthly_salaries(
                month, year, bid, self._session.user_id
            )
            InfoDialog("Done", result["message"],
                       "success" if result["success"] else "error", self).exec()
            if result["success"]: self._load_data()

    def _open_adjust(self, record_id, base, bonus, deduction, notes):
        dlg = SalaryAdjustDialog(record_id, base, bonus, deduction, notes,
                                  self._session.user_id, self)
        dlg.saved.connect(self._load_data)
        dlg.exec()

    def _mark_paid(self, record_id):
        dlg = ConfirmDialog(
            "Mark Salary Paid",
            "Mark this salary record as PAID?\nThis action is recorded in the audit log.",
            "Mark Paid", "primary", self
        )
        if dlg.exec():
            result = salary_svc.mark_salary_paid(record_id, self._session.user_id)
            InfoDialog("Result", result["message"],
                       "success" if result["success"] else "error", self).exec()
            if result["success"]: self._load_data()

    def _view_slip(self, record_id):
        slip_data = salary_svc.get_salary_slip_data(record_id)
        if not slip_data:
            InfoDialog("Error","Salary record not found.","error",self).exec(); return
        dlg = SalarySlipDialog(slip_data, self)
        dlg.exec()

    def refresh(self): self._load_data()


# ── Salary Adjust Dialog ──────────────────────────────────────────────────────
class SalaryAdjustDialog(QDialog):
    saved = pyqtSignal()

    def __init__(self, record_id, base_salary, bonus, deduction, notes, user_id, parent=None):
        super().__init__(parent)
        self._record_id  = record_id
        self._base       = base_salary
        self._user_id    = user_id
        self.setWindowTitle("Adjust Salary")
        self.setMinimumWidth(460)
        self.setStyleSheet("background:#0D1B2A; color:#F0F4FF;")
        self._setup_ui(bonus, deduction, notes)

    def _setup_ui(self, bonus, deduction, notes):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28,24,28,28); layout.setSpacing(14)

        title = QLabel("✏️  Adjust Salary Record")
        title.setStyleSheet("font-size:18px; font-weight:bold; color:#7C3AED;")
        layout.addWidget(title)

        base_lbl = QLabel(f"Base Salary:  Rs. {self._base:,.0f}")
        base_lbl.setStyleSheet("font-size:15px; color:#00F5FF;")
        layout.addWidget(base_lbl)

        grid = QGridLayout(); grid.setSpacing(12)
        grid.setColumnStretch(1,1)

        grid.addWidget(QLabel("Bonus (Rs.):"),0,0)
        self.bonus_spin = QDoubleSpinBox()
        self.bonus_spin.setRange(0,999999); self.bonus_spin.setValue(bonus)
        self.bonus_spin.setPrefix("Rs. "); self.bonus_spin.setMinimumHeight(38)
        self.bonus_spin.valueChanged.connect(self._update_preview)
        grid.addWidget(self.bonus_spin,0,1)

        grid.addWidget(QLabel("Deduction (Rs.):"),1,0)
        self.deduct_spin = QDoubleSpinBox()
        self.deduct_spin.setRange(0,999999); self.deduct_spin.setValue(deduction)
        self.deduct_spin.setPrefix("Rs. "); self.deduct_spin.setMinimumHeight(38)
        self.deduct_spin.valueChanged.connect(self._update_preview)
        grid.addWidget(self.deduct_spin,1,1)

        grid.addWidget(QLabel("Notes:"),2,0)
        self.notes_inp = QLineEdit()
        self.notes_inp.setText(notes or ""); self.notes_inp.setMinimumHeight(36)
        grid.addWidget(self.notes_inp,2,1)
        layout.addLayout(grid)

        self.net_lbl = QLabel()
        self.net_lbl.setStyleSheet("font-size:16px; font-weight:bold; color:#00E676;")
        layout.addWidget(self.net_lbl)
        self._update_preview()

        btn_row = QHBoxLayout(); btn_row.addStretch()
        cancel = QPushButton("Cancel"); cancel.setFixedHeight(38)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        save = QPushButton("💾 Save Adjustment"); save.setMinimumHeight(38)
        save.setStyleSheet(
            "QPushButton{background:#7C3AED;border:none;border-radius:10px;"
            "color:#fff;font-size:14px;font-weight:bold;padding:0 20px;}"
            "QPushButton:hover{background:#8B5CF6;}"
        )
        save.clicked.connect(self._save)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

    def _update_preview(self):
        net = self._base + self.bonus_spin.value() - self.deduct_spin.value()
        self.net_lbl.setText(f"Net Salary:  Rs. {net:,.0f}")

    def _save(self):
        result = salary_svc.update_salary_record(
            self._record_id,
            self.bonus_spin.value(),
            self.deduct_spin.value(),
            self.notes_inp.text().strip(),
            self._user_id
        )
        InfoDialog("Result", result["message"],
                   "success" if result["success"] else "error", self).exec()
        if result["success"]:
            self.saved.emit()
            self.accept()


# ── Salary Slip Dialog ────────────────────────────────────────────────────────
class SalarySlipDialog(QDialog):
    def __init__(self, slip: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Salary Slip")
        self.setMinimumWidth(520)
        self.setMinimumHeight(600)
        self.setStyleSheet("background:#0A0E2A; color:#F0F4FF;")
        self._setup_ui(slip)

    def _setup_ui(self, s):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32,28,32,28); layout.setSpacing(12)

        # Header
        brand = QLabel("💪  FitLife")
        brand.setStyleSheet("font-size:28px;font-weight:900;color:#7C3AED;")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(brand)

        branch_info = QLabel(f"{s['branch_name']}\n{s['branch_address']}\n{s['branch_phone']}")
        branch_info.setStyleSheet("font-size: 13px;color:#9CA3AF;")
        branch_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(branch_info)

        slip_title = QLabel(f"SALARY SLIP — {s['month']} {s['year']}")
        slip_title.setStyleSheet(
            "font-size:16px;font-weight:bold;color:#00F5FF;"
            "background:rgba(0,245,255,0.08);border-radius:8px;padding:8px;"
        )
        slip_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(slip_title)

        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background:rgba(124,58,237,0.4);"); layout.addWidget(div)

        # Employee info
        def row(label, val, color="#F0F4FF"):
            h = QHBoxLayout()
            l = QLabel(label); l.setStyleSheet("color:#6B7280;font-size:13px;"); l.setFixedWidth(180)
            v = QLabel(str(val)); v.setStyleSheet(f"color:{color};font-size:14px;font-weight:600;")
            h.addWidget(l); h.addWidget(v); h.addStretch()
            layout.addLayout(h)

        row("Trainer Name:",    s['trainer_name'])
        row("CNIC:",            s['trainer_cnic'])
        row("Designation:",     s['designation'])
        row("Specialization:",  s['specialization'])
        row("Status:",          s['status'], "#00E676" if s['status']=="Paid" else "#FFB800")
        if s['payment_date']:
            row("Payment Date:", str(s['payment_date']))

        div2 = QFrame(); div2.setFrameShape(QFrame.Shape.HLine)
        div2.setStyleSheet("background:rgba(124,58,237,0.4);"); layout.addWidget(div2)

        row("Base Salary:",   f"Rs. {s['base_salary']:,.0f}", "#F0F4FF")
        row("Bonus:",         f"Rs. {s['bonus']:,.0f}",       "#00E676")
        row("Deduction:",     f"Rs. {s['deduction']:,.0f}",   "#FF2D78")

        div3 = QFrame(); div3.setFrameShape(QFrame.Shape.HLine)
        div3.setStyleSheet("background:rgba(124,58,237,0.4);"); layout.addWidget(div3)

        net_lbl = QLabel(f"Net Salary:  Rs. {s['net_salary']:,.0f}")
        net_lbl.setStyleSheet("font-size:20px;font-weight:bold;color:#00E676;")
        net_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(net_lbl)

        if s.get('notes'):
            row("Notes:", s['notes'], "#9CA3AF")

        layout.addStretch()
        footer = QLabel("This is a system-generated salary slip.")
        footer.setStyleSheet("color:#374151;font-size: 13px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(38)
        close_btn.setStyleSheet(
            "QPushButton{background:rgba(124,58,237,0.2);border:1px solid #7C3AED;"
            "border-radius:10px;color:#7C3AED;font-size:14px;}"
            "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #8B5CF6,stop:1 #7C3AED);}"
        )
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
