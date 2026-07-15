"""FitLife — Top Bar Component"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from config.constants import SEARCH_DEBOUNCE_MS, TOPBAR_HEIGHT


class TopBar(QWidget):
    """Top application bar with title, search, theme toggle, notifications, user menu."""

    search_changed = pyqtSignal(str)
    theme_toggled  = pyqtSignal()
    logout_clicked = pyqtSignal()
    notif_clicked  = pyqtSignal()
    profile_clicked= pyqtSignal()

    def __init__(self, user_name: str, role: str, parent=None):
        super().__init__(parent)
        self._user_name = user_name
        self._role = role
        self.setObjectName("topbar")
        self.setFixedHeight(TOPBAR_HEIGHT)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(16)

        # ── App Title (left) ──────────────────────────────────────────────────
        title_lbl = QLabel("FitLife")
        title_lbl.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #0066FF; letter-spacing: 1px;"
        )
        layout.addWidget(title_lbl)

        subtitle = QLabel("Male Fitness Chain ERP")
        subtitle.setStyleSheet("font-size: 12px; color: #6B7280;")
        layout.addWidget(subtitle)

        layout.addStretch()

        # ── Global Search (center) ────────────────────────────────────────────
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("  🔍  Global search...")
        self.search_input.setFixedWidth(320)
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.07);
                border: 1px solid rgba(0, 102, 255, 0.3);
                border-radius: 18px;
                padding: 0 16px;
                color: #F0F4FF;
                font-size: 14px;
            }
            QLineEdit:focus { border: 1.5px solid #0066FF; }
        """)
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(SEARCH_DEBOUNCE_MS)
        self._debounce.timeout.connect(
            lambda: self.search_changed.emit(self.search_input.text())
        )
        self.search_input.textChanged.connect(lambda: self._debounce.start())
        layout.addWidget(self.search_input)

        layout.addStretch()

        # ── Theme Toggle ──────────────────────────────────────────────────────
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setObjectName("btnIcon")
        self.theme_btn.setFixedSize(36, 36)
        self.theme_btn.setToolTip("Toggle Dark/Light Theme")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self._on_theme_toggle)
        layout.addWidget(self.theme_btn)

        # ── Notification Bell ─────────────────────────────────────────────────
        self.notif_btn = QPushButton("🔔")
        self.notif_btn.setObjectName("btnIcon")
        self.notif_btn.setFixedSize(36, 36)
        self.notif_btn.setToolTip("Notifications")
        self.notif_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.notif_btn.clicked.connect(self.notif_clicked.emit)
        layout.addWidget(self.notif_btn)

        # ── Separator ─────────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: rgba(0, 102, 255, 0.3);")
        sep.setFixedHeight(28)
        layout.addWidget(sep)

        # ── User Chip ─────────────────────────────────────────────────────────
        user_lbl = QLabel(f"👤  {self._user_name}")
        user_lbl.setStyleSheet("color: #F0F4FF; font-size: 14px; font-weight: 600;")
        layout.addWidget(user_lbl)

        role_lbl = QLabel(f"({self._role})")
        role_lbl.setStyleSheet("color: #0066FF; font-size: 12px;")
        layout.addWidget(role_lbl)

        # ── Logout ────────────────────────────────────────────────────────────
        logout_btn = QPushButton("Sign Out")
        logout_btn.setObjectName("btnSecondary")
        logout_btn.setFixedHeight(34)
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #FF2D78;
                border-radius: 8px;
                color: #FF2D78;
                padding: 0 14px;
                font-size: 13px;
            }
            QPushButton:hover { background: rgba(255,45,120,0.12); }
        """)
        logout_btn.clicked.connect(self.logout_clicked.emit)
        layout.addWidget(logout_btn)

    def _on_theme_toggle(self):
        self.theme_toggled.emit()
        is_dark = self.theme_btn.text() == "🌙"
        self.theme_btn.setText("☀️" if is_dark else "🌙")

    def set_notification_count(self, count: int):
        if count > 0:
            self.notif_btn.setText(f"🔔 {count}")
        else:
            self.notif_btn.setText("🔔")
