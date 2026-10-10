"""
FitLife — Fast Check-In Modal Dialog
Matches GYM-MANAGEMENT Fast Athlete Check-In modal overlay.
Allows instant search by athlete name/email and 1-click floor clock-in/out.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ui.theme.theme_manager import ThemeManager
from ui.components.icons import get_icon
import services.attendance_service as att_svc
import services.member_service as member_svc


class FastCheckInDialog(QDialog):
    checkin_changed = pyqtSignal()

    def __init__(self, branch_id: int = 1, parent=None):
        super().__init__(parent)
        self.branch_id = branch_id
        self.setWindowTitle("Fast Athlete Check-In")
        self.setFixedSize(480, 520)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._members = []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.container = QFrame()
        self.container.setObjectName("dialogContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        hdr_icon = QLabel()
        hdr_icon.setPixmap(get_icon("user_check", color="#FA5A3C", size=22).pixmap(22, 22))
        hdr.addWidget(hdr_icon)

        title = QLabel("Fast Athlete Check-In")
        title.setStyleSheet("font-size: 15px; font-weight: 800;")
        hdr.addWidget(title)

        hdr.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none; font-size: 14px; font-weight: bold; color: #8C93A3;
            }
            QPushButton:hover { color: #FA5A3C; }
        """)
        close_btn.clicked.connect(self.close)
        hdr.addWidget(close_btn)
        container_layout.addLayout(hdr)

        # Search Input
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search athlete by name or email...")
        self.search_box.setFixedHeight(38)
        self.search_box.textChanged.connect(self._filter_list)
        container_layout.addWidget(self.search_box)

        # Scroll Area with List
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)

        scroll.setWidget(self.list_widget)
        container_layout.addWidget(scroll, 1)

        main_layout.addWidget(self.container)
        self.update_styles()

    def update_styles(self):
        is_dark = ThemeManager.current_theme() == "dark"
        bg = "#181A1F" if is_dark else "#FFFFFF"
        border = "#2B2F38" if is_dark else "#E2E6ED"
        text = "#F4F5F8" if is_dark else "#18181B"
        input_bg = "#20232A" if is_dark else "#F8F9FB"

        self.container.setStyleSheet(f"""
            QFrame#dialogContainer {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 20px;
            }}
        """)

        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: {input_bg};
                border: 1px solid {border};
                border-radius: 12px;
                color: {text};
                padding: 0 14px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1.5px solid #FA5A3C;
            }}
        """)

    def _load_data(self):
        try:
            m_list = member_svc.get_all_members() or []
            self._members = m_list
        except Exception:
            self._members = []
        self._filter_list()

    def _filter_list(self):
        # Clear list
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        query = self.search_box.text().strip().lower()
        active_turnstile_ids = set()
        try:
            active_logs = att_svc.get_active_checkins(self.branch_id) or []
            for al in active_logs:
                active_turnstile_ids.add(al[1])  # member_id
        except Exception:
            pass

        count = 0
        for m in self._members:
            # m tuple schema: (member_id, first_name, last_name, email, phone, status, ...)
            mid = m[0]
            name = f"{m[1]} {m[2]}"
            email = m[3] or ""

            if query and (query not in name.lower() and query not in email.lower()):
                continue

            is_checked_in = mid in active_turnstile_ids
            row = self._create_member_row(mid, name, email, is_checked_in)
            self.list_layout.addWidget(row)
            count += 1
            if count >= 15:
                break

        self.list_layout.addStretch()

    def _create_member_row(self, mid: int, name: str, email: str, is_in: bool) -> QFrame:
        is_dark = ThemeManager.current_theme() == "dark"
        card = QFrame()
        bg = "#20232A" if is_dark else "#F8F9FB"
        border = "#2B2F38" if is_dark else "#E2E6ED"
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        info = QVBoxLayout()
        info.setSpacing(2)
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet("font-size: 13px; font-weight: 700;")
        lbl_email = QLabel(email)
        lbl_email.setStyleSheet("font-size: 11px; color: #8C93A3;")
        info.addWidget(lbl_name)
        info.addWidget(lbl_email)
        layout.addLayout(info)

        layout.addStretch()

        btn = QPushButton("Clock Out" if is_in else "Clock In")
        btn.setFixedHeight(30)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        if is_in:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(239, 68, 68, 0.15);
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 8px;
                    color: #EF4444; font-size: 11px; font-weight: bold;
                    padding: 0 12px;
                }
                QPushButton:hover { background-color: #EF4444; color: white; }
            """)
            btn.clicked.connect(lambda checked, m=mid: self._toggle_clock(m, "OUT"))
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(16, 185, 129, 0.15);
                    border: 1px solid rgba(16, 185, 129, 0.3);
                    border-radius: 8px;
                    color: #10B981; font-size: 11px; font-weight: bold;
                    padding: 0 12px;
                }
                QPushButton:hover { background-color: #10B981; color: white; }
            """)
            btn.clicked.connect(lambda checked, m=mid: self._toggle_clock(m, "IN"))

        layout.addWidget(btn)
        return card

    def _toggle_clock(self, member_id: int, direction: str):
        try:
            if direction == "IN":
                att_svc.check_in_member(member_id, self.branch_id, "Fast Check-In")
            else:
                att_svc.check_out_member(member_id)
        except Exception:
            pass
        self.checkin_changed.emit()
        self._load_data()
