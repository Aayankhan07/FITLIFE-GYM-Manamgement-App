"""
FitLife — Loading Spinner & Toast Notification Components
"""
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen
import math


class LoadingSpinner(QWidget):
    """Animated circular loading spinner overlay."""

    def __init__(self, parent=None, color: str = "#7C3AED", size: int = 50):
        super().__init__(parent)
        self._color = QColor(color)
        self._size = size
        self._angle = 0
        self.setFixedSize(size, size)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self.hide()

    def _rotate(self):
        self._angle = (self._angle + 8) % 360
        self.update()

    def start(self):
        self._timer.start(20)
        self.show()

    def stop(self):
        self._timer.stop()
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self._color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        rect = QRect(6, 6, self._size - 12, self._size - 12)
        painter.drawArc(rect, self._angle * 16, 270 * 16)


class LoadingOverlay(QWidget):
    """Full-widget loading overlay with spinner and message."""

    def __init__(self, parent=None, message: str = "Loading..."):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background: rgba(10,14,42,0.75); border-radius: 16px;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        self.spinner = LoadingSpinner(self, size=60)
        layout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignCenter)

        self.msg_lbl = QLabel(message)
        self.msg_lbl.setStyleSheet("color: #F0F4FF; font-size: 14px; background: transparent;")
        self.msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.msg_lbl)
        self.hide()

    def show_loading(self, message: str = "Loading..."):
        self.msg_lbl.setText(message)
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.raise_()
        self.show()
        self.spinner.start()

    def hide_loading(self):
        self.spinner.stop()
        self.hide()


# ─── Toast Notification ───────────────────────────────────────────────────────
class ToastNotification(QFrame):
    """Slide-in toast notification from top-right."""

    COLORS = {
        "success": ("#00E676", "#003319"),
        "error":   ("#FF2D78", "#2D0014"),
        "warning": ("#FFB800", "#2D2000"),
        "info":    ("#00F5FF", "#002D33"),
    }
    ICONS = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(340)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        self._layout.setSpacing(12)

        self.icon_lbl = QLabel()
        self.icon_lbl.setStyleSheet("font-size: 20px; background: transparent;")
        self.icon_lbl.setFixedWidth(28)
        self._layout.addWidget(self.icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.title_lbl = QLabel()
        self.title_lbl.setStyleSheet("font-weight: bold; font-size: 14px; background: transparent;")
        self.msg_lbl = QLabel()
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet("font-size: 12px; background: transparent;")
        text_col.addWidget(self.title_lbl)
        text_col.addWidget(self.msg_lbl)
        self._layout.addLayout(text_col)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, title: str, message: str, toast_type: str = "info", duration: int = 4000):
        fg, bg = self.COLORS.get(toast_type, ("#00F5FF", "#002D33"))
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {fg};
                border-radius: 12px;
            }}
        """)
        self.icon_lbl.setText(self.ICONS.get(toast_type, "ℹ️"))
        self.title_lbl.setText(title)
        self.title_lbl.setStyleSheet(f"font-weight:bold; font-size:14px; color:{fg}; background:transparent;")
        self.msg_lbl.setText(message)
        self.msg_lbl.setStyleSheet(f"font-size:12px; color:#F0F4FF; background:transparent;")
        self.adjustSize()

        # Position top-right of parent
        if self.parent():
            pr = self.parent().rect()
            x = pr.right() - self.width() - 20
            y = pr.top() + 80
            self.move(x, y)

        self.show()
        self.raise_()
        self._timer.start(duration)
