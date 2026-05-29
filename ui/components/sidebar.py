"""FitLife — Sidebar Component"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon
from config.constants import (
    SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED,
    ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER
)


# Nav item definition: (label, icon_emoji, module_key, allowed_roles)
NAV_ITEMS = [
    ("Dashboard",       "🏠", "dashboard",      [ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER]),
    ("Members",         "👥", "members",         [ROLE_ADMIN, ROLE_MANAGER]),
    ("Trainers",        "💪", "trainers",         [ROLE_ADMIN, ROLE_MANAGER]),
    ("Branches",        "🏢", "branches",         [ROLE_ADMIN]),
    ("Membership Plans","📋", "plans",            [ROLE_ADMIN, ROLE_MANAGER]),
    ("Attendance",      "📅", "attendance",       [ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER]),
    ("Finance Center",  "💳", "finance",          [ROLE_ADMIN, ROLE_MANAGER]),
    ("Workout Plans",   "🏋️", "workout_plans",   [ROLE_ADMIN, ROLE_MANAGER, ROLE_MEMBER]),
    ("Diet Plans",      "🥗", "diet_plans",       [ROLE_ADMIN, ROLE_MANAGER, ROLE_MEMBER]),
    ("Progress",        "📈", "progress",         [ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER]),
    ("Equipment",       "🔧", "equipment",        [ROLE_ADMIN, ROLE_MANAGER]),
    ("Schedule",        "📅", "schedule",         [ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER]),
    ("Staff",           "👔", "staff",            [ROLE_ADMIN]),
    ("Analytics",       "📊", "analytics",        [ROLE_ADMIN, ROLE_MANAGER]),
    ("Reports",         "📄", "reports",          [ROLE_ADMIN, ROLE_MANAGER]),
    ("Diary",           "📓", "diary",            [ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER]),
    ("Audit Logs",      "🔍", "audit",            [ROLE_ADMIN]),
    ("Settings",        "⚙️", "settings",         [ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER]),
]


class SidebarButton(QPushButton):
    def __init__(self, icon: str, label: str, module_key: str, parent=None):
        super().__init__(parent)
        self.module_key = module_key
        self._icon = icon
        self._label = label
        self._expanded = True
        self.setObjectName("sidebarBtn")
        self.setMinimumHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self._update_text()

    def _update_text(self):
        if self._expanded:
            self.setText(f"  {self._icon}   {self._label}")
            self.setFixedHeight(44)
        else:
            self.setText(self._icon)
            self.setFixedHeight(44)

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        self._update_text()

    def set_active(self, active: bool):
        self.setChecked(active)
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QWidget):
    """Collapsible glassmorphism sidebar."""

    nav_clicked = pyqtSignal(str)  # emits module_key

    def __init__(self, role: str, user_name: str, parent=None):
        super().__init__(parent)
        self._role = role
        self._user_name = user_name
        self._expanded = True
        self._buttons: list[SidebarButton] = []
        self._active_key = "dashboard"
        self.setObjectName("sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH_EXPANDED)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(4)

        # ── Logo / Brand ──────────────────────────────────────────────────────
        brand_row = QHBoxLayout()
        self.logo_lbl = QLabel("💪")
        self.logo_lbl.setStyleSheet("font-size: 28px;")
        self.app_name_lbl = QLabel("FitLife")
        self.app_name_lbl.setStyleSheet(
            "font-size: 22px; font-weight: bold; "
            "color: #7C3AED; letter-spacing: 1px;"
        )
        brand_row.addWidget(self.logo_lbl)
        brand_row.addWidget(self.app_name_lbl)
        brand_row.addStretch()
        layout.addLayout(brand_row)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: rgba(124,58,237,0.3);")
        layout.addWidget(div)
        layout.addSpacing(8)

        # ── Nav Items ─────────────────────────────────────────────────────────
        for label, icon, key, roles in NAV_ITEMS:
            if self._role not in roles:
                continue
            btn = SidebarButton(icon, label, key)
            btn.clicked.connect(lambda checked, k=key: self._on_nav_click(k))
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # Divider
        div2 = QFrame()
        div2.setFrameShape(QFrame.Shape.HLine)
        div2.setStyleSheet("color: rgba(124,58,237,0.3);")
        layout.addWidget(div2)

        # ── Toggle collapse ───────────────────────────────────────────────────
        self.toggle_btn = QPushButton("◀ Collapse")
        self.toggle_btn.setObjectName("sidebarBtn")
        self.toggle_btn.setMinimumHeight(40)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle_collapse)
        layout.addWidget(self.toggle_btn)

        # ── User Info ─────────────────────────────────────────────────────────
        user_frame = QFrame()
        user_frame.setStyleSheet(
            "background: rgba(124,58,237,0.12); border-radius: 12px; padding: 4px;"
        )
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(8, 8, 8, 8)
        user_layout.setSpacing(8)

        avatar = QLabel("👤")
        avatar.setStyleSheet("font-size: 24px;")
        user_layout.addWidget(avatar)

        self.user_info = QVBoxLayout()
        self.user_name_lbl = QLabel(self._user_name)
        self.user_name_lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #F0F4FF;")
        self.user_role_lbl = QLabel(self._role)
        self.user_role_lbl.setStyleSheet("font-size: 11px; color: #7C3AED;")
        self.user_info.addWidget(self.user_name_lbl)
        self.user_info.addWidget(self.user_role_lbl)
        user_layout.addLayout(self.user_info)
        layout.addWidget(user_frame)

        # Set dashboard active by default
        self.set_active("dashboard")

    def _on_nav_click(self, key: str):
        self.set_active(key)
        self.nav_clicked.emit(key)

    def set_active(self, key: str):
        self._active_key = key
        for btn in self._buttons:
            btn.set_active(btn.module_key == key)

    def toggle_collapse(self):
        self._expanded = not self._expanded
        target_width = SIDEBAR_WIDTH_EXPANDED if self._expanded else SIDEBAR_WIDTH_COLLAPSED

        self._anim = QPropertyAnimation(self, b"minimumWidth")
        self._anim.setDuration(250)
        self._anim.setStartValue(self.width())
        self._anim.setEndValue(target_width)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim.start()

        self._anim2 = QPropertyAnimation(self, b"maximumWidth")
        self._anim2.setDuration(250)
        self._anim2.setStartValue(self.width())
        self._anim2.setEndValue(target_width)
        self._anim2.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim2.start()

        for btn in self._buttons:
            btn.set_expanded(self._expanded)

        self.app_name_lbl.setVisible(self._expanded)
        self.user_name_lbl.setVisible(self._expanded)
        self.user_role_lbl.setVisible(self._expanded)
        self.toggle_btn.setText("◀ Collapse" if self._expanded else "▶")
