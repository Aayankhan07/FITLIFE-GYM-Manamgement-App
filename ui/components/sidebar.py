"""FitLife — Redesigned Sidebar Component (Matching GYM-MANAGEMENT)"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon
from config.constants import (
    ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER
)
from ui.theme.theme_manager import ThemeManager
from ui.components.icons import get_icon


class NavButton(QPushButton):
    """Clean navigation item with rounded pill background and active state indicator."""
    def __init__(self, icon_name: str, label: str, module_key: str, parent=None):
        super().__init__(parent)
        self.module_key = module_key
        self._icon_name = icon_name
        self._label = label
        self._is_active = False
        self._expanded = True
        self.setObjectName("navItemBtn")
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()

    def update_style(self):
        is_dark = ThemeManager.current_theme() == "dark"
        icon_color = "#FFFFFF" if is_dark and self._is_active else (
            "#18181B" if not is_dark and self._is_active else ("#9CA3AF" if is_dark else "#6B7280")
        )
        self.setIcon(get_icon(self._icon_name, color=icon_color, size=18))
        self.setIconSize(QSize(18, 18))

        if self._is_active:
            bg = "#1E2129" if is_dark else "#FFFFFF"
            border = "1px solid #2B2F38" if is_dark else "1px solid #E2E6ED"
            text_color = "#FFFFFF" if is_dark else "#18181B"
            font_weight = "bold"
        else:
            bg = "transparent"
            border = "none"
            text_color = "#9CA3AF" if is_dark else "#6B7280"
            font_weight = "500"

        hover_bg = "#1A1D23" if is_dark else "rgba(255, 255, 255, 0.8)"
        hover_color = "#FFFFFF" if is_dark else "#18181B"

        if self._expanded:
            self.setText(f"  {self._label}")
            self.setStyleSheet(f"""
                QPushButton#navItemBtn {{
                    background-color: {bg};
                    border: {border};
                    border-radius: 12px;
                    color: {text_color};
                    font-weight: {font_weight};
                    font-size: 13px;
                    text-align: left;
                    padding-left: 12px;
                }}
                QPushButton#navItemBtn:hover {{
                    background-color: {hover_bg};
                    color: {hover_color};
                }}
            """)
        else:
            self.setText("")
            self.setStyleSheet(f"""
                QPushButton#navItemBtn {{
                    background-color: {bg};
                    border: {border};
                    border-radius: 12px;
                    text-align: center;
                }}
                QPushButton#navItemBtn:hover {{
                    background-color: {hover_bg};
                }}
            """)

    def set_active(self, active: bool):
        self._is_active = active
        self.update_style()

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        self.update_style()


class SubNavButton(QPushButton):
    """Sub-item with tree connector line."""
    def __init__(self, label: str, module_key: str, parent=None):
        super().__init__(parent)
        self.module_key = module_key
        self._label = label
        self._is_active = False
        self.setFixedHeight(32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()

    def update_style(self):
        is_dark = ThemeManager.current_theme() == "dark"
        if self._is_active:
            bg = "#1E2129" if is_dark else "#FFFFFF"
            text_color = "#FFFFFF" if is_dark else "#18181B"
            font_weight = "bold"
        else:
            bg = "transparent"
            text_color = "#8C93A3" if is_dark else "#6B7280"
            font_weight = "500"

        hover_color = "#FFFFFF" if is_dark else "#18181B"

        self.setText(f"  · {self._label}")
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                border: none;
                border-radius: 8px;
                color: {text_color};
                font-weight: {font_weight};
                font-size: 12px;
                text-align: left;
                padding-left: 16px;
            }}
            QPushButton:hover {{
                color: {hover_color};
            }}
        """)

    def set_active(self, active: bool):
        self._is_active = active
        self.update_style()


