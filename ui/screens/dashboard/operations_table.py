"""
FitLife — Operations Table Widget with Expandable In-Row Drawer
Matches GYM-MANAGEMENT operations table:
- Segmented tab filter: Live Floor, All Members, Renewals Due, Equipment Health, Turnstiles & Gates
- Fast Check-In launch action
- Expandable In-Row accordion drawer displaying 4 stat cards (Account Status, Plan Tier, Weekly Visits, Fitness Gauge)
- Instant clock in/out & renew actions
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont
from ui.theme.theme_manager import ThemeManager
from ui.components.icons import get_icon
import services.member_service as member_svc
import services.attendance_service as att_svc
import services.equipment_service as equip_svc


class FitnessScoreGauge(QWidget):
    """Circular ring progress gauge matching GYM-MANAGEMENT."""
    def __init__(self, score: int = 85, parent=None):
        super().__init__(parent)
        self.score = score
        self.setFixedSize(48, 48)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_dark = ThemeManager.current_theme() == "dark"
        cx, cy = 24.0, 24.0
        r = 18.0

        # Background track
        painter.setPen(QPen(QColor("#2B2F38") if is_dark else QColor("#F0F2F5"), 3))
        painter.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))

        # Progress Arc
        span = int((self.score / 100.0) * 360 * 16)
        painter.setPen(QPen(QColor("#FA5A3C"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(QRectF(cx - r, cy - r, 2 * r, 2 * r), 90 * 16, -span)

        # Center Score
        painter.setFont(QFont("Inter", 9, QFont.Weight.ExtraBold))
        painter.setPen(QColor("#F4F5F8") if is_dark else QColor("#18181B"))
        painter.drawText(QRectF(cx - 15, cy - 10, 30, 20), Qt.AlignmentFlag.AlignCenter, str(self.score))


class OperationsTableRow(QFrame):
    """Interactive member row with expandable accordion drawer."""
    toggled = pyqtSignal()
    action_performed = pyqtSignal()

    def __init__(self, member_data: dict, is_checked_in: bool = False, branch_id: int = 1, parent=None):
        super().__init__(parent)
        self.member = member_data
        self.is_checked_in = is_checked_in
        self.branch_id = branch_id
        self._expanded = False
        self.setObjectName("opTableRow")
        self._setup_ui()

    def _setup_ui(self):
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(12, 10, 12, 10)
        self.root.setSpacing(8)

        # ── Main Row Bar ──────────────────────────────────────────────────────
        self.main_bar = QWidget()
        bar_layout = QHBoxLayout(self.main_bar)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(12)

        # Status indicator
        status_box = QHBoxLayout()
        status_box.setSpacing(6)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {'#10B981' if self.is_checked_in else '#FA5A3C'}; font-size: 10px;")
        status_lbl = QLabel("Live on Floor" if self.is_checked_in else f"Expires {self.member.get('expiry_date', 'Active')}")
        status_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #8C93A3;")
        status_box.addWidget(dot)
        status_box.addWidget(status_lbl)
        bar_layout.addLayout(status_box)

        # Member Name
        name_lbl = QLabel(f"{self.member.get('first_name', '')} {self.member.get('last_name', '')}")
        name_lbl.setStyleSheet("font-size: 13px; font-weight: 800;")
        bar_layout.addWidget(name_lbl)

        # Email
        email_lbl = QLabel(self.member.get("email", ""))
        email_lbl.setStyleSheet("font-size: 11px; color: #6B7280; font-family: monospace;")
        bar_layout.addWidget(email_lbl)

        bar_layout.addStretch()

        # Quality Badge
        badge = QLabel(f" {self.member.get('status', 'Active').upper()} ")
        badge.setStyleSheet("""
            font-size: 10px; font-weight: 800;
            padding: 2px 8px; border-radius: 6px;
            background-color: rgba(16, 185, 129, 0.12);
            color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3);
        """)
        bar_layout.addWidget(badge)

        # Expand Arrow
        self.arrow_btn = QPushButton("▼")
        self.arrow_btn.setFixedSize(24, 24)
        self.arrow_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.arrow_btn.setStyleSheet("border: none; background: transparent; font-size: 10px; color: #8C93A3;")
        self.arrow_btn.clicked.connect(self.toggle_expand)
        bar_layout.addWidget(self.arrow_btn)

        self.root.addWidget(self.main_bar)

        # ── Expandable Drawer Panel ───────────────────────────────────────────
        self.drawer = QFrame()
        self.drawer.setObjectName("drawerPanel")
        drawer_layout = QVBoxLayout(self.drawer)
        drawer_layout.setContentsMargins(12, 12, 12, 12)
        drawer_layout.setSpacing(12)

        # 4 Stat Cards
        stats_grid = QHBoxLayout()
        stats_grid.setSpacing(10)

        # Card 1: Account Status
        c1 = self._stat_card("ACCOUNT STATUS", f"{self.member.get('status', 'Active')} Athlete", "Dues: Fully Paid", "#10B981")
        # Card 2: Plan
        c2 = self._stat_card("MEMBERSHIP PLAN", f"Tier #{self.member.get('membership_id', 1)} Access", f"Phone: {self.member.get('phone', 'N/A')}", "#8C93A3")
        # Card 3: Weekly Visits
        c3 = self._stat_card("WEEKLY VISITS", "4 Sessions / Wk", "Consistent Lifter", "#3B82F6")

        # Card 4: Fitness Score Ring Gauge
        c4 = QFrame()
        c4_layout = QHBoxLayout(c4)
        c4_layout.setContentsMargins(10, 8, 10, 8)
        c4_layout.setSpacing(10)
        c4_layout.addWidget(FitnessScoreGauge(score=85))

        c4_text = QVBoxLayout()
        c4_text.setSpacing(1)
        c4_title = QLabel("FITNESS SCORE")
        c4_title.setStyleSheet("font-size: 9px; font-weight: 800; color: #8C93A3;")
        c4_sub = QLabel("High Adherence")
        c4_sub.setStyleSheet("font-size: 11px; font-weight: 700; color: #10B981;")
        c4_text.addWidget(c4_title)
        c4_text.addWidget(c4_sub)
        c4_layout.addLayout(c4_text)

        stats_grid.addWidget(c1)
        stats_grid.addWidget(c2)
        stats_grid.addWidget(c3)
        stats_grid.addWidget(c4)
        drawer_layout.addLayout(stats_grid)

        # Drawer Footer Actions
        footer = QHBoxLayout()
        mid_lbl = QLabel(f"Athlete ID: #{self.member.get('member_id', 0)}")
        mid_lbl.setStyleSheet("font-size: 11px; color: #8C93A3;")
        footer.addWidget(mid_lbl)
        footer.addStretch()

        if self.is_checked_in:
            clock_btn = QPushButton("Clock Out Member")
            clock_btn.setStyleSheet("""
                QPushButton {
                    background: transparent; border: 1px solid #EF4444; border-radius: 8px;
                    color: #EF4444; font-size: 11px; font-weight: bold; padding: 4px 12px;
                }
                QPushButton:hover { background: rgba(239, 68, 68, 0.15); }
            """)
            clock_btn.clicked.connect(self._clock_out)
        else:
            clock_btn = QPushButton("Clock In to Floor")
            clock_btn.setStyleSheet("""
                QPushButton {
                    background: transparent; border: 1px solid #10B981; border-radius: 8px;
                    color: #10B981; font-size: 11px; font-weight: bold; padding: 4px 12px;
                }
                QPushButton:hover { background: rgba(16, 185, 129, 0.15); }
            """)
            clock_btn.clicked.connect(self._clock_in)
        footer.addWidget(clock_btn)

        drawer_layout.addLayout(footer)
        self.drawer.setVisible(False)
        self.root.addWidget(self.drawer)

        self.update_styles()

    def _stat_card(self, title: str, main: str, sub: str, sub_color: str) -> QFrame:
        is_dark = ThemeManager.current_theme() == "dark"
        card = QFrame()
        card_bg = "#201C1B" if is_dark else "#FFFFFF"
        border = "#3A2220" if is_dark else "#FEE2E2"
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {card_bg};
                border: 1px solid {border};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 9px; font-weight: 800; color: #8C93A3;")
        m_lbl = QLabel(main)
        m_lbl.setStyleSheet("font-size: 12px; font-weight: 800;")
        s_lbl = QLabel(sub)
        s_lbl.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {sub_color};")

        layout.addWidget(t_lbl)
        layout.addWidget(m_lbl)
        layout.addWidget(s_lbl)
        return card

    def toggle_expand(self):
        self._expanded = not self._expanded
        self.drawer.setVisible(self._expanded)
        self.arrow_btn.setText("▲" if self._expanded else "▼")
        self.update_styles()
        self.toggled.emit()

    def update_styles(self):
        is_dark = ThemeManager.current_theme() == "dark"
        bg = "#181A1F" if is_dark else "#FFFFFF"
        border = "#24272D" if is_dark else "#E6E9EE"

        if self._expanded:
            self.setStyleSheet(f"""
                QFrame#opTableRow {{
                    background-color: {"#201816" if is_dark else "#FFF7F5"};
                    border: 1px solid #FA5A3C;
                    border-radius: 12px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#opTableRow {{
                    background-color: {bg};
                    border: 1px solid {border};
                    border-radius: 12px;
                }}
                QFrame#opTableRow:hover {{
                    border-color: #FA5A3C;
                }}
            """)

    def _clock_in(self):
        try:
            att_svc.check_in_member(self.member.get("member_id"), self.branch_id, "Floor Table")
        except Exception:
            pass
        self.action_performed.emit()

    def _clock_out(self):
        try:
            att_svc.check_out_member(self.member.get("member_id"))
        except Exception:
            pass
        self.action_performed.emit()


class OperationsTableWidget(QFrame):
    """Complete segmented operations table with drawer expansion and Fast Check-in modal trigger."""
    fast_checkin_requested = pyqtSignal()

    def __init__(self, branch_id: int = 1, parent=None):
        super().__init__(parent)
        self.branch_id = branch_id
        self._active_tab = "floor"
        self.setObjectName("operationsTableCard")
        self._setup_ui()
        self.refresh_table()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(14)

        # Tab Segmented Header Bar
        hdr = QHBoxLayout()
        hdr.setSpacing(10)

        self.tab_container = QFrame()
        tab_layout = QHBoxLayout(self.tab_container)
        tab_layout.setContentsMargins(3, 3, 3, 3)
        tab_layout.setSpacing(4)

        self.tab_buttons = {}
        tabs = [
            ("floor", "Live Floor"),
            ("members", "All Members"),
            ("renewals", "Renewals Due"),
            ("equipment", "Equipment Health"),
            ("turnstiles", "Turnstiles & Gates"),
        ]
        for key, title in tabs:
            btn = QPushButton(title)
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._set_tab(k))
            tab_layout.addWidget(btn)
            self.tab_buttons[key] = btn

        hdr.addWidget(self.tab_container)
        hdr.addStretch()

        # Fast Check-in Action Button
        self.checkin_btn = QPushButton(" + Fast Check-In ")
        self.checkin_btn.setFixedHeight(30)
        self.checkin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkin_btn.clicked.connect(self.fast_checkin_requested.emit)
        hdr.addWidget(self.checkin_btn)

        root.addLayout(hdr)

        # Scrollable Rows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(8)

        scroll.setWidget(self.rows_container)
        root.addWidget(scroll, 1)

        self.update_styles()

    def _set_tab(self, key: str):
        self._active_tab = key
        self.update_styles()
        self.refresh_table()

    def refresh_table(self):
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Fetch active check-ins
        active_ids = set()
        try:
            active_logs = att_svc.get_active_checkins(self.branch_id) or []
            for al in active_logs:
                active_ids.add(al[1])
        except Exception:
            pass

        # Fetch all members
        members = []
        try:
            raw = member_svc.get_all_members() or []
            for r in raw:
                members.append({
                    "member_id": r[0],
                    "first_name": r[1],
                    "last_name": r[2],
                    "email": r[3],
                    "phone": r[4],
                    "status": r[5] if len(r) > 5 else "Active",
                    "expiry_date": r[8] if len(r) > 8 else "2026-12-31",
                    "membership_id": r[9] if len(r) > 9 else 1,
                })
        except Exception:
            pass

        # Filter based on tab
        if self._active_tab == "floor":
            display_list = [m for m in members if m["member_id"] in active_ids]
        elif self._active_tab == "renewals":
            display_list = [m for m in members if m.get("status") in ("Expired", "Inactive")][:10]
        elif self._active_tab == "equipment":
            # Show equipment items
            self._render_equipment_tab()
            return
        elif self._active_tab == "turnstiles":
            self._render_turnstile_tab()
            return
        else:
            display_list = members[:15]

        if not display_list:
            lbl = QLabel("No active records found for this view.")
            lbl.setStyleSheet("font-size: 12px; color: #8C93A3; padding: 20px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.rows_layout.addWidget(lbl)
        else:
            for m in display_list:
                is_in = m["member_id"] in active_ids
                row = OperationsTableRow(m, is_checked_in=is_in, branch_id=self.branch_id)
                row.action_performed.connect(self.refresh_table)
                self.rows_layout.addWidget(row)

        self.rows_layout.addStretch()

    def _render_equipment_tab(self):
        try:
            equips = equip_svc.get_all_equipment(self.branch_id) or []
        except Exception:
            equips = []
        for eq in equips[:12]:
            card = QFrame()
            card.setStyleSheet("background-color: rgba(255,255,255,0.03); border-radius: 10px; padding: 8px;")
            l = QHBoxLayout(card)
            l.addWidget(QLabel(f"<b>{eq[1]}</b> ({eq[2]})"))
            l.addStretch()
            status = eq[4] if len(eq) > 4 else "Operational"
            st_lbl = QLabel(f" {status} ")
            st_lbl.setStyleSheet("color: #10B981; font-weight: bold;")
            l.addWidget(st_lbl)
            self.rows_layout.addWidget(card)
        self.rows_layout.addStretch()

    def _render_turnstile_tab(self):
        gates = [
            ("GATE-NORTH-01", "Downtown Hub Turnstile", "ONLINE"),
            ("GATE-SOUTH-02", "South Wing RFID Gate", "ONLINE"),
            ("GATE-VIP-03", "VIP Locker Entry", "STANDBY"),
        ]
        for gid, desc, st in gates:
            card = QFrame()
            card.setStyleSheet("background-color: rgba(255,255,255,0.03); border-radius: 10px; padding: 10px;")
            l = QHBoxLayout(card)
            l.addWidget(QLabel(f"<b>{gid}</b> — {desc}"))
            l.addStretch()
            st_lbl = QLabel(f" ● {st} ")
            st_lbl.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px;")
            l.addWidget(st_lbl)
            self.rows_layout.addWidget(card)
        self.rows_layout.addStretch()

    def update_styles(self):
        is_dark = ThemeManager.current_theme() == "dark"
        card_bg = "#141518" if is_dark else "#FFFFFF"
        border_color = "#24272D" if is_dark else "#E6E9EE"
        tab_bg = "#1E2129" if is_dark else "#F4F5F8"

        self.setStyleSheet(f"""
            QFrame#operationsTableCard {{
                background-color: {card_bg};
                border: 1px solid {border_color};
                border-radius: 16px;
            }}
        """)

        self.tab_container.setStyleSheet(f"""
            QFrame {{
                background-color: {tab_bg};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
        """)

        self.checkin_btn.setStyleSheet("""
            QPushButton {
                background-color: #FA5A3C;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
                padding: 0 14px;
            }
            QPushButton:hover { background-color: #E54829; }
        """)

        for k, btn in self.tab_buttons.items():
            if k == self._active_tab:
                btn.setStyleSheet(f"""
                    background-color: {"#282C36" if is_dark else "#FFFFFF"};
                    border: none;
                    border-radius: 8px;
                    color: {"#FFFFFF" if is_dark else "#18181B"};
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 10px;
                """)
            else:
                btn.setStyleSheet(f"""
                    background-color: transparent;
                    border: none;
                    color: {"#9CA3AF" if is_dark else "#6B7280"};
                    font-size: 11px;
                    font-weight: 600;
                    padding: 0 10px;
                """)
