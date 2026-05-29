"""FitLife — Empty State Component"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class EmptyState(QWidget):
    """
    Shown when a list/table has no data.
    Displays icon, message, and an optional action button.
    """
    action_clicked = pyqtSignal()

    def __init__(self, icon: str = "📭", title: str = "No Data Found",
                 message: str = "There's nothing here yet.",
                 button_text: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        layout.setContentsMargins(40, 40, 40, 40)

        # Icon
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 56px;")
        layout.addWidget(icon_lbl)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #E5E7EB;"
        )
        layout.addWidget(title_lbl)

        # Message
        msg_lbl = QLabel(message)
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet("font-size: 14px; color: #6B7280;")
        layout.addWidget(msg_lbl)

        # Optional button
        if button_text:
            btn = QPushButton(button_text)
            btn.setObjectName("btnPrimary")
            btn.setFixedHeight(40)
            btn.setFixedWidth(180)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(self.action_clicked.emit)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
