"""
FitLife — Billing Screen
Payment recording, fee status overview, invoice view, monthly filters.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QDateEdit, QDoubleSpinBox,
    QLineEdit, QTabWidget, QTableWidget, QTableWidgetItem,
    QSplitter, QGridLayout, QTextEdit, QHeaderView, QStackedWidget
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime

from ui.components.glass_card import KPICard, StatusBadge, SectionHeader
from ui.components.confirm_dialog import ConfirmDialog, InfoDialog
from ui.components.data_table import DataTable
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
import services.billing_service as billing_svc
import services.member_service as member_svc
import services.membership_service as membership_svc
from config.constants import PAYMENT_METHODS, ROLE_ADMIN, ROLE_MANAGER


class BillingScreen(QWidget):
    """Billing module with fee collection, status overview, and invoice list."""

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
        title = QLabel("💰  Billing & Payments")
        title.setStyleSheet("font-size:26px; font-weight:900; color:#F0F4FF;")
        hdr.addWidget(title); hdr.addStretch()
        rec_btn = QPushButton("➕  Record Payment")
        rec_btn.setObjectName("btnPrimary")
        rec_btn.setMinimumHeight(40)
        rec_btn.clicked.connect(self._show_record_form)
        hdr.addWidget(rec_btn); main.addLayout(hdr)

        # ── KPI row ───────────────────────────────────────────────────────────
        krow = QHBoxLayout(); krow.setSpacing(14)
        self._kpi_collected  = KPICard("Collected (Month)", "—", "💰","","#00E676")
        self._kpi_pending    = KPICard("Pending",           "—", "⚠️","","#FFB800")
        self._kpi_paid_count = KPICard("Paid Invoices",     "—", "✅","","#0066FF")
        self._kpi_overdue    = KPICard("Overdue",           "—", "🔴","","#FF2D78")
        for k in [self._kpi_collected, self._kpi_pending, self._kpi_paid_count, self._kpi_overdue]:
            krow.addWidget(k)
        main.addLayout(krow)

        # ── Month Filter ──────────────────────────────────────────────────────
        filter_frame = QFrame()
        filter_frame.setStyleSheet("background:rgba(255,255,255,0.04);border:1px solid rgba(0, 102, 255, 0.2);border-radius:12px;")
        fr = QHBoxLayout(filter_frame)
        fr.setContentsMargins(16,10,16,10); fr.setSpacing(12)

        now = datetime.now()
        fr.addWidget(QLabel("Month:"))
        self.month_cb = QComboBox()
        self.month_cb.setFixedHeight(34)
        for i, m in enumerate(["Jan","Feb","Mar","Apr","May","Jun",
                                "Jul","Aug","Sep","Oct","Nov","Dec"], 1):
            self.month_cb.addItem(m, i)
        self.month_cb.setCurrentIndex(now.month - 1)
        fr.addWidget(self.month_cb)

        fr.addWidget(QLabel("Year:"))
        self.year_cb = QComboBox()
        self.year_cb.setFixedHeight(34)
        for y in range(now.year - 2, now.year + 1):
            self.year_cb.addItem(str(y), y)
        self.year_cb.setCurrentIndex(2)
        fr.addWidget(self.year_cb)

        fr.addWidget(QLabel("Status:"))
        self.status_cb = QComboBox()
        self.status_cb.setFixedHeight(34)
        self.status_cb.addItem("All", None)
        for s in ["Paid","Unpaid","Partial","Overdue"]:
            self.status_cb.addItem(s, s)
        fr.addWidget(self.status_cb)

        fr.addStretch()
        ref_btn = QPushButton("🔄 Refresh")
        ref_btn.setObjectName("btnSecondary")
        ref_btn.setFixedHeight(34)
        ref_btn.clicked.connect(self._load_data)
        fr.addWidget(ref_btn)
        main.addWidget(filter_frame)

        # ── Tabs: Payments | Unpaid Members ───────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane{background:rgba(255,255,255,0.04);
            border:1px solid rgba(0, 102, 255, 0.2);border-radius:12px;}
            QTabBar::tab{background:transparent;color:#9CA3AF;padding:10px 20px;
            border:none;border-bottom:2px solid transparent;}
            QTabBar::tab:selected{color:#0066FF;border-bottom:2px solid #0066FF;font-weight:bold;}
        """)

        # Tab 1: Payment history
        pay_tab = QWidget(); pay_tab.setStyleSheet("background:transparent;")
        ptl = QVBoxLayout(pay_tab); ptl.setContentsMargins(12,12,12,12)
        cols = ["ID","Member","CNIC","Branch","Amount","Date","Method","Status","Invoice #","Actions"]
        self.pay_table = DataTable(cols)
        ptl.addWidget(self.pay_table)
        self.tabs.addTab(pay_tab, "📄 Payments")

        # Tab 2: Unpaid members
        unpaid_tab = QWidget(); unpaid_tab.setStyleSheet("background:transparent;")
        utl = QVBoxLayout(unpaid_tab); utl.setContentsMargins(12,12,12,12)
        self.unpaid_table = QTableWidget()
        self.unpaid_table.setColumnCount(7)
        self.unpaid_table.setHorizontalHeaderLabels(
            ["Member","Phone","Email","Plan","Due Amount","Expiry","Quick Pay"]
        )
        self.unpaid_table.verticalHeader().setVisible(False)
        self.unpaid_table.horizontalHeader().setStretchLastSection(True)
        self.unpaid_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.unpaid_table.setStyleSheet("""
            QTableWidget{background:transparent;border:none;color:#F0F4FF;}
            QTableWidget::item{padding:8px;border-bottom:1px solid rgba(0, 102, 255, 0.15);}
            QHeaderView::section{background:rgba(255,45,120,0.2);color:#FF2D78;
            padding:10px;border:none;font-weight:bold;}
        """)
        utl.addWidget(self.unpaid_table)
        self.tabs.addTab(unpaid_tab, "⚠️ Unpaid Members")
        main.addWidget(self.tabs)

        # Record Payment form (stacked — hidden by default)
        self._record_form = PaymentRecordForm(self._session, self)
        self._record_form.saved.connect(self._on_payment_saved)
        self._record_form.cancelled.connect(self._record_form.hide)
        self._record_form.hide()
        main.addWidget(self._record_form)

        self._overlay = LoadingOverlay(self)
        scroll.setWidget(container)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

    # ── Data ──────────────────────────────────────────────────────────────────
    def _load_data(self):
        self._overlay.show_loading("Loading billing data...")
        month = self.month_cb.currentData()
        year  = self.year_cb.currentData()
        status = self.status_cb.currentData()
        self._worker = Worker(self._fetch, month, year, status)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.error.connect(lambda e: self._overlay.hide_loading())
        self._worker.start()

    def _fetch(self, month, year, status):
        payments = billing_svc.get_payments_by_branch(
            self._branch_id, status=status, month=month, year=year
        )
        summary  = billing_svc.get_fee_status_summary(self._branch_id)
        unpaid   = billing_svc.get_unpaid_members(self._branch_id)
        return {"payments": payments, "summary": summary, "unpaid": unpaid}

    def _on_data_loaded(self, data):
        self._overlay.hide_loading()
        s = data["summary"]
        self._kpi_collected.set_value(f"Rs. {s['collected']:,.0f}")
        self._kpi_pending.set_value(f"Rs. {s['outstanding']:,.0f}")
        self._kpi_paid_count.set_value(str(s["paid_count"]))
        self._kpi_overdue.set_value(str(s["overdue_count"]))

        # Payments table
        rows = []
        for p in data["payments"]:
            rows.append([
                p[0], p[1], p[2], p[3],
                f"Rs. {float(p[4]):,.0f}", str(p[5]),
                p[6], p[7], p[8], ""
            ])
        self.pay_table.set_data(rows)
        self._inject_payment_actions(data["payments"])

        # Unpaid table
        self.unpaid_table.setRowCount(0)
        for u in data["unpaid"]:
            r = self.unpaid_table.rowCount()
            self.unpaid_table.insertRow(r)
            self.unpaid_table.setItem(r, 0, QTableWidgetItem(u[1]))
            self.unpaid_table.setItem(r, 1, QTableWidgetItem(u[2]))
            self.unpaid_table.setItem(r, 2, QTableWidgetItem(u[3] or "—"))
            self.unpaid_table.setItem(r, 3, QTableWidgetItem(u[5] or "—"))
            amount = float(u[6] or 0)
            self.unpaid_table.setItem(r, 4, QTableWidgetItem(f"Rs. {amount:,.0f}"))
            self.unpaid_table.setItem(r, 5, QTableWidgetItem(str(u[4]) if u[4] else "—"))
            pay_btn = QPushButton("💰 Pay Now")
            pay_btn.setFixedHeight(32)
            pay_btn.setStyleSheet(
                "QPushButton{background:rgba(0,230,118,0.15);border:1px solid #00E676;"
                "border-radius:6px;color:#00E676;font-size: 13px;padding:0 10px;}"
                "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #33FF99,stop:1 #00E676);}"
            )
            pay_btn.clicked.connect(lambda _, mid=u[0], amt=amount: self._quick_pay(mid, amt))
            self.unpaid_table.setCellWidget(r, 6, pay_btn)

    def _inject_payment_actions(self, payments):
        tw = self.pay_table.table
        visible = payments[
            self.pay_table._current_page * self.pay_table._page_size:
            (self.pay_table._current_page + 1) * self.pay_table._page_size
        ]
        for r_idx, p in enumerate(visible):
            pid = p[0]
            cell = QWidget()
            bl = QHBoxLayout(cell); bl.setContentsMargins(4,2,4,2); bl.setSpacing(4)
            view_btn = QPushButton("🧾 Invoice")
            view_btn.setFixedHeight(32)
            view_btn.setStyleSheet(
                "QPushButton{background:rgba(0,245,255,0.15);border:1px solid #00F5FF;"
                "border-radius:6px;color:#00F5FF;font-size: 13px;padding:0 8px;}"
                "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00B8D9,stop:1 #00F5FF);}"
            )
            view_btn.clicked.connect(lambda _, i=pid: self._view_invoice(i))
            bl.addWidget(view_btn)
            tw.setCellWidget(r_idx, 9, cell)
            tw.setCellWidget(r_idx, 7, StatusBadge(p[7]))

    def _show_record_form(self):
        self._record_form.reset()
        self._record_form.show()
        self._record_form.raise_()

    def _quick_pay(self, member_id: int, amount: float):
        self._record_form.preset_member(member_id, amount)
        self._record_form.show()
        self._record_form.raise_()

    def _on_payment_saved(self):
        self._record_form.hide()
        self._load_data()

    def _view_invoice(self, payment_id: int):
        dlg = InvoiceDialog(payment_id, self)
        dlg.exec()

    def refresh(self): self._load_data()


