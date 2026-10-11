"""
FitLife — Clean & Minimal Login Window
Executive, uncluttered, and refined aesthetic:
- Solid obsidian background (#0C0D0E) without distracting particles or neon glows
- Centered, minimalist card (#141518) with a fine 1px slate-zinc border (#24272D)
- Clean unified input fields with soft neutral borders and subtle #FA5A3C focus state
- Smooth Coral Sign In button
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QApplication, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation,
    QRect, QEasingCurve, QSize
)
from PyQt6.QtGui import QColor
import services.auth_service as auth
from ui.theme.theme_manager import ThemeManager
import logging

logger = logging.getLogger(__name__)


class _LoginWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, username: str, password: str):
        super().__init__()
        self._username = username
        self._password = password

    def run(self):
        result = auth.login(self._username, self._password)
        self.finished.emit(result)


class LoginWindow(QWidget):
    login_success = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FitLife — Sign In")
        self.setMinimumSize(920, 600)
        self.setStyleSheet("background-color: #0C0D0E;")
        self.setWindowFlags(Qt.WindowType.Window)
        
        self._lockout_timer = QTimer(self)
        self._lockout_timer.timeout.connect(self._update_lockout_countdown)
        self._lockout_seconds = 0
        self._worker = None
        self._error_hide_timer = QTimer(self)
        self._error_hide_timer.setSingleShot(True)
        self._error_hide_timer.timeout.connect(self._hide_error)
        
        self._setup_ui()
        QTimer.singleShot(40, self._animate_card_in)

    def _setup_ui(self):
        # Center card in main window
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ── Minimalist Container Card ─────────────────────────────────────────
        self.card = QFrame()
        self.card.setFixedWidth(400)
        self.card.setObjectName("loginCard")
        self.card.setStyleSheet("""
            QFrame#loginCard {
                background-color: #141518;
                border: 1px solid #24272D;
                border-radius: 16px;
            }
        """)

        # Clean, natural drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(0, 0, 0, 140))
        shadow.setOffset(0, 8)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(36, 40, 36, 36)
        card_layout.setSpacing(0)

        # ── Brand Header (Minimalist Icon + Wordmark) ────────────────────────
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setSpacing(10)

        icon_lbl = QLabel()
        from ui.components.icons import get_icon
        icon_lbl.setPixmap(get_icon("brand", color="#FA5A3C", size=32).pixmap(32, 32))
        header_layout.addWidget(icon_lbl)

        brand_lbl = QLabel("FITLIFE")
        brand_lbl.setStyleSheet("""
            font-size: 24px;
            font-weight: 800;
            color: #F4F5F8;
            letter-spacing: 2px;
            background: transparent;
        """)
        header_layout.addWidget(brand_lbl)
        card_layout.addLayout(header_layout)
        card_layout.addSpacing(4)

        subtitle = QLabel("Gym Management System")
        subtitle.setStyleSheet("font-size: 13px; color: #6B7280; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(32)

        # ── Username Input ───────────────────────────────────────────────────
        user_lbl = QLabel("Username")
        user_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #9CA3AF; background: transparent;")
        card_layout.addWidget(user_lbl)
        card_layout.addSpacing(6)

        user_input_wrap = QFrame()
        user_input_wrap.setStyleSheet("""
            QFrame {
                background-color: #181A1F;
                border: 1px solid #24272D;
                border-radius: 8px;
            }
            QFrame:focus-within {
                border: 1px solid #FA5A3C;
                background-color: #1C1E24;
            }
        """)
        user_wrap_layout = QHBoxLayout(user_input_wrap)
        user_wrap_layout.setContentsMargins(12, 0, 12, 0)
        user_wrap_layout.setSpacing(8)

        user_icon = QLabel()
        user_icon.setPixmap(get_icon("user", color="#6B7280", size=15).pixmap(15, 15))
        user_icon.setStyleSheet("background: transparent; border: none;")
        user_wrap_layout.addWidget(user_icon)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setMinimumHeight(40)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #F4F5F8;
                font-size: 13px;
                selection-background-color: #FA5A3C;
            }
        """)
        user_wrap_layout.addWidget(self.username_input)
        card_layout.addWidget(user_input_wrap)

        self.username_err = QLabel("")
        self.username_err.setStyleSheet("color: #EF4444; font-size: 11px; background: transparent; margin-top: 3px;")
        card_layout.addWidget(self.username_err)
        card_layout.addSpacing(14)

        # ── Password Input ───────────────────────────────────────────────────
        pass_lbl = QLabel("Password")
        pass_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #9CA3AF; background: transparent;")
        card_layout.addWidget(pass_lbl)
        card_layout.addSpacing(6)

        pass_input_wrap = QFrame()
        pass_input_wrap.setStyleSheet("""
            QFrame {
                background-color: #181A1F;
                border: 1px solid #24272D;
                border-radius: 8px;
            }
            QFrame:focus-within {
                border: 1px solid #FA5A3C;
                background-color: #1C1E24;
            }
        """)
        pass_wrap_layout = QHBoxLayout(pass_input_wrap)
        pass_wrap_layout.setContentsMargins(12, 0, 8, 0)
        pass_wrap_layout.setSpacing(8)

        pass_icon = QLabel()
        pass_icon.setPixmap(get_icon("lock", color="#6B7280", size=15).pixmap(15, 15))
        pass_icon.setStyleSheet("background: transparent; border: none;")
        pass_wrap_layout.addWidget(pass_icon)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #F4F5F8;
                font-size: 13px;
                selection-background-color: #FA5A3C;
            }
        """)
        self.password_input.returnPressed.connect(self._attempt_login)
        pass_wrap_layout.addWidget(self.password_input)

        self.eye_btn = QPushButton()
        self.eye_btn.setFixedSize(28, 28)
        self.eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.eye_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
            }
        """)
        self.eye_btn.clicked.connect(self._toggle_password)
        pass_wrap_layout.addWidget(self.eye_btn)
        card_layout.addWidget(pass_input_wrap)

        self._update_eye_icon()

        self.pass_err = QLabel("")
        self.pass_err.setStyleSheet("color: #EF4444; font-size: 11px; background: transparent; margin-top: 3px;")
        card_layout.addWidget(self.pass_err)
        card_layout.addSpacing(16)

        # ── Error Banner ─────────────────────────────────────────────────────
        self.error_lbl = QLabel("")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_lbl.setStyleSheet("""
            QLabel {
                background-color: rgba(239, 68, 68, 0.12);
                border: 1px solid rgba(239, 68, 68, 0.25);
                border-radius: 6px;
                padding: 8px 12px;
                color: #F87171;
                font-size: 12px;
            }
        """)
        self.error_lbl.hide()
        card_layout.addWidget(self.error_lbl)
        card_layout.addSpacing(6)

        # ── Sign In Button ───────────────────────────────────────────────────
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setObjectName("btnPrimary")
        self.login_btn.setMinimumHeight(42)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton#btnPrimary {
                background-color: #FA5A3C;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton#btnPrimary:hover {
                background-color: #E54829;
            }
            QPushButton#btnPrimary:pressed {
                background-color: #C93A1E;
            }
            QPushButton#btnPrimary:disabled {
                background-color: #24272D;
                color: #6B7280;
            }
        """)
        self.login_btn.clicked.connect(self._attempt_login)
        card_layout.addWidget(self.login_btn)
        card_layout.addSpacing(22)

        # ── Footer ────────────────────────────────────────────────────────────
        footer = QLabel("FitLife © 2026")
        footer.setStyleSheet("font-size: 11px; color: #4B5563; background: transparent;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(footer)

        main_layout.addWidget(self.card)

    def _animate_card_in(self):
        if not self.card.isVisible():
            return
        start_geo = self.card.geometry()
        end_geo = QRect(start_geo.x(), start_geo.y(), start_geo.width(), start_geo.height())
        slide_start = QRect(start_geo.x(), start_geo.y() + 14, start_geo.width(), start_geo.height())
        self._anim = QPropertyAnimation(self.card, b"geometry")
        self._anim.setDuration(280)
        self._anim.setStartValue(slide_start)
        self._anim.setEndValue(end_geo)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def _toggle_password(self):
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._update_eye_icon()

    def _update_eye_icon(self):
        from ui.components.icons import get_icon
        is_visible = self.password_input.echoMode() == QLineEdit.EchoMode.Normal
        icon_name = "eye-off" if is_visible else "eye"
        self.eye_btn.setIcon(get_icon(icon_name, color="#6B7280", size=15))
        self.eye_btn.setIconSize(QSize(15, 15))

    def _attempt_login(self):
        self.username_err.setText("")
        self.pass_err.setText("")
        self._hide_error()

        username = self.username_input.text().strip()
        password = self.password_input.text()

        valid = True
        if not username:
            self.username_err.setText("Username is required.")
            valid = False
        if not password:
            self.pass_err.setText("Password is required.")
            valid = False
        if not valid:
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in...")

        self._worker = _LoginWorker(username, password)
        self._worker.finished.connect(self._on_login_result)
        self._worker.start()

    def _on_login_result(self, result: dict):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Sign In")

        if result["success"]:
            self.login_success.emit(result["session"])
        else:
            self._show_error(result["message"])
            if result.get("locked"):
                self._lockout_seconds = result.get("lock_seconds", 0)
                self.login_btn.setEnabled(False)
                self._lockout_timer.start(1000)

    def _show_error(self, msg: str):
        self.error_lbl.setText(msg)
        self.error_lbl.show()
        self._error_hide_timer.start(4000)

    def _hide_error(self):
        self.error_lbl.hide()
        self.error_lbl.setText("")

    def _update_lockout_countdown(self):
        self._lockout_seconds -= 1
        if self._lockout_seconds <= 0:
            self._lockout_timer.stop()
            self.login_btn.setEnabled(True)
            self._hide_error()
            return
        mins = self._lockout_seconds // 60
        secs = self._lockout_seconds % 60
        self._show_error(
            f"Account locked. Try again in {mins}m {secs:02d}s."
        )
