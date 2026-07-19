"""
FitLife — Confirm Dialog Component
Used for all destructive actions and notifications without emojis.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.theme.theme_manager import ThemeManager


class ConfirmDialog(QDialog):
    """
    Standard confirmation dialog for destructive actions.
    Usage:
        dlg = ConfirmDialog("Delete Member", "Are you sure you want to delete Ahmed Siddiqui?\nThis action cannot be undone.", "Delete", "danger")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # proceed
    """

    def __init__(self, title: str, message: str,
                 confirm_text: str = "Confirm",
                 confirm_type: str = "danger",   # "danger" | "primary" | "warning"
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Card container
        card = QFrame()
        card.setObjectName("glassCard")
        c = ThemeManager.colors()
        card.setStyleSheet(f"""
            QFrame#glassCard {{
                background: {c['bg_secondary']};
                border: 1px solid {c['glass_border']};
                border-radius: 16px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 24)
        card_layout.setSpacing(16)

        # Icon row
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        from ui.components.icons import get_icon
        accent_key = {
            "danger": ("error", "accent_danger"),
            "primary": ("info", "accent_primary"),
            "warning": ("warning", "accent_warning"),
        }
        icon_name, color_var = accent_key.get(confirm_type, ("warning", "accent_warning"))
        color = ThemeManager.color(color_var)
        icon_lbl.setPixmap(get_icon(icon_name, color=color, size=48).pixmap(48, 48))
        card_layout.addWidget(icon_lbl)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setObjectName("heading2")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
        card_layout.addWidget(title_lbl)

        # Message
        msg_lbl = QLabel(message)
        msg_lbl.setObjectName("labelMuted")
        msg_lbl.setWordWrap(True)
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(msg_lbl)

        card_layout.addSpacing(8)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btnSecondary")
        cancel_btn.setMinimumHeight(42)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton(confirm_text)
        confirm_btn.setObjectName(
            "btnDanger" if confirm_type == "danger" else
            "btnWarning" if confirm_type == "warning" else
            "btnPrimary"
        )
        confirm_btn.setMinimumHeight(42)
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.clicked.connect(self.accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(confirm_btn)
        card_layout.addLayout(btn_row)

        layout.addWidget(card)


class InfoDialog(QDialog):
    """Simple info/success dialog."""

    def __init__(self, title: str, message: str,
                 dialog_type: str = "info",  # info | success | error | warning
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(380)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("glassCard")
        c = ThemeManager.colors()
        card.setStyleSheet(f"QFrame#glassCard {{ background:{c['bg_secondary']}; border:1px solid {c['glass_border']}; border-radius:16px; }}")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(28, 28, 28, 24)
        cl.setSpacing(14)

        accent_key = {
            "info": ("info", "accent_primary"),
            "success": ("success", "accent_success"),
            "error": ("error", "accent_danger"),
            "warning": ("warning", "accent_warning"),
        }

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        from ui.components.icons import get_icon
        icon_name, color_var = accent_key.get(dialog_type, ("info", "accent_primary"))
        color = ThemeManager.color(color_var)
        icon_lbl.setPixmap(get_icon(icon_name, color=color, size=48).pixmap(48, 48))
        cl.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(title_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setObjectName("labelMuted")
        msg_lbl.setWordWrap(True)
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(msg_lbl)

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("btnPrimary")
        ok_btn.setMinimumHeight(42)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        cl.addWidget(ok_btn)

        layout.addWidget(card)
