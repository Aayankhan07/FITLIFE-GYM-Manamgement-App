"""
FitLife — Expenses Screen
Record and track extra expenses like rent, electricity, maintenance, etc.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QComboBox, QDateEdit, QDoubleSpinBox, QLineEdit,
    QGridLayout
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from ui.components.data_table import DataTable
from ui.components.loading_spinner import LoadingOverlay
from ui.components.confirm_dialog import InfoDialog, ConfirmDialog
from utils.thread_worker import Worker
from config.constants import ROLE_ADMIN, ROLE_MANAGER
import services.expense_service as expense_svc

class ExpensesScreen(QWidget):
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
        container = QWidget()
        container.setStyleSheet("background:transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(28, 24, 28, 24)
        main.setSpacing(20)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("📉 Extra Expenses")
        title.setStyleSheet("font-size:24px; font-weight:bold; color:#F0F4FF;")
        hdr.addWidget(title)
        hdr.addStretch()

        if self._session.role in (ROLE_ADMIN, ROLE_MANAGER):
            add_btn = QPushButton("➕ Record Expense")
            add_btn.setObjectName("btnPrimary")
            add_btn.setMinimumHeight(38)
            add_btn.clicked.connect(self._show_form)
            hdr.addWidget(add_btn)
        main.addLayout(hdr)

        # Filters
        filter_frame = QFrame()
        filter_frame.setStyleSheet("background:rgba(255,255,255,0.04);border:1px solid rgba(124,58,237,0.2);border-radius:12px;")
        fr = QHBoxLayout(filter_frame)
        fr.setContentsMargins(16, 10, 16, 10)
        fr.setSpacing(12)

        import datetime
        now = datetime.datetime.now()
        fr.addWidget(QLabel("Month:"))
        self.month_cb = QComboBox()
        self.month_cb.setFixedHeight(34)
        self.month_cb.addItem("All", None)
        for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1):
            self.month_cb.addItem(m, i)
        self.month_cb.setCurrentIndex(now.month) # 1-based index because "All" is at 0
        fr.addWidget(self.month_cb)

        fr.addWidget(QLabel("Year:"))
        self.year_cb = QComboBox()
        self.year_cb.setFixedHeight(34)
        self.year_cb.addItem("All", None)
        for y in range(now.year - 2, now.year + 1):
            self.year_cb.addItem(str(y), y)
        self.year_cb.setCurrentIndex(3) # The current year
        fr.addWidget(self.year_cb)

        fr.addStretch()
        ref_btn = QPushButton("🔄 Refresh")
        ref_btn.setObjectName("btnSecondary")
        ref_btn.setFixedHeight(34)
        ref_btn.clicked.connect(self._load_data)
        fr.addWidget(ref_btn)
        main.addWidget(filter_frame)

        # Table
        cols = ["ID", "Branch", "Category", "Amount", "Date", "Description", "Recorded By", "Actions"]
        self.table = DataTable(cols)
        main.addWidget(self.table)

        # Add Form (Hidden by default)
        self._form = ExpenseForm(self._session, self)
        self._form.saved.connect(self._on_saved)
        self._form.cancelled.connect(self._form.hide)
        self._form.hide()
        main.addWidget(self._form)

        self._overlay = LoadingOverlay(self)
        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _load_data(self):
        self._overlay.show_loading("Loading expenses...")
        month = self.month_cb.currentData()
        year = self.year_cb.currentData()
        self._worker = Worker(expense_svc.get_expenses_by_branch, self._branch_id, month, year)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.error.connect(lambda e: self._overlay.hide_loading())
        self._worker.start()

    def _on_data_loaded(self, expenses):
        self._overlay.hide_loading()
        rows = []
        for e in expenses:
            rows.append([
                e[0], e[1], e[2], f"Rs. {float(e[3]):,.0f}", str(e[4]),
                e[5] or "", e[6] or "System", ""
            ])
        self.table.set_data(rows)
        self._inject_actions(expenses)

    def _inject_actions(self, expenses):
        if self._session.role not in (ROLE_ADMIN, ROLE_MANAGER):
            return
        tw = self.table.table
        visible = expenses[
            self.table._current_page * self.table._page_size:
            (self.table._current_page + 1) * self.table._page_size
        ]
        for r_idx, e in enumerate(visible):
            eid = e[0]
            del_btn = QPushButton("🗑️")
            del_btn.setToolTip("Delete Expense")
            del_btn.setFixedSize(32, 32)
            del_btn.setStyleSheet(
                "QPushButton{background:rgba(255,45,120,0.1);border:1px solid #FF2D78;"
                "border-radius:6px;color:#FF2D78;}"
                "QPushButton:hover{background:#FF2D78;color:white;}"
            )
            del_btn.clicked.connect(lambda _, i=eid: self._delete_expense(i))
            cell = QWidget()
            l = QHBoxLayout(cell)
            l.setContentsMargins(4, 2, 4, 2)
            l.addWidget(del_btn)
            tw.setCellWidget(r_idx, 7, cell)

    def _show_form(self):
        self._form.reset()
        self._form.show()
        self._form.raise_()

    def _on_saved(self):
        self._form.hide()
        self._load_data()

    def _delete_expense(self, expense_id):
        dlg = ConfirmDialog("Delete Expense", "Are you sure you want to delete this expense record?", "Delete", "danger", self)
        if dlg.exec():
            res = expense_svc.delete_expense(expense_id)
            if res["success"]:
                self._load_data()
            else:
                InfoDialog("Error", res["message"], "error", self).exec()

    def refresh(self):
        self._load_data()

class ExpenseForm(QFrame):
    saved = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setObjectName("glassCard")
        self.setStyleSheet("""
            QFrame#glassCard{background:rgba(255,184,0,0.05);
            border:2px solid rgba(255,184,0,0.3);border-radius:16px;}
        """)
        self._setup_ui()

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(14)

        hdr = QHBoxLayout()
        title = QLabel("📉 Record Extra Expense")
        title.setStyleSheet("font-size:18px;font-weight:bold;color:#FFB800;")
        hdr.addWidget(title)
        hdr.addStretch()
        close = QPushButton("✕")
        close.setFixedSize(28, 28)
        close.setStyleSheet("QPushButton{background:transparent;border:none;color:#9CA3AF;font-size:16px;}")
        close.clicked.connect(self.cancelled.emit)
        hdr.addWidget(close)
        main.addLayout(hdr)

        grid = QGridLayout()
        grid.setSpacing(12)

        grid.addWidget(QLabel("Category:*"), 0, 0)
        self.category = QComboBox()
        self.category.setMinimumHeight(38)
        self.category.addItems(["Rent", "Electricity Bill", "Water Bill", "Internet", "Maintenance", "Cleaning", "Marketing", "Other"])
        grid.addWidget(self.category, 0, 1)

        grid.addWidget(QLabel("Amount (Rs.):*"), 0, 2)
        self.amount = QDoubleSpinBox()
        self.amount.setRange(1, 9999999)
        self.amount.setValue(1000)
        self.amount.setPrefix("Rs. ")
        self.amount.setMinimumHeight(38)
        grid.addWidget(self.amount, 0, 3)

        grid.addWidget(QLabel("Date:*"), 1, 0)
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat("dd/MM/yyyy")
        self.date.setDate(QDate.currentDate())
        self.date.setMinimumHeight(38)
        grid.addWidget(self.date, 1, 1)

        grid.addWidget(QLabel("Description:"), 2, 0)
        self.desc = QLineEdit()
        self.desc.setPlaceholderText("Details about the expense...")
        self.desc.setMinimumHeight(36)
        grid.addWidget(self.desc, 2, 1, 1, 3)

        if self._session.role == ROLE_ADMIN:
            import services.branch_service as branch_svc
            grid.addWidget(QLabel("Branch:*"), 3, 0)
            self.branch = QComboBox()
            self.branch.setMinimumHeight(38)
            for bid, name in branch_svc.get_all_branches_dropdown():
                self.branch.addItem(name, bid)
            grid.addWidget(self.branch, 3, 1, 1, 3)

        main.addLayout(grid)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btnSecondary")
        cancel_btn.setFixedHeight(38)
        cancel_btn.clicked.connect(self.cancelled.emit)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("✅ Save Expense")
        save_btn.setObjectName("btnPrimary")
        save_btn.setMinimumHeight(38)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)
        main.addLayout(btn_row)

    def reset(self):
        self.category.setCurrentIndex(0)
        self.amount.setValue(1000)
        self.date.setDate(QDate.currentDate())
        self.desc.clear()
        if self._session.role == ROLE_ADMIN and hasattr(self, 'branch') and self.branch.count() > 0:
            self.branch.setCurrentIndex(0)

    def _save(self):
        cat = self.category.currentText()
        amt = self.amount.value()
        desc = self.desc.text().strip()
        date_str = self.date.date().toPyDate().strftime("%Y-%m-%d")

        bid = self.branch.currentData() if self._session.role == ROLE_ADMIN else self._session.branch_id

        res = expense_svc.add_expense(
            bid, cat, amt, date_str, desc, self._session.user_id
        )
        if res["success"]:
            self.saved.emit()
            InfoDialog("Success", res["message"], "success", self).exec()
        else:
            InfoDialog("Error", res["message"], "error", self).exec()