class Sidebar(QWidget):
    """
    Modern editorial sidebar matching reference GYM-MANAGEMENT:
    - Top circular brand emblem button
    - Grouped tree navigation
    - Collapsible Gym Operations submenu
    - Bottom pill segmented theme toggle
    """

    nav_clicked = pyqtSignal(str)
    theme_changed = pyqtSignal(str)
    theme_toggled = pyqtSignal()

    def __init__(self, role: str, user_name: str, parent=None):
        super().__init__(parent)
        self._role = role
        self._user_name = user_name
        self._expanded = True
        self._active_key = "dashboard"
        self._nav_buttons: list[NavButton] = []
        self._sub_buttons: list[SubNavButton] = []
        self._operations_expanded = True

        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 16)
        layout.setSpacing(16)

        # ── 1. Top Section: Circular Brand Emblem ─────────────────────────────
        # ── 1. Top Section: Brand Title ──────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setContentsMargins(4, 0, 0, 0)
        
        self.brand_title_lbl = QLabel("FitLife Pro")
        self.brand_title_lbl.setStyleSheet("""
            font-size: 16px; font-weight: 800; letter-spacing: 0.5px;
        """)

        top_row.addWidget(self.brand_title_lbl)
        top_row.addStretch()
        layout.addLayout(top_row)

        # ── 2. Scrollable Navigation List ─────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.nav_layout = QVBoxLayout(scroll_content)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(4)

        # Build dynamic role-based items
        self._build_nav_items()

        self.nav_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # ── 3. Bottom Controls: Pill Theme Toggle & Collapse ─────────────────
        bottom_box = QVBoxLayout()
        bottom_box.setContentsMargins(0, 8, 0, 8)
        bottom_box.setSpacing(8)

        # Pill theme switcher
        self.theme_pill = QWidget()
        self.theme_pill.setObjectName("sidebarThemePill")
        self.theme_pill.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.theme_pill.setFixedSize(72, 34)
        theme_pill_layout = QHBoxLayout(self.theme_pill)
        theme_pill_layout.setContentsMargins(3, 3, 3, 3)
        theme_pill_layout.setSpacing(2)

        self.light_btn = QPushButton()
        self.light_btn.setObjectName("sidebarThemeBtn")
        self.light_btn.setFixedSize(32, 28)
        self.light_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.light_btn.setIcon(get_icon("sun", size=15))
        self.light_btn.setIconSize(QSize(15, 15))
        self.light_btn.clicked.connect(lambda: self._set_theme("light"))

        self.dark_btn = QPushButton()
        self.dark_btn.setObjectName("sidebarThemeBtn")
        self.dark_btn.setFixedSize(32, 28)
        self.dark_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dark_btn.setIcon(get_icon("moon", size=15))
        self.dark_btn.setIconSize(QSize(15, 15))
        self.dark_btn.clicked.connect(lambda: self._set_theme("dark"))

        theme_pill_layout.addWidget(self.light_btn)
        theme_pill_layout.addWidget(self.dark_btn)

        self.bottom_row = QHBoxLayout()
        self.bottom_row.setContentsMargins(0, 0, 0, 0)
        self.bottom_row.addWidget(self.theme_pill)
        self.bottom_stretch = self.bottom_row.addStretch()

        self.collapse_toggle = QPushButton()
        self.collapse_toggle.setObjectName("sidebarCollapseBtn")
        self.collapse_toggle.setFixedSize(34, 34)
        self.collapse_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.collapse_toggle.clicked.connect(self.toggle_collapse)
        self.bottom_row.addWidget(self.collapse_toggle)

        bottom_box.addLayout(self.bottom_row)
        layout.addLayout(bottom_box)

        self.refresh_styles()
        self.set_active("dashboard")

    def _build_nav_items(self):
        role = self._role

        # Helper to add standard button
        def add_btn(icon, label, key):
            btn = NavButton(icon, label, key)
            btn.clicked.connect(lambda checked, k=key: self._on_nav_click(k))
            self._nav_buttons.append(btn)
            self.nav_layout.addWidget(btn)

        # Dashboard for everyone
        add_btn("dashboard", "Overview", "dashboard")

        if role in (ROLE_ADMIN, ROLE_MANAGER):
            add_btn("members", "Members Directory", "members")

            # Operations collapsible group
            self.ops_btn = QPushButton()
            self.ops_btn.setFixedHeight(40)
            self.ops_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.ops_btn.clicked.connect(self._toggle_operations)
            self.nav_layout.addWidget(self.ops_btn)

            self.ops_container = QWidget()
            self.ops_layout = QVBoxLayout(self.ops_container)
            self.ops_layout.setContentsMargins(12, 0, 0, 0)
            self.ops_layout.setSpacing(2)

            sub_items = [
                ("Branch Facilities", "branches"),
                ("Staff & Trainers", "staff"),
                ("Equipment & Repairs", "equipment"),
                ("Attendance", "attendance"),
            ]
            for sub_lbl, sub_key in sub_items:
                sbtn = SubNavButton(sub_lbl, sub_key)
                sbtn.clicked.connect(lambda checked, k=sub_key: self._on_nav_click(k))
                self._sub_buttons.append(sbtn)
                self.ops_layout.addWidget(sbtn)

            self.nav_layout.addWidget(self.ops_container)

            add_btn("trainers", "Trainers Directory", "trainers")
            add_btn("plans", "Membership Plans", "plans")
            add_btn("workout_plans", "Workout Programs", "workout_plans")
            add_btn("diet_plans", "Diet & Nutrition", "diet_plans")
            add_btn("progress", "Client Progress", "progress")
            add_btn("finance", "Billing & Invoices", "finance")
            add_btn("analytics", "Revenue Analytics", "analytics")
            add_btn("reports", "System Reports", "reports")
            add_btn("diary", "Daily Diary", "diary")
            if role == ROLE_ADMIN:
                add_btn("audit", "System Audit", "audit")
            add_btn("smart_ask", "AI Assistant", "smart_ask")
            add_btn("settings", "Settings", "settings")

        elif role == ROLE_TRAINER:
            add_btn("members", "Assigned Clients", "members")
            add_btn("attendance", "Attendance", "attendance")
            add_btn("workout_plans", "Workout Programs", "workout_plans")
            add_btn("diet_plans", "Diet & Nutrition", "diet_plans")
            add_btn("progress", "Client Progress", "progress")
            add_btn("schedule", "My Schedule", "schedule")
            add_btn("diary", "My Diary", "diary")
            add_btn("smart_ask", "AI Assistant", "smart_ask")
            add_btn("settings", "Settings", "settings")

        elif role == ROLE_MEMBER:
            add_btn("workout_plans", "My Workout Plan", "workout_plans")
            add_btn("diet_plans", "My Diet Plan", "diet_plans")
            add_btn("progress", "My Weight Progress", "progress")
            add_btn("finance", "My Invoices", "finance")
            add_btn("diary", "My Diary", "diary")
            add_btn("smart_ask", "AI Assistant", "smart_ask")
            add_btn("settings", "Settings", "settings")

    def _toggle_operations(self):
        self._operations_expanded = not self._operations_expanded
        self.ops_container.setVisible(self._operations_expanded)
        self._update_ops_button_text()

    def _update_ops_button_text(self):
        if not hasattr(self, 'ops_btn'):
            return
        is_dark = ThemeManager.current_theme() == "dark"
        arrow = "▲" if self._operations_expanded else "▼"
        color = "#9CA3AF" if is_dark else "#6B7280"
        self.ops_btn.setText(f"  Gym Operations   {arrow}")
        self.ops_btn.setIcon(get_icon("branches", color=color, size=18))
        self.ops_btn.setIconSize(QSize(18, 18))
        self.ops_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 12px;
                color: {color};
                font-size: 13px;
                font-weight: 600;
                text-align: left;
                padding-left: 12px;
            }}
            QPushButton:hover {{
                background-color: {"#1A1D23" if is_dark else "rgba(255,255,255,0.8)"};
                color: {"#FFFFFF" if is_dark else "#18181B"};
            }}
        """)

    def _set_theme(self, target_theme: str):
        if ThemeManager.current_theme() != target_theme:
            self.theme_changed.emit(target_theme)

    def refresh_styles(self):
        is_dark = ThemeManager.current_theme() == "dark"

        # 1. Update Brand Title
        self.brand_title_lbl.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 800;
            letter-spacing: 0.5px;
            color: {"#FA5A3C" if is_dark else "#FA5A3C"};
        """)

        # 2. Update Theme Pill
        pill_bg = "#1E2129" if is_dark else "#FFFFFF"
        pill_border = "#2B2F38" if is_dark else "#E2E6ED"
        self.theme_pill.setStyleSheet(f"""
            QWidget#sidebarThemePill {{
                background-color: {pill_bg};
                border: 1px solid {pill_border};
                border-radius: 17px;
            }}
        """)

        active_btn_style = f"""
            QPushButton#sidebarThemeBtn {{
                background-color: {"#282C36" if is_dark else "#EAECEF"} !important;
                border: none !important;
                outline: none !important;
                border-radius: 14px;
                min-width: 32px;
                max-width: 32px;
                min-height: 28px;
                max-height: 28px;
                padding: 0px !important;
                margin: 0px !important;
            }}
            QPushButton#sidebarThemeBtn:hover {{
                border: none !important;
                outline: none !important;
            }}
        """
        inactive_btn_style = """
            QPushButton#sidebarThemeBtn {{
                background-color: transparent !important;
                background: transparent !important;
                border: none !important;
                outline: none !important;
                border-radius: 14px;
                min-width: 32px;
                max-width: 32px;
                min-height: 28px;
                max-height: 28px;
                padding: 0px !important;
                margin: 0px !important;
            }}
            QPushButton#sidebarThemeBtn:hover {{
                background-color: rgba(125, 125, 125, 0.08) !important;
                border: none !important;
                outline: none !important;
            }}
        """

        self.dark_btn.setStyleSheet(active_btn_style if is_dark else inactive_btn_style)
        self.light_btn.setStyleSheet(inactive_btn_style if is_dark else active_btn_style)

        # Update icons with high contrast colors
        sun_color = "#6B7280" if is_dark else "#FA5A3C"
        moon_color = "#FA5A3C" if is_dark else "#6B7280"
        self.light_btn.setIcon(get_icon("sun", color=sun_color, size=15))
        self.dark_btn.setIcon(get_icon("moon", color=moon_color, size=15))

        arrow_icon_name = "chevron_left" if self._expanded else "chevron_right"
        self.collapse_toggle.setIcon(get_icon(arrow_icon_name, color="#FFFFFF", size=16))
        self.collapse_toggle.setIconSize(QSize(16, 16))
        self.collapse_toggle.setStyleSheet("""
            QPushButton#sidebarCollapseBtn {
                background-color: #FA5A3C;
                border: none;
                border-radius: 17px;
                min-width: 34px;
                max-width: 34px;
                min-height: 34px;
                max-height: 34px;
                padding: 0px;
            }
            QPushButton#sidebarCollapseBtn:hover {
                background-color: #E0482B;
            }
            QPushButton#sidebarCollapseBtn:pressed {
                background-color: #C83C22;
            }
        """)

        self._update_ops_button_text()

        for btn in self._nav_buttons:
            btn.update_style()
        for sbtn in self._sub_buttons:
            sbtn.update_style()

    def _on_nav_click(self, key: str):
        self.set_active(key)
        self.nav_clicked.emit(key)

    def set_active(self, key: str):
        self._active_key = key
        for btn in self._nav_buttons:
            btn.set_active(btn.module_key == key)
        for sbtn in self._sub_buttons:
            sbtn.set_active(sbtn.module_key == key)

    def toggle_collapse(self):
        self._expanded = not self._expanded
        target_width = 240 if self._expanded else 76

        self._anim = QPropertyAnimation(self, b"minimumWidth")
        self._anim.setDuration(200)
        self._anim.setStartValue(self.width())
        self._anim.setEndValue(target_width)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim.start()

        self._anim2 = QPropertyAnimation(self, b"maximumWidth")
        self._anim2.setDuration(200)
        self._anim2.setStartValue(self.width())
        self._anim2.setEndValue(target_width)
        self._anim2.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim2.start()

        self.brand_title_lbl.setVisible(self._expanded)
        self.theme_pill.setVisible(self._expanded)
        if hasattr(self, 'bottom_row'):
            self.bottom_row.invalidate()
        if hasattr(self, 'ops_container'):
            self.ops_container.setVisible(self._expanded and self._operations_expanded)
            self.ops_btn.setVisible(self._expanded)

        for btn in self._nav_buttons:
            btn.set_expanded(self._expanded)

        arrow_icon_name = "chevron_left" if self._expanded else "chevron_right"
        self.collapse_toggle.setIcon(get_icon(arrow_icon_name, color="#FFFFFF", size=16))