# ── Payment Record Form ────────────────────────────────────────────────────────
class PaymentRecordForm(QFrame):
    saved     = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setObjectName("glassCard")
        self.setStyleSheet("""
            QFrame#glassCard{background:rgba(0,230,118,0.05);
            border:2px solid rgba(0,230,118,0.3);border-radius:16px;}
        """)
        self._setup_ui()

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(24,20,24,20); main.setSpacing(14)

        hdr = QHBoxLayout()
        title = QLabel("💰  Record Payment")
        title.setStyleSheet("font-size:18px;font-weight:bold;color:#00E676;")
        hdr.addWidget(title); hdr.addStretch()
        close = QPushButton("✕")
        close.setFixedSize(28,28)
        close.setStyleSheet("QPushButton{background:transparent;border:none;color:#9CA3AF;font-size:16px;}")
        close.clicked.connect(self.cancelled.emit)
        hdr.addWidget(close); main.addLayout(hdr)

        grid = QGridLayout()
        grid.setSpacing(12); grid.setColumnStretch(1,1); grid.setColumnStretch(3,1)

        grid.addWidget(QLabel("Member:*"),0,0)
        self.member_cb = QComboBox(); self.member_cb.setMinimumHeight(38)
        self.member_cb.currentIndexChanged.connect(self._on_member_changed)
        grid.addWidget(self.member_cb,0,1)

        grid.addWidget(QLabel("Amount (Rs.):*"),0,2)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0,9999999); self.amount_spin.setValue(0)
        self.amount_spin.setPrefix("Rs. "); self.amount_spin.setMinimumHeight(38)
        grid.addWidget(self.amount_spin,0,3)

        grid.addWidget(QLabel("Payment Method:*"),1,0)
        self.method_cb = QComboBox(); self.method_cb.setMinimumHeight(38)
        for m in PAYMENT_METHODS: self.method_cb.addItem(m,m)
        grid.addWidget(self.method_cb,1,1)

        grid.addWidget(QLabel("Payment Date:*"),1,2)
        self.pay_date = QDateEdit(); self.pay_date.setCalendarPopup(True)
        self.pay_date.setDisplayFormat("dd/MM/yyyy")
        self.pay_date.setDate(QDate.currentDate()); self.pay_date.setMinimumHeight(38)
        grid.addWidget(self.pay_date,1,3)

        grid.addWidget(QLabel("Notes:"),2,0)
        self.notes = QLineEdit(); self.notes.setPlaceholderText("Optional notes...")
        self.notes.setMinimumHeight(36)
        grid.addWidget(self.notes,2,1,1,3)
        main.addLayout(grid)

        # Current plan info
        self.plan_info = QLabel("")
        self.plan_info.setStyleSheet("color:#00F5FF;font-size: 13px;")
        main.addWidget(self.plan_info)

        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel"); cancel_btn.setObjectName("btnSecondary")
        cancel_btn.setFixedHeight(38); cancel_btn.clicked.connect(self.cancelled.emit)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("✅  Record Payment"); save_btn.setObjectName("btnPrimary")
        save_btn.setMinimumHeight(38); save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)
        main.addLayout(btn_row)

        self._populate_members()

    def _populate_members(self):
        self.member_cb.clear()
        self.member_cb.addItem("— Select Member —", None)
        branch_id = self._session.branch_id
        members = member_svc.get_all_members(branch_id=branch_id, status="Active")
        self._members_map = {m[0]: m for m in members}
        for m in members:
            self.member_cb.addItem(f"{m[1]}  ({m[2]})", m[0])

    def _on_member_changed(self):
        mid = self.member_cb.currentData()
        if mid and mid in self._members_map:
            m = self._members_map[mid]
            plan_name = m[7] or "—"
            expiry = str(m[8]) if m[8] else "—"
            self.plan_info.setText(f"Plan: {plan_name}  |  Expiry: {expiry}")
        else:
            self.plan_info.setText("")

    def preset_member(self, member_id: int, amount: float):
        self._populate_members()
        idx = self.member_cb.findData(member_id)
        if idx >= 0: self.member_cb.setCurrentIndex(idx)
        self.amount_spin.setValue(amount)
        self.member_cb.setEnabled(False)

    def reset(self):
        self._populate_members()
        self.member_cb.setCurrentIndex(0)
        self.amount_spin.setValue(0)
        self.notes.clear()
        self.pay_date.setDate(QDate.currentDate())
        self.member_cb.setEnabled(True)

    def _save(self):
        mid = self.member_cb.currentData()
        amt = self.amount_spin.value()
        if not mid:
            InfoDialog("Error","Please select a member.","error",self).exec(); return
        if amt <= 0:
            InfoDialog("Error","Amount must be greater than 0.","error",self).exec(); return

        dlg = ConfirmDialog(
            "Confirm Payment",
            f"Record payment of Rs.{amt:,.0f} for\n'{self.member_cb.currentText()}'?",
            "Record Payment", "primary", self
        )
        if dlg.exec():
            result = billing_svc.record_payment(
                member_id=mid,
                amount=amt,
                payment_method=self.method_cb.currentData(),
                payment_date=self.pay_date.date().toPyDate(),
                membership_id=None,
                recorded_by=self._session.user_id,
                notes=self.notes.text().strip()
            )
            InfoDialog("Result", result["message"],
                       "success" if result["success"] else "error", self).exec()
            if result["success"]: self.saved.emit()


