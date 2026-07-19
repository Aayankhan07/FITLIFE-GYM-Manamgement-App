"""
FitLife — Login Window (Redesigned)
Full-window animated gradient background with floating particles.
Single centered glass card. Premium glassmorphism design.
"""
import math
import random

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QApplication, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation,
    QRect, QEasingCurve, QPoint, QSize
)
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QLinearGradient, QBrush, QPen,
    QRadialGradient
)
import services.auth_service as auth
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


class AnimatedBackground(QWidget):
    """Animated gradient background with floating particle dots."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._frame = 0
        self._particles = []
        self._init_particles()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(33)  # ~30fps

    def _init_particles(self):
        """Create 25 floating particle dots with random positions/speeds."""
        for _ in range(25):
            self._particles.append({
                'x': random.uniform(0, 1),
                'y': random.uniform(0, 1),
                'r': random.uniform(2, 5),
                'speed': random.uniform(0.0003, 0.0008),
                'drift': random.uniform(-0.0002, 0.0002),
                'opacity': random.uniform(0.15, 0.4),
            })

    def _animate(self):
        self._frame += 1
        # Move particles upward with slight horizontal drift
        for p in self._particles:
            p['y'] -= p['speed']
            p['x'] += p['drift']
            if p['y'] < -0.02:
                p['y'] = 1.02
                p['x'] = random.uniform(0, 1)
            if p['x'] < -0.02:
                p['x'] = 1.02
            if p['x'] > 1.02:
                p['x'] = -0.02
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()

        # Animated gradient background — oscillates through color stops
        t = (self._frame * 0.002) % (2 * math.pi)
        blend = (math.sin(t) + 1) / 2  # 0..1 oscillating

        grad = QLinearGradient(0, 0, W, H)
        # Interpolate between two color sets
        r1 = int(10 + blend * 7)
        g1 = int(14 + blend * 2)
        b1 = int(42 + blend * 14)
        r2 = int(26 - blend * 3)
        g2 = int(16 + blend * 2)
        b2 = int(64 - blend * 10)
        r3 = int(23 + blend * 5)
        g3 = int(10 - blend * 3)
        b3 = int(46 + blend * 12)

        grad.setColorAt(0.0, QColor(r1, g1, b1))
        grad.setColorAt(0.5, QColor(r2, g2, b2))
        grad.setColorAt(1.0, QColor(r3, g3, b3))
        painter.fillRect(self.rect(), QBrush(grad))

        # Soft glow orb at top-right
        orb = QRadialGradient(W * 0.8, H * 0.2, H * 0.45)
        orb.setColorAt(0.0, QColor(0, 102, 255, 35))
        orb.setColorAt(1.0, QColor(0, 102, 255, 0))
        painter.fillRect(self.rect(), QBrush(orb))

        # Soft glow orb at bottom-left
        orb2 = QRadialGradient(W * 0.15, H * 0.85, H * 0.40)
        orb2.setColorAt(0.0, QColor(0, 245, 255, 25))
        orb2.setColorAt(1.0, QColor(0, 245, 255, 0))
        painter.fillRect(self.rect(), QBrush(orb2))

        # Draw floating particles
        for p in self._particles:
            px = int(p['x'] * W)
            py = int(p['y'] * H)
            r = p['r']
            alpha = int(p['opacity'] * 255)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(140, 180, 255, alpha)))
            painter.drawEllipse(QPoint(px, py), int(r), int(r))

        painter.end()


class LoginWindow(QWidget):
    login_success = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FitLife — Login")
        self.setMinimumSize(900, 620)
        self.setWindowFlags(Qt.WindowType.Window)
        self._lockout_timer = QTimer(self)
        self._lockout_timer.timeout.connect(self._update_lockout_countdown)
        self._lockout_seconds = 0
        self._worker = None
        self._error_hide_timer = QTimer(self)
        self._error_hide_timer.setSingleShot(True)
        self._error_hide_timer.timeout.connect(self._hide_error)
        self._setup_ui()
        # Trigger card fade-in animation after show
        QTimer.singleShot(50, self._animate_card_in)

    def _setup_ui(self):
        # Full-window animated background
        self.bg = AnimatedBackground(self)
        self.bg.setGeometry(self.rect())

        # Center layout on bg
        center_layout = QVBoxLayout(self.bg)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setContentsMargins(0, 0, 0, 0)

        # ── Glass Card ────────────────────────────────────────────────────────
        self.card = QFrame()
        self.card.setFixedWidth(440)
        self.card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.06);
                border: none;
                border-radius: 24px;
            }
        """)

        # Glow shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(70)
        shadow.setColor(QColor(0, 102, 255, 100))
        shadow.setOffset(0, 0)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(44, 44, 44, 40)
        card_layout.setSpacing(0)

        # ── Logo area ─────────────────────────────────────────────────────────
        icon_lbl = QLabel()
        from ui.components.icons import get_icon
        icon_lbl.setPixmap(get_icon("brand", color="#00F5FF", size=56).pixmap(56, 56))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon_lbl)
        card_layout.addSpacing(8)

        brand_lbl = QLabel("FitLife")
        brand_lbl.setStyleSheet("""
            font-size: 34px;
            font-weight: 900;
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #38BDF8, stop:1 #00F5FF);
            background: transparent;
            letter-spacing: 2px;
        """)
        brand_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(brand_lbl)
        card_layout.addSpacing(4)

        tagline_lbl = QLabel("Male Fitness Chain ERP")
        tagline_lbl.setStyleSheet(
            "font-size: 13px; color: rgba(255,255,255,0.45); background: transparent;"
        )
        tagline_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(tagline_lbl)
        card_layout.addSpacing(32)

        # ── Username field ────────────────────────────────────────────────────
        user_lbl = QLabel("Username")
        user_lbl.setStyleSheet(
            "font-size: 12px; color: rgba(255,255,255,0.55); "
            "font-weight: 600; background: transparent;"
        )
        card_layout.addWidget(user_lbl)
        card_layout.addSpacing(5)

        # Username row with icon overlay
        user_row = QHBoxLayout()
        user_row.setSpacing(0)
        user_icon = QLabel()
        user_icon.setFixedSize(44, 44)
        from ui.components.icons import get_icon
        user_icon.setPixmap(get_icon("user", color="rgba(255,255,255,0.6)", size=18).pixmap(18, 18))
        user_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_icon.setStyleSheet(
            "background: rgba(255,255,255,0.08); "
            "border: none; border-radius: 12px 0 0 12px;"
        )
        user_row.addWidget(user_icon)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setMinimumHeight(44)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.08);
                border: none;
                border-radius: 0 12px 12px 0;
                padding: 0 14px;
                color: #F0F4FF;
                font-size: 14px;
                selection-background-color: #0066FF;
            }
            QLineEdit:focus {
                border: none;
                background: rgba(0,102,255,0.12);
            }
        """)
        user_row.addWidget(self.username_input)
        card_layout.addLayout(user_row)

        self.username_err = QLabel("")
        self.username_err.setStyleSheet(
            "color: #FF2D78; font-size: 11px; background: transparent; margin-top: 2px;"
        )
        card_layout.addWidget(self.username_err)
        card_layout.addSpacing(14)

        # ── Password field ────────────────────────────────────────────────────
        pass_lbl = QLabel("Password")
        pass_lbl.setStyleSheet(
            "font-size: 12px; color: rgba(255,255,255,0.55); "
            "font-weight: 600; background: transparent;"
        )
        card_layout.addWidget(pass_lbl)
        card_layout.addSpacing(5)

        pass_row = QHBoxLayout()
        pass_row.setSpacing(0)

        pass_icon = QLabel()
        pass_icon.setFixedSize(44, 44)
        from ui.components.icons import get_icon
        pass_icon.setPixmap(get_icon("lock", color="rgba(255,255,255,0.6)", size=18).pixmap(18, 18))
        pass_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pass_icon.setStyleSheet(
            "background: rgba(255,255,255,0.08); "
            "border: none; border-radius: 12px 0 0 12px;"
        )
        pass_row.addWidget(pass_icon)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(44)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.08);
                border: none;
                border-radius: 0;
                padding: 0 14px;
                color: #F0F4FF;
                font-size: 14px;
                selection-background-color: #0066FF;
            }
            QLineEdit:focus {
                border: none;
                background: rgba(0,102,255,0.12);
            }
        """)
        self.password_input.returnPressed.connect(self._attempt_login)
        pass_row.addWidget(self.password_input)

        self.eye_btn = QPushButton()
        self.eye_btn.setFixedSize(44, 44)
        self.eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.eye_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.08);
                border: none;
                border-radius: 0 12px 12px 0;
            }
            QPushButton:hover { background: rgba(0,102,255,0.15); }
        """)
        self.eye_btn.clicked.connect(self._toggle_password)
        pass_row.addWidget(self.eye_btn)
        card_layout.addLayout(pass_row)
        
        # Initial eye icon
        self._update_eye_icon()

        self.pass_err = QLabel("")
        self.pass_err.setStyleSheet(
            "color: #FF2D78; font-size: 11px; background: transparent; margin-top: 2px;"
        )
        card_layout.addWidget(self.pass_err)
        card_layout.addSpacing(16)

        # ── Error message ─────────────────────────────────────────────────────
        self.error_lbl = QLabel("")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_lbl.setStyleSheet("""
            QLabel {
                background: rgba(255, 45, 120, 0.12);
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                color: #FF8FAB;
                font-size: 13px;
            }
        """)
        self.error_lbl.hide()
        card_layout.addWidget(self.error_lbl)
        card_layout.addSpacing(8)

        # ── Login button ──────────────────────────────────────────────────────
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setMinimumHeight(52)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0066FF, stop:1 #1D4ED8);
                border: none;
                border-radius: 12px;
                color: #FFFFFF;
                font-size: 15px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3B82F6, stop:1 #0066FF);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1D4ED8, stop:1 #1E3A8A);
                padding-top: 2px;
            }
            QPushButton:disabled {
                background: rgba(107, 114, 128, 0.5);
                color: rgba(255,255,255,0.4);
            }
        """)
        self.login_btn.clicked.connect(self._attempt_login)
        card_layout.addWidget(self.login_btn)
        card_layout.addSpacing(20)

        # ── Footer ────────────────────────────────────────────────────────────
        footer_lbl = QLabel("FitLife v1.0 — Male Fitness Management")
        footer_lbl.setStyleSheet(
            "font-size: 11px; color: rgba(255,255,255,0.25); background: transparent;"
        )
        footer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(footer_lbl)

        center_layout.addWidget(self.card)

        # Outer layout
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.bg)

    def _animate_card_in(self):
        """Fade-in + slide-up animation for the card on load."""
        # Use geometry animation for slide-up effect
        if not self.card.isVisible():
            return
        start_geo = self.card.geometry()
        end_geo = QRect(start_geo.x(), start_geo.y(), start_geo.width(), start_geo.height())
        slide_start = QRect(start_geo.x(), start_geo.y() + 24,
                            start_geo.width(), start_geo.height())
        self._anim = QPropertyAnimation(self.card, b"geometry")
        self._anim.setDuration(420)
        self._anim.setStartValue(slide_start)
        self._anim.setEndValue(end_geo)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.bg.setGeometry(self.rect())

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
        self.eye_btn.setIcon(get_icon(icon_name, color="rgba(255,255,255,0.65)", size=18))
        self.eye_btn.setIconSize(QSize(18, 18))

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
