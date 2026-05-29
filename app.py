"""
FitLife — Application Controller
Manages window transitions and DB initialization.
"""
import sys
import logging
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

from ui.theme.theme_manager import ThemeManager
from database.connection import initialize_pool, close_pool, test_connection
from config.constants import APP_NAME
try:
    from utils.scheduler import start_scheduler, stop_scheduler
    _SCHEDULER_AVAILABLE = True
except ImportError:
    _SCHEDULER_AVAILABLE = False


logger = logging.getLogger(__name__)


class DBErrorScreen(QWidget):
    """Shown when DB connection fails at startup."""

    def __init__(self, on_retry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FitLife — Connection Error")
        self.setMinimumSize(500, 300)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        icon = QLabel("❌")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        title = QLabel("Database Connection Failed")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #FF2D78;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        msg = QLabel(
            "FitLife could not connect to the SQL Server database.\n\n"
            "Please check:\n"
            "  • SQL Server is running\n"
            "  • config/settings.json has correct server name\n"
            "  • ODBC Driver 17 for SQL Server is installed\n"
            "  • FitLifeDB database exists (run schema.sql)"
        )
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet("color: #9CA3AF; font-size: 14px;")
        layout.addWidget(msg)

        retry_btn = QPushButton("🔄  Retry Connection")
        retry_btn.setObjectName("btnPrimary")
        retry_btn.setMinimumHeight(44)
        retry_btn.setFixedWidth(220)
        retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        retry_btn.clicked.connect(on_retry)
        layout.addWidget(retry_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class FitLifeApp:
    """Main application controller."""

    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setApplicationName(APP_NAME)
        self.app.setApplicationVersion("1.0.0")
        self._login_window = None
        self._main_window = None
        self._db_error_screen = None

    def run(self):
        # Apply default dark theme first
        ThemeManager.apply_theme("dark")

        # Test DB connection
        if not test_connection():
            self._show_db_error()
        else:
            if not initialize_pool():
                self._show_db_error()
            else:
                # Start background scheduler
                if _SCHEDULER_AVAILABLE:
                    try:
                        start_scheduler()
                    except Exception as se:
                        logger.warning(f"Scheduler start failed (non-fatal): {se}")
                self._show_login()

        exit_code = self.app.exec()
        if _SCHEDULER_AVAILABLE:
            try:
                stop_scheduler()
            except Exception:
                pass
        close_pool()
        return exit_code

    def _show_db_error(self):
        self._db_error_screen = DBErrorScreen(on_retry=self._retry_connection)
        ThemeManager.apply_theme("dark")
        self._db_error_screen.setStyleSheet("background: #0A0E2A; color: #F0F4FF;")
        self._db_error_screen.show()

    def _retry_connection(self):
        if test_connection() and initialize_pool():
            if self._db_error_screen:
                self._db_error_screen.close()
            self._show_login()
        else:
            logger.error("Retry failed.")

    def _show_login(self):
        from ui.windows.login_window import LoginWindow
        self._login_window = LoginWindow()
        self._login_window.login_success.connect(self._on_login_success)
        self._login_window.show()

    def _on_login_success(self, session):
        from ui.windows.main_window import MainWindow
        # Apply saved theme
        ThemeManager.apply_theme(session.theme_pref or "dark")

        if self._login_window:
            self._login_window.close()

        self._main_window = MainWindow(session)
        self._main_window.logout_signal.connect(self._on_logout)
        self._main_window.showMaximized()

    def _on_logout(self):
        if self._main_window:
            self._main_window.close()
            self._main_window = None
        # Return to login
        ThemeManager.apply_theme("dark")
        self._show_login()
