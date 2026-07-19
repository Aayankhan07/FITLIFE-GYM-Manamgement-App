"""FitLife — Top Bar Component"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon
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
        self._notif_count = 0
        self.setObjectName("topbar")
        self.setFixedHeight(TOPBAR_HEIGHT)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(16)

        # ── Page Title (left) ──────────────────────────────────────────────────
        self.page_title_lbl = QLabel("Dashboard")
        self.page_title_lbl.setObjectName("topbarPageTitle")
        layout.addWidget(self.page_title_lbl)
 
        layout.addStretch()
 
        # ── Global Search (center) ────────────────────────────────────────────
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Global search...")
        self.search_input.setFixedWidth(320)
        self.search_input.setFixedHeight(36)
        self.search_input.setObjectName("topbarSearch")
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
        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("btnIcon")
        self.theme_btn.setFixedSize(36, 36)
        self.theme_btn.setToolTip("Toggle Dark/Light Theme")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self._on_theme_toggle)
        layout.addWidget(self.theme_btn)
 
        # ── Notification Bell ─────────────────────────────────────────────────
        self.notif_btn = QPushButton()
        self.notif_btn.setObjectName("btnIcon")
        self.notif_btn.setFixedSize(48, 36) # slightly wider to accommodate count text
        self.notif_btn.setToolTip("Notifications")
        self.notif_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.notif_btn.clicked.connect(self.notif_clicked.emit)
        layout.addWidget(self.notif_btn)
 
        # ── Separator ─────────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: rgba(0, 102, 255, 0.2);")
        sep.setFixedHeight(28)
        layout.addWidget(sep)
 
        # ── User Chip ─────────────────────────────────────────────────────────
        self.user_avatar = QLabel()
        layout.addWidget(self.user_avatar)

        user_lbl = QLabel(self._user_name)
        user_lbl.setObjectName("topbarUserLbl")
        layout.addWidget(user_lbl)
 
        role_lbl = QLabel(f"({self._role})")
        role_lbl.setObjectName("topbarRoleLbl")
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
        
        self.update_icons()

    def update_icons(self):
        from ui.components.icons import get_icon
        from ui.theme.theme_manager import ThemeManager
        
        c = ThemeManager.color("text_secondary")
        primary_color = ThemeManager.color("accent_primary")
        
        # User avatar icon
        self.user_avatar.setPixmap(get_icon("user", color=primary_color, size=18).pixmap(18, 18))
        
        # Notification bell icon
        self.notif_btn.setIcon(get_icon("bell", color=c, size=18))
        self.notif_btn.setIconSize(QSize(18, 18))
        
        # Theme toggle icon
        is_dark = ThemeManager.current_theme() == "dark"
        icon_name = "sun" if is_dark else "moon"
        self.theme_btn.setIcon(get_icon(icon_name, color=c, size=18))
        self.theme_btn.setIconSize(QSize(18, 18))

    def _on_theme_toggle(self):
        self.theme_toggled.emit()
        self.update_icons()
 
    def set_notification_count(self, count: int):
        self._notif_count = count
        if count > 0:
            self.notif_btn.setText(f" {count}")
        else:
            self.notif_btn.setText("")
            
    def set_page_title(self, title: str):
        self.page_title_lbl.setText(title)
