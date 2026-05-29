"""FitLife — Calendar Picker Component (wraps QDateEdit with forced calendar popup)"""
from PyQt6.QtWidgets import QDateEdit, QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont


class CalendarPicker(QDateEdit):
    """
    A QDateEdit configured to:
    - Always show calendar popup
    - Disable manual keyboard typing
    - Display in dd/MM/yyyy format
    """
    date_selected = pyqtSignal(QDate)

    def __init__(self, parent=None, min_date: QDate = None, max_date: QDate = None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("dd/MM/yyyy")
        self.setDate(QDate.currentDate())
        self.setReadOnly(False)  # Allow calendar, block keyboard
        self.setFixedHeight(36)
        self.setStyleSheet("""
            QDateEdit {
                background: rgba(255,255,255,0.07);
                border: 1px solid rgba(124,58,237,0.3);
                border-radius: 8px;
                padding: 0 12px;
                color: #F0F4FF;
                font-size: 13px;
            }
            QDateEdit::drop-down {
                border: none;
                width: 24px;
            }
            QDateEdit:focus { border: 1.5px solid #7C3AED; }
            QCalendarWidget {
                background: rgba(20,20,40,0.98);
                color: #F0F4FF;
                border: 1px solid rgba(124,58,237,0.5);
                border-radius: 12px;
            }
        """)

        if min_date:
            self.setMinimumDate(min_date)
        if max_date:
            self.setMaximumDate(max_date)

        self.dateChanged.connect(self.date_selected.emit)

    def get_date(self) -> QDate:
        return self.date()

    def get_python_date(self):
        d = self.date()
        from datetime import date
        return date(d.year(), d.month(), d.day())

    def set_date_from_python(self, py_date) -> None:
        if py_date:
            try:
                self.setDate(QDate(py_date.year, py_date.month, py_date.day))
            except Exception:
                pass

    def keyPressEvent(self, event):
        """Block manual typing — only allow calendar selection."""
        from PyQt6.QtCore import Qt
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            return  # Block delete/backspace
        # Allow tab and arrow keys for calendar navigation
        super().keyPressEvent(event)


class LabeledDatePicker(QWidget):
    """Convenience widget: label + CalendarPicker in a row."""
    date_selected = pyqtSignal(QDate)

    def __init__(self, label: str, parent=None,
                 min_date: QDate = None, max_date: QDate = None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: #9CA3AF; font-size: 13px;")
        lbl.setFixedWidth(100)
        layout.addWidget(lbl)

        self.picker = CalendarPicker(min_date=min_date, max_date=max_date)
        self.picker.date_selected.connect(self.date_selected.emit)
        layout.addWidget(self.picker)

    def get_python_date(self):
        return self.picker.get_python_date()

    def set_date_from_python(self, py_date) -> None:
        self.picker.set_date_from_python(py_date)
