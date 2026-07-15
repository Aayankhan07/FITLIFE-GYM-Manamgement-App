"""FitLife — Finance Center Module
Replaces individual Billing and Salary panels with a unified finance dashboard.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel
)
from PyQt6.QtCore import Qt
from ui.screens.billing.billing_screen import BillingScreen
from ui.screens.billing.salary_screen import SalaryScreen


class FinanceCenterModule(QWidget):
    """Unified module combining Billing and Salary."""

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setStyleSheet("background:transparent;")
        self._setup_ui()

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(28, 24, 28, 24)
        main.setSpacing(16)

        # Header + Tab buttons
        hdr_row = QHBoxLayout()
        title = QLabel("💳  Finance Center")
        title.setStyleSheet("font-size:26px; font-weight:900; color:#F0F4FF;")
        hdr_row.addWidget(title)
        hdr_row.addStretch()

        self.btn_billing = QPushButton("📝 Member Invoices")
        self.btn_billing.setMinimumHeight(38)
        self.btn_billing.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_billing.setCheckable(True)
        self.btn_billing.setChecked(True)
        self.btn_billing.clicked.connect(lambda: self._switch_tab(0))

        self.btn_salary = QPushButton("💸 Staff Payroll")
        self.btn_salary.setMinimumHeight(38)
        self.btn_salary.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_salary.setCheckable(True)
        self.btn_salary.clicked.connect(lambda: self._switch_tab(1))

        self.btn_expenses = QPushButton("📉 Extra Expenses")
        self.btn_expenses.setMinimumHeight(38)
        self.btn_expenses.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_expenses.setCheckable(True)
        self.btn_expenses.clicked.connect(lambda: self._switch_tab(2))

        self._style_tabs()

        hdr_row.addWidget(self.btn_billing)
        hdr_row.addWidget(self.btn_salary)
        hdr_row.addWidget(self.btn_expenses)
        main.addLayout(hdr_row)

        # Stacked Widget for screens
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background:transparent;")
        
        self.billing_screen = BillingScreen(self._session)
        self.salary_screen = SalaryScreen(self._session)
        from ui.screens.billing.expenses_screen import ExpensesScreen
        self.expenses_screen = ExpensesScreen(self._session)

        self.billing_screen.layout().setContentsMargins(0, 0, 0, 0)
        self.salary_screen.layout().setContentsMargins(0, 0, 0, 0)
        self.expenses_screen.layout().setContentsMargins(0, 0, 0, 0)

        self.stack.addWidget(self.billing_screen)
        self.stack.addWidget(self.salary_screen)
        self.stack.addWidget(self.expenses_screen)
        main.addWidget(self.stack)

    def _style_tabs(self):
        active_style = """
            QPushButton {
                background: rgba(0, 102, 255, 0.2); border: 1px solid #0066FF;
                border-radius: 10px; color: #FFFFFF; font-weight: bold; padding: 0 20px;
            }
        """
        inactive_style = """
            QPushButton {
                background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
                border-radius: 10px; color: #9CA3AF; font-weight: 600; padding: 0 20px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.1); color: #F0F4FF; }
        """
        
        self.btn_billing.setStyleSheet(active_style if self.btn_billing.isChecked() else inactive_style)
        self.btn_salary.setStyleSheet(active_style if self.btn_salary.isChecked() else inactive_style)
        self.btn_expenses.setStyleSheet(active_style if self.btn_expenses.isChecked() else inactive_style)

    def _switch_tab(self, index: int):
        self.btn_billing.setChecked(index == 0)
        self.btn_salary.setChecked(index == 1)
        self.btn_expenses.setChecked(index == 2)
        self._style_tabs()
        self.stack.setCurrentIndex(index)
        
        if index == 0:
            self.billing_screen.refresh()
        elif index == 1:
            self.salary_screen.refresh()
        else:
            self.expenses_screen.refresh()

    def refresh(self):
        idx = self.stack.currentIndex()
        if idx == 0:
            self.billing_screen.refresh()
        elif idx == 1:
            self.salary_screen.refresh()
        else:
            self.expenses_screen.refresh()