# ── Invoice Dialog ─────────────────────────────────────────────────────────────
class InvoiceDialog(QWidget):
    """Read-only invoice viewer."""

    def __init__(self, payment_id: int, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.setWindowTitle("Invoice")
        self.setMinimumSize(520, 580)
        self.setStyleSheet("background:#0A0E2A; color:#F0F4FF;")
        self._setup_ui(payment_id)

    def _setup_ui(self, payment_id):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30,30,30,30); layout.setSpacing(16)
        p = billing_svc.get_payment_by_id(payment_id)
        if not p:
            layout.addWidget(QLabel("Invoice not found."))
            return

        title = QLabel("🧾  INVOICE")
        title.setStyleSheet("font-size:26px; font-weight:900; color:#0066FF; text-align:center;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        inv_num = QLabel(p[12])
        inv_num.setStyleSheet("font-size:14px; color:#00F5FF; text-align:center;")
        inv_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(inv_num)

        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background:rgba(0, 102, 255, 0.4);"); layout.addWidget(line)

        def row(label, val):
            h = QHBoxLayout()
            l = QLabel(label); l.setStyleSheet("color:#9CA3AF; font-size:13px;")
            v = QLabel(str(val)); v.setStyleSheet("color:#F0F4FF; font-size:14px; font-weight:600;")
            l.setFixedWidth(160)
            h.addWidget(l); h.addWidget(v); h.addStretch()
            layout.addLayout(h)

        row("Branch:",        p[5])
        row("Member:",        p[1])
        row("CNIC:",          p[2])
        row("Contact:",       p[4])
        row("Membership Plan:",p[7] or "—")
        row("Payment Date:",  str(p[9]))
        row("Method:",        p[10])
        row("Amount:",        f"Rs. {float(p[8]):,.0f}")
        row("Status:",        p[11])
        if p[13]: row("Notes:", p[13])

        line2 = QFrame(); line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet("background:rgba(0, 102, 255, 0.4);"); layout.addWidget(line2)

        total_lbl = QLabel(f"Total:  Rs. {float(p[8]):,.2f}")
        total_lbl.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#00E676;text-align:right;"
        )
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(total_lbl)

        footer = QLabel("Thank you for choosing FitLife!")
        footer.setStyleSheet("color:#6B7280;font-size: 13px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("btnSecondary")
        close_btn.setFixedHeight(38)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def exec(self):
        self.show()
