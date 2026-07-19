"""
FitLife — Data Table Component
Reusable paginated table with search, filter bar, and action buttons.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from config.constants import PAGE_SIZE, SEARCH_DEBOUNCE_MS


class DataTable(QWidget):
    """
    A glass-styled data table with:
    - Configurable columns
    - Built-in search with debounce
    - Pagination (25 rows/page)
    - Row selection signals
    - Per-row action buttons support
    """

    row_selected = pyqtSignal(int)          # emits row index
    row_double_clicked = pyqtSignal(int)    # emits row index

    def __init__(self, columns: list[str], parent=None):
        super().__init__(parent)
        self._columns = columns
        self._all_data: list[list] = []
        self._filtered_data: list[list] = []
        self._current_page = 0
        self._page_size = PAGE_SIZE
        self._action_builders: list = []   # callables that return list of QPushButton
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        # ── Search Bar ────────────────────────────────────────────────────────
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("  Search...")
        self.search_input.setObjectName("searchInput")
        self.search_input.setMinimumHeight(38)
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(SEARCH_DEBOUNCE_MS)
        self._debounce_timer.timeout.connect(self._apply_search)
        self.search_input.textChanged.connect(lambda: self._debounce_timer.start())
 
        self.result_label = QLabel("0 records")
        self.result_label.setObjectName("labelMuted")
        self.result_label.setStyleSheet("color: #6B7280; font-size: 13px;")
 
        search_row.addWidget(self.search_input)
        search_row.addWidget(self.result_label)
        layout.addLayout(search_row)
 
        # ── Table ─────────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(len(self._columns))
        self.table.setHorizontalHeaderLabels(self._columns)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(56)  # Increase row height
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.setMinimumHeight(300)
        self.table.cellClicked.connect(lambda r, c: self.row_selected.emit(r))
        self.table.cellDoubleClicked.connect(lambda r, c: self.row_double_clicked.emit(r))
        layout.addWidget(self.table)

        # ── Pagination ────────────────────────────────────────────────────────
        pag_row = QHBoxLayout()
        self.prev_btn = QPushButton("Prev")
        self.prev_btn.setObjectName("btnSecondary")
        self.prev_btn.setFixedHeight(38)
        self.prev_btn.clicked.connect(self._prev_page)
 
        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setObjectName("labelMuted")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet("color: #9CA3AF; font-size: 13px;")
 
        self.next_btn = QPushButton("Next")
        self.next_btn.setObjectName("btnSecondary")
        self.next_btn.setFixedHeight(38)
        self.next_btn.clicked.connect(self._next_page)

        pag_row.addStretch()
        pag_row.addWidget(self.prev_btn)
        pag_row.addWidget(self.page_label)
        pag_row.addWidget(self.next_btn)
        pag_row.addStretch()
        layout.addLayout(pag_row)

    # ── Public API ────────────────────────────────────────────────────────────
    def set_data(self, data: list[list]):
        """Load data into the table. Each row is a list of values."""
        self._all_data = data
        self._filtered_data = data
        self._current_page = 0
        self._apply_search()

    def add_action_column(self, builder_func):
        """
        Register a function that receives (row_index, row_data) and
        returns a list of QPushButton widgets to place in the Actions column.
        """
        self._action_builders.append(builder_func)

    def get_selected_row_data(self) -> list | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        start = self._current_page * self._page_size
        idx = start + row
        if idx < len(self._filtered_data):
            return self._filtered_data[idx]
        return None

    def refresh(self):
        self._render_page()

    # ── Internal ──────────────────────────────────────────────────────────────
    def _apply_search(self):
        query = self.search_input.text().strip().lower()
        if query:
            self._filtered_data = [
                row for row in self._all_data
                if any(query in str(cell).lower() for cell in row)
            ]
        else:
            self._filtered_data = self._all_data
        self._current_page = 0
        self._render_page()

    def _render_page(self):
        start = self._current_page * self._page_size
        end = start + self._page_size
        page_data = self._filtered_data[start:end]
        total_pages = max(1, math.ceil(len(self._filtered_data) / self._page_size))

        self.table.setRowCount(0)
        for r_idx, row in enumerate(page_data):
            self.table.insertRow(r_idx)
            col_offset = 0
            for c_idx, cell in enumerate(row):
                item = QTableWidgetItem(str(cell) if cell is not None else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(r_idx, c_idx, item)
                col_offset = c_idx + 1

        self.result_label.setText(f"{len(self._filtered_data)} record(s)")
        self.page_label.setText(f"Page {self._current_page + 1} of {total_pages}")
        self.prev_btn.setEnabled(self._current_page > 0)
        self.next_btn.setEnabled(self._current_page < total_pages - 1)

        # Dynamic header sizing to prevent badge/button overlap and fill empty space
        header = self.table.horizontalHeader()
        stretch_col = -1
        for i, col in enumerate(self._columns):
            name_lower = col.lower()
            if "name" in name_lower or "member" in name_lower or "description" in name_lower or "branch" in name_lower:
                stretch_col = i
                break
        header.setStretchLastSection(stretch_col == -1)
        for c_idx in range(self.table.columnCount()):
            col_name = self._columns[c_idx].lower()
            if c_idx == stretch_col:
                header.setSectionResizeMode(c_idx, QHeaderView.ResizeMode.Stretch)
            elif "status" in col_name:
                header.setSectionResizeMode(c_idx, QHeaderView.ResizeMode.Interactive)
                self.table.setColumnWidth(c_idx, 105)
            elif "actions" in col_name:
                header.setSectionResizeMode(c_idx, QHeaderView.ResizeMode.Interactive)
                self.table.setColumnWidth(c_idx, 220)
            else:
                header.setSectionResizeMode(c_idx, QHeaderView.ResizeMode.ResizeToContents)

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_page()

    def _next_page(self):
        total_pages = max(1, math.ceil(len(self._filtered_data) / self._page_size))
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._render_page()


import math  # noqa: E402 — needed at module level after class
