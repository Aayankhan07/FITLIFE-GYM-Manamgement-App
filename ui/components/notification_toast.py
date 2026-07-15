"""FitLife — Notification Toast (in-app dropdown notifications)"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QFont


class NotificationItem(QFrame):
    """Single notification row."""
    def __init__(self, title: str, message: str, notif_type: str = "info", parent=None):
        super().__init__(parent)
        self.setObjectName("notifItem")

        colors = {
            "info":    "#3B82F6",
            "success": "#00E676",
            "warning": "#FFB800",
            "error":   "#FF2D78",
            "alert":   "#0066FF",
        }
        color = colors.get(notif_type, "#3B82F6")

        self.setStyleSheet(f"""
            QFrame#notifItem {{
                background: rgba(255,255,255,0.06);
                border-left: 3px solid {color};
                border-radius: 6px;
                padding: 4px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)

        icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", "alert": "🔔"}
        icon_lbl = QLabel(icon.get(notif_type, "ℹ️"))
        icon_lbl.setFixedWidth(24)
        layout.addWidget(icon_lbl)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-weight: 700; font-size: 12px; color: {color};")
        m_lbl = QLabel(message)
        m_lbl.setWordWrap(True)
        m_lbl.setStyleSheet("font-size: 11px; color: #D1D5DB;")
        text_layout.addWidget(t_lbl)
        text_layout.addWidget(m_lbl)
        layout.addLayout(text_layout, 1)


class NotificationPanel(QWidget):
    """Dropdown notification panel from topbar bell."""
    closed = pyqtSignal()

    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self._user_id = user_id
        self.setObjectName("notifPanel")
        self.setFixedWidth(360)
        self.setStyleSheet("""
            QWidget#notifPanel {
                background: rgba(20, 20, 40, 0.96);
                border: 1px solid rgba(0, 102, 255, 0.4);
                border-radius: 14px;
            }
        """)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header row
        hdr = QHBoxLayout()
        title = QLabel("🔔  Notifications")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #F0F4FF;")
        hdr.addWidget(title)
        hdr.addStretch()

        clear_btn = QPushButton("Clear All")
        clear_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#FF2D78;border:none;font-size:11px;}"
            "QPushButton:hover{color:#FF6B9D;}"
        )
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_all)
        hdr.addWidget(clear_btn)

        read_btn = QPushButton("Mark All Read")
        read_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#0066FF;border:none;font-size:11px;}"
            "QPushButton:hover{color:#9B59B6;}"
        )
        read_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        read_btn.clicked.connect(self._mark_all_read)
        hdr.addWidget(read_btn)
        layout.addLayout(hdr)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: rgba(0, 102, 255, 0.3);")
        layout.addWidget(div)

        # Scroll area for notification items
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("border: none; background: transparent;")
        self._scroll.setMaximumHeight(320)

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._notif_layout = QVBoxLayout(self._content)
        self._notif_layout.setContentsMargins(0, 0, 0, 0)
        self._notif_layout.setSpacing(6)
        self._scroll.setWidget(self._content)
        layout.addWidget(self._scroll)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setObjectName("btnSecondary")
        close_btn.setFixedHeight(32)
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)

    def refresh(self):
        """Reload notifications from service."""
        try:
            import services.notification_service as ns
            notifications = ns.get_notifications(self._user_id)

            # Clear existing items
            while self._notif_layout.count():
                item = self._notif_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            if not notifications:
                empty = QLabel("✓  No new notifications")
                empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty.setStyleSheet("color: #6B7280; font-size: 13px; padding: 20px;")
                self._notif_layout.addWidget(empty)
            else:
                for n in notifications:
                    item = NotificationItem(n["title"], n["message"], n["type"])
                    self._notif_layout.addWidget(item)

            self._notif_layout.addStretch()
        except Exception:
            pass

    def _mark_all_read(self):
        try:
            import services.notification_service as ns
            ns.mark_all_read(self._user_id)
            self.refresh()
        except Exception:
            pass

    def _clear_all(self):
        try:
            import services.notification_service as ns
            ns.clear_all(self._user_id)
            self.refresh()
        except Exception:
            pass
