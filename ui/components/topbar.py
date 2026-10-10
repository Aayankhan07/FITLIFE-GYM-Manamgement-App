"""FitLife — Redesigned Top Bar Component (Matching GYM-MANAGEMENT)"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon
from config.constants import SEARCH_DEBOUNCE_MS
from ui.theme.theme_manager import ThemeManager
from ui.components.icons import get_icon


class TopBar(QWidget):
    """
    Editorial TopBar matching GYM-MANAGEMENT:
    - Left Page Title with subtle breadcrumb
    - Centered pill global search box
    - Alert notification bell badge
    - Redesigned user role capsule
    - Modern sign out action
    """

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
        self.setFixedHeight(64)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)

        # ── 1. Page Title ──────────────────────────────────────────────────────
        self.page_title_lbl = QLabel("Overview")
        self.page_title_lbl.setStyleSheet("""
            font-size: 18px;
            font-weight: 800;
            letter-spacing: -0.2px;
        """)
        layout.addWidget(self.page_title_lbl)

        layout.addStretch()

        # ── 2. Pill Global Search Box ──────────────────────────────────────────
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search athletes, plans, equipment...")
        self.search_input.setFixedWidth(340)
        self.search_input.setFixedHeight(38)
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(SEARCH_DEBOUNCE_MS)
        self._debounce.timeout.connect(
            lambda: self.search_changed.emit(self.search_input.text())
        )
        self.search_input.textChanged.connect(lambda: self._debounce.start())
        layout.addWidget(self.search_input)

        layout.addStretch()

        # ── 3. Theme Toggle Button ────────────────────────────────────────────
        self.theme_btn = QPushButton()
        self.theme_btn.setFixedSize(40, 40)
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.setToolTip("Toggle Light/Dark Theme")
        self.theme_btn.clicked.connect(self.theme_toggled.emit)
        layout.addWidget(self.theme_btn)

        # ── 3b. Notification Bell with Badge ──────────────────────────────────
        self.notif_btn = QPushButton()
        self.notif_btn.setFixedSize(40, 40)
        self.notif_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.notif_btn.setToolTip("Live Alerts & Maintenance")
        self.notif_btn.clicked.connect(self.notif_clicked.emit)
        layout.addWidget(self.notif_btn)

        # ── 4. Separator ──────────────────────────────────────────────────────
        self.sep = QFrame()
        self.sep.setFrameShape(QFrame.Shape.VLine)
        self.sep.setFixedHeight(24)
        layout.addWidget(self.sep)

        # ── 5. User Profile Capsule ───────────────────────────────────────────
        self.user_capsule = QFrame()
        self.user_capsule.setFixedHeight(40)
        capsule_layout = QHBoxLayout(self.user_capsule)
        capsule_layout.setContentsMargins(10, 4, 12, 4)
        capsule_layout.setSpacing(8)

        self.user_avatar = QLabel()
        capsule_layout.addWidget(self.user_avatar)

        user_text_box = QHBoxLayout()
        user_text_box.setSpacing(6)

        self.user_lbl = QLabel(self._user_name)
        self.user_lbl.setStyleSheet("font-size: 13px; font-weight: 700;")
        user_text_box.addWidget(self.user_lbl)

        self.role_badge = QLabel(f" {self._role.upper()} ")
        self.role_badge.setStyleSheet("""
            font-size: 10px;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 6px;
        """)
        user_text_box.addWidget(self.role_badge)
        capsule_layout.addLayout(user_text_box)

        layout.addWidget(self.user_capsule)

        # ── 6. Modern Sign Out Button ─────────────────────────────────────────
        self.logout_btn = QPushButton("Sign Out")
        self.logout_btn.setFixedHeight(36)
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_btn.clicked.connect(self.logout_clicked.emit)
        layout.addWidget(self.logout_btn)

        self.update_styles()

    def update_styles(self):
        is_dark = ThemeManager.current_theme() == "dark"

        border_color = "#24272D" if is_dark else "#E2E6ED"
        bg_bar = "#0C0D0E" if is_dark else "#F4F5F8"
        text_color = "#F4F5F8" if is_dark else "#18181B"
        sub_text = "#9CA3AF" if is_dark else "#6B7280"

        self.setStyleSheet(f"""
            QWidget#topbar {{
                background-color: {bg_bar};
                border-bottom: 1px solid {border_color};
            }}
        """)

        # Search Input
        input_bg = "#141518" if is_dark else "#FFFFFF"
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {input_bg};
                border: 1px solid {border_color};
                border-radius: 19px;
                color: {text_color};
                font-size: 13px;
                padding-left: 16px;
                padding-right: 16px;
            }}
            QLineEdit:focus {{
                border: 1.5px solid #FA5A3C;
            }}
        """)

        # Theme button
        btn_bg = "#141518" if is_dark else "#FFFFFF"
        theme_icon_name = "sun" if is_dark else "moon"
        theme_icon_color = "#F59E0B" if is_dark else "#3B82F6"
        self.theme_btn.setIcon(get_icon(theme_icon_name, color=theme_icon_color, size=18))
        self.theme_btn.setIconSize(QSize(18, 18))
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                border: 1px solid {border_color};
                border-radius: 20px;
            }}
            QPushButton:hover {{
                border-color: #FA5A3C;
            }}
        """)

        # Notif button
        notif_bg = "#141518" if is_dark else "#FFFFFF"
        self.notif_btn.setIcon(get_icon("bell", color=sub_text, size=18))
        self.notif_btn.setIconSize(QSize(18, 18))
        self.notif_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {notif_bg};
                border: 1px solid {border_color};
                border-radius: 20px;
                color: {text_color};
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border-color: #FA5A3C;
            }}
        """)

        self.sep.setStyleSheet(f"color: {border_color};")

        # User Capsule
        capsule_bg = "#141518" if is_dark else "#FFFFFF"
        self.user_capsule.setStyleSheet(f"""
            QFrame {{
                background-color: {capsule_bg};
                border: 1px solid {border_color};
                border-radius: 20px;
            }}
        """)

        self.user_avatar.setPixmap(get_icon("user", color="#FA5A3C", size=18).pixmap(18, 18))
        self.user_lbl.setStyleSheet(f"color: {text_color}; font-size: 13px; font-weight: 700;")
        self.role_badge.setStyleSheet(f"""
            background-color: {"#2A1715" if is_dark else "#FFF2F0"};
            color: #FA5A3C;
            font-size: 10px;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 6px;
            border: 1px solid rgba(250, 90, 60, 0.3);
        """)

        # Sign out button
        self.logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {border_color};
                border-radius: 12px;
                color: {sub_text};
                padding: 0 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {"#2A1715" if is_dark else "#FFF2F0"};
                border-color: #EF4444;
                color: #EF4444;
            }}
        """)

    def set_notification_count(self, count: int):
        self._notif_count = count
        if count > 0:
            self.notif_btn.setText(f" {count}")
        else:
            self.notif_btn.setText("")

    def set_page_title(self, title: str):
        self.page_title_lbl.setText(title)
