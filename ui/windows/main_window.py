"""
FitLife — Main Window (Phases 2, 3, 4, 5 complete)
All modules registered with role-based access control.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QLabel
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QBrush

from ui.components.sidebar import Sidebar
from ui.components.topbar import TopBar
from ui.components.loading_spinner import ToastNotification
from ui.theme.theme_manager import ThemeManager
from config.constants import ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER
import services.auth_service as auth
import logging

logger = logging.getLogger(__name__)


class GradientBackground(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), self.height())
        if ThemeManager.current_theme() == "dark":
            g.setColorAt(0.0, QColor(11, 15, 25))    # #0B0F19
            g.setColorAt(0.5, QColor(21, 32, 51))    # #152033
            g.setColorAt(1.0, QColor(15, 23, 42))    # #0F172A
        else:
            g.setColorAt(0.0, QColor(248, 250, 252)) # #F8FAFC
            g.setColorAt(0.5, QColor(241, 245, 249)) # #F1F5F9
            g.setColorAt(1.0, QColor(226, 232, 240)) # #E2E8F0
        painter.fillRect(self.rect(), QBrush(g))


class MainWindow(QMainWindow):
    logout_signal = pyqtSignal()

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self._screen_registry: dict[str, QWidget] = {}
        self._session_timer = QTimer(self)
        self._session_timer.setInterval(60_000)
        self._session_timer.timeout.connect(self._check_session)
        self.setWindowTitle(f"FitLife — {session.role} Dashboard")
        self.setMinimumSize(1280, 720)
        self._setup_ui()
        self._session_timer.start()

    # ── UI Shell ──────────────────────────────────────────────────────────────
    def _setup_ui(self):
        central = GradientBackground()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        self.topbar = TopBar(self._session.full_name, self._session.role, parent=central)
        self.topbar.theme_toggled.connect(self._toggle_theme)
        self.topbar.logout_clicked.connect(self._logout)
        root.addWidget(self.topbar)

        body = QHBoxLayout(); body.setSpacing(0); body.setContentsMargins(0,0,0,0)
        self.sidebar = Sidebar(self._session.role, self._session.full_name, parent=central)
        self.sidebar.nav_clicked.connect(self._navigate)
        body.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background: transparent;")
        body.addWidget(self.content_stack, 1)
        root.addLayout(body, 1)

        self.toast = ToastNotification(central)
        self._load_screens()
        self._navigate("dashboard")

    # ── Screen Loading ─────────────────────────────────────────────────────────
    def _load_screens(self):
        role = self._session.role

        # Dashboard (all roles)
        from ui.screens.dashboard_placeholder import DashboardPlaceholder
        dash = DashboardPlaceholder(self._session)
        dash.nav_requested.connect(self.navigate_to)
        self._register("dashboard", dash)

        # ── ADMIN + MANAGER ────────────────────────────────────────────────────
        if role in (ROLE_ADMIN, ROLE_MANAGER):
            from ui.screens.members       import MembersModule
            from ui.screens.trainers      import TrainersModule
            from ui.screens.billing.finance_module import FinanceCenterModule
            from ui.screens.billing.plans_module import PlansModule
            from ui.screens.workout_plans import WorkoutPlansModule
            from ui.screens.diet_plans    import DietPlansModule
            from ui.screens.progress      import ProgressModule
            from ui.screens.equipment     import EquipmentModule
            from ui.screens.staff         import StaffModule, ScheduleModule
            from ui.screens.analytics     import AnalyticsDashboard, AuditLogsModule
            from ui.screens.reports       import ReportsModule

            self._register("members",       MembersModule(self._session))
            self._register("trainers",      TrainersModule(self._session))
            self._register("plans",         PlansModule(self._session))
            self._register("finance",       FinanceCenterModule(self._session))
            self._register("workout_plans", WorkoutPlansModule(self._session))
            self._register("diet_plans",    DietPlansModule(self._session))
            self._register("progress",      ProgressModule(self._session))
            self._register("equipment",     EquipmentModule(self._session))
            self._register("schedule",      ScheduleModule(self._session))
            self._register("analytics",     AnalyticsDashboard(self._session))
            self._register("reports",       ReportsModule(self._session))
            self._register("audit",         AuditLogsModule(self._session))

            if role == ROLE_ADMIN:
                self._register("staff", StaffModule(self._session))

        # Admin-only: Branches
        if role == ROLE_ADMIN:
            from ui.screens.branches import BranchesModule
            self._register("branches", BranchesModule(self._session))

        # Attendance — admin, manager, trainer
        if role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER):
            from ui.screens.attendance import AttendanceScreen
            self._register("attendance", AttendanceScreen(self._session))

        # Trainer: workout plan verification + schedule view
        if role == ROLE_TRAINER:
            from ui.screens.workout_plans import WorkoutPlansModule
            from ui.screens.staff         import ScheduleModule
            from ui.screens.progress      import ProgressModule
            self._register("workout_plans", WorkoutPlansModule(self._session))
            self._register("schedule",      ScheduleModule(self._session))
            self._register("progress",      ProgressModule(self._session))

        # Member: own workout + diet + progress
        if role == ROLE_MEMBER:
            from ui.screens.workout_plans import WorkoutPlansModule
            from ui.screens.diet_plans    import DietPlansModule
            from ui.screens.progress      import ProgressModule
            self._register("workout_plans", WorkoutPlansModule(self._session))
            self._register("diet_plans",    DietPlansModule(self._session))
            self._register("progress",      ProgressModule(self._session))

        # ── Phase 6 screens — all roles ───────────────────────────────────────
        from ui.screens.smart_ask import SmartAskModule
        from ui.screens.diary     import DiaryModule
        from ui.screens.settings  import SettingsModule
        self._register("smart_ask", SmartAskModule(self._session))
        self._register("diary",     DiaryModule(self._session))
        self._register("settings",  SettingsModule(self._session))

    def _placeholder(self, key: str) -> QWidget:
        w = QWidget(); w.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(w); lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(f"{key.replace('_',' ').title()}\nUnder Construction")
        lbl.setStyleSheet("font-size:22px; color:#6B7280;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl)
        return w

    def _register(self, key: str, widget: QWidget):
        if key not in self._screen_registry:
            self._screen_registry[key] = widget
            self.content_stack.addWidget(widget)

    # ── Navigation ─────────────────────────────────────────────────────────────
    def _navigate(self, key: str):
        self._session.refresh()
        screen = self._screen_registry.get(key)
        if screen:
            self.content_stack.setCurrentWidget(screen)
            self.sidebar.set_active(key)
            
            # Map navigation keys to user-friendly page titles
            titles = {
                "dashboard": "Dashboard Overview",
                "members": "Members Directory",
                "trainers": "Trainers Directory",
                "branches": "Branch Management",
                "plans": "Membership Plans",
                "attendance": "Attendance Register",
                "finance": "Finance Center",
                "workout_plans": "Workout Plans",
                "diet_plans": "Diet Plans",
                "progress": "Progress Logs",
                "equipment": "Equipment Inventory",
                "schedule": "Class & Trainer Schedule",
                "staff": "Staff Management",
                "analytics": "Business Analytics",
                "reports": "System Reports",
                "diary": "My Daily Diary",
                "audit": "System Audit Logs",
                "settings": "Account Settings",
                "smart_ask": "Smart Ask Assistant"
            }
            title = titles.get(key, key.replace("_", " ").title())
            self.topbar.set_page_title(title)
            
            if hasattr(screen, "refresh"):
                screen.refresh()
        else:
            logger.warning(f"No screen for key: {key}")

    def navigate_to(self, key: str):
        self._navigate(key)

    def show_toast(self, title: str, message: str, toast_type: str = "info"):
        self.toast.show_message(title, message, toast_type)

    # ── Theme + Session ────────────────────────────────────────────────────────
    def _toggle_theme(self):
        new_theme = ThemeManager.toggle_theme()
        auth.save_theme_preference(self._session.user_id, new_theme)
        self.toast.show_message("Theme Changed", f"Switched to {new_theme.title()} mode.", "info")
        
        # Refresh dynamic vector colors across sidebar and topbar
        self.sidebar.refresh_icons()
        self.topbar.update_icons()
        
        # Refresh current screen's dynamic elements (like KPI cards)
        current_screen = self.content_stack.currentWidget()
        if current_screen and hasattr(current_screen, "refresh"):
            current_screen.refresh()
            
        self.centralWidget().update()

    def _check_session(self):
        session = auth.get_current_session()
        if session is None:
            self._logout(); return
        if session.warn_expiry():
            mins = session.minutes_until_timeout()
            if mins <= 0:
                self._logout()
            else:
                self.toast.show_message(
                    "Session Expiring",
                    f"Logging out in {mins} minute(s) due to inactivity.",
                    "warning", duration=8000
                )

    def _logout(self):
        self._session_timer.stop()
        auth.logout()
        self.logout_signal.emit()

    def mousePressEvent(self, event):
        if self._session: self._session.refresh()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if self._session: self._session.refresh()
        super().keyPressEvent(event)
