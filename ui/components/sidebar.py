"""FitLife — Sidebar Component"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon
from config.constants import (
    SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED,
    ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER
)


# Nav item definition: (label, icon_name, module_key, allowed_roles)
NAV_ITEMS = [
    ("Dashboard",       "dashboard",      "dashboard",      [ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER]),
    ("Members",         "members",        "members",         [ROLE_ADMIN, ROLE_MANAGER]),
    ("Trainers",        "trainers",       "trainers",         [ROLE_ADMIN, ROLE_MANAGER]),
    ("Branches",        "branches",       "branches",         [ROLE_ADMIN]),
    ("Membership Plans","plans",          "plans",            [ROLE_ADMIN, ROLE_MANAGER]),
    ("Attendance",      "attendance",     "attendance",       [ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER]),
    ("Finance Center",  "finance",        "finance",          [ROLE_ADMIN, ROLE_MANAGER]),
    ("Workout Plans",   "workout_plans",  "workout_plans",   [ROLE_ADMIN, ROLE_MANAGER, ROLE_MEMBER]),
    ("Diet Plans",      "diet_plans",     "diet_plans",       [ROLE_ADMIN, ROLE_MANAGER, ROLE_MEMBER]),
    ("Progress",        "progress",       "progress",         [ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER]),
    ("Equipment",       "equipment",      "equipment",        [ROLE_ADMIN, ROLE_MANAGER]),
    ("Schedule",        "schedule",       "schedule",         [ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER]),
    ("Staff",           "staff",          "staff",            [ROLE_ADMIN]),
    ("Analytics",       "analytics",      "analytics",        [ROLE_ADMIN, ROLE_MANAGER]),
    ("Reports",         "reports",        "reports",          [ROLE_ADMIN, ROLE_MANAGER]),
    ("Diary",           "diary",          "diary",            [ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER]),
    ("Audit Logs",      "audit",          "audit",            [ROLE_ADMIN]),
    ("Settings",        "settings",       "settings",         [ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER]),
]


class SidebarButton(QPushButton):
    def __init__(self, icon_name: str, label: str, module_key: str, parent=None):
        super().__init__(parent)
        self.module_key = module_key
        self._icon_name = icon_name
        self._label = label
        self._expanded = True
        self.setObjectName("sidebarBtn")
        self.setMinimumHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setProperty("collapsed", "false")
        self._update_icon_and_text()

    def _update_icon_and_text(self):
        from ui.components.icons import get_icon
        from ui.theme.theme_manager import ThemeManager
        
        color_var = "accent_primary" if self.isChecked() else "text_secondary"
        color = ThemeManager.color(color_var)
        self.setIcon(get_icon(self._icon_name, color=color, size=20))
        self.setIconSize(QSize(20, 20))
        
        if self._expanded:
            self.setText(f"   {self._label}")
            self.setFixedHeight(44)
        else:
            self.setText("")
            self.setFixedHeight(44)

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        self.setProperty("collapsed", "true" if not expanded else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self._update_icon_and_text()

    def set_active(self, active: bool):
        self.setChecked(active)
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self._update_icon_and_text()


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
        self.logo_lbl = QLabel()
        from ui.components.icons import get_icon
        from ui.theme.theme_manager import ThemeManager
        self.logo_lbl.setPixmap(get_icon("brand", color=ThemeManager.color("accent_primary"), size=28).pixmap(28, 28))
        
        self.app_name_lbl = QLabel("FitLife")
        self.app_name_lbl.setObjectName("sidebarLogoText")
        brand_row.addWidget(self.logo_lbl)
        brand_row.addWidget(self.app_name_lbl)
        brand_row.addStretch()
        layout.addLayout(brand_row)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: rgba(0, 102, 255, 0.3);")
        layout.addWidget(div)
        layout.addSpacing(8)

        # ── Scroll Area for Nav Items ─────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        scroll_content = QWidget()
        scroll_content.setObjectName("sidebarScrollContent")
        scroll_content.setStyleSheet("QWidget#sidebarScrollContent { background: transparent; }")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(4)
        
        for label, icon, key, roles in NAV_ITEMS:
            if self._role not in roles:
                continue
            btn = SidebarButton(icon, label, key)
            btn.clicked.connect(lambda checked, k=key: self._on_nav_click(k))
            self._buttons.append(btn)
            scroll_layout.addWidget(btn)
            
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # Divider
        div2 = QFrame()
        div2.setFrameShape(QFrame.Shape.HLine)
        div2.setStyleSheet("color: rgba(0, 102, 255, 0.3);")
        layout.addWidget(div2)

        # ── Toggle collapse ───────────────────────────────────────────────────
        self.toggle_btn = QPushButton("◀ Collapse")
        self.toggle_btn.setObjectName("sidebarBtn")
        self.toggle_btn.setMinimumHeight(40)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle_collapse)
        layout.addWidget(self.toggle_btn)

        # ── User Info ─────────────────────────────────────────────────────────
        self.user_frame = QFrame()
        self.user_frame.setObjectName("userFrame")
        self.user_frame.setStyleSheet(
            "QFrame#userFrame { background: rgba(0, 102, 255, 0.12); border-radius: 12px; }"
        )
        user_layout = QHBoxLayout(self.user_frame)
        user_layout.setContentsMargins(8, 8, 8, 8)
        user_layout.setSpacing(8)

        self.avatar_lbl = QLabel()
        self.avatar_lbl.setPixmap(get_icon("user", color=ThemeManager.color("accent_primary"), size=24).pixmap(24, 24))
        user_layout.addWidget(self.avatar_lbl)

        self.user_info = QVBoxLayout()
        self.user_name_lbl = QLabel(self._user_name)
        self.user_name_lbl.setObjectName("userNameLbl")
        self.user_role_lbl = QLabel(self._role)
        self.user_role_lbl.setObjectName("userRoleLbl")
        self.user_info.addWidget(self.user_name_lbl)
        self.user_info.addWidget(self.user_role_lbl)
        user_layout.addLayout(self.user_info)
        layout.addWidget(self.user_frame)

        # Set dashboard active by default
        self.set_active("dashboard")

    def _on_nav_click(self, key: str):
        self.set_active(key)
        self.nav_clicked.emit(key)

    def set_active(self, key: str):
        self._active_key = key
        for btn in self._buttons:
            btn.set_active(btn.module_key == key)

    def refresh_icons(self):
        from ui.components.icons import get_icon
        from ui.theme.theme_manager import ThemeManager
        # Refresh brand logo icon
        self.logo_lbl.setPixmap(get_icon("brand", color=ThemeManager.color("accent_primary"), size=28).pixmap(28, 28))
        self.avatar_lbl.setPixmap(get_icon("user", color=ThemeManager.color("accent_primary"), size=24).pixmap(24, 24))
        
        # Refresh all nav buttons
        for btn in self._buttons:
            btn._update_icon_and_text()

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

        # Adjust margins of the sidebar main layout dynamically
        margin = 12 if self._expanded else 6
        self.layout().setContentsMargins(margin, 16, margin, 16)

        for btn in self._buttons:
            btn.set_expanded(self._expanded)

        self.toggle_btn.setProperty("collapsed", "true" if not self._expanded else "false")
        self.toggle_btn.style().unpolish(self.toggle_btn)
        self.toggle_btn.style().polish(self.toggle_btn)

        self.app_name_lbl.setVisible(self._expanded)
        self.user_name_lbl.setVisible(self._expanded)
        self.user_role_lbl.setVisible(self._expanded)
        self.user_frame.setVisible(self._expanded)
        self.toggle_btn.setText("◀ Collapse" if self._expanded else "▶")
