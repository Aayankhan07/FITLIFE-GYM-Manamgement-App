"""
FitLife — Reusable Glass Card Component
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt


class GlassCard(QFrame):
    """A glassmorphism-styled card container."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glassCard")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.setSpacing(12)
        
        # Soft elevation shadow
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 45))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

    def card_layout(self) -> QVBoxLayout:
        return self._layout


class KPICard(QFrame):
    """KPI metric card with title, value, icon, and trend indicator."""

    def __init__(self, title: str, value: str, icon: str = "",
                 trend: str = "", accent_color: str = "#0066FF", parent=None):
        super().__init__(parent)
        self.setObjectName("kpiCard")
        self.setMinimumSize(180, 110)
        self.setMaximumHeight(130)
        
        # Soft colored glow shadow
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        # Parse hex accent color to add a soft glowing shadow
        glow_color = QColor(accent_color)
        glow_color.setAlpha(35)  # low opacity glow
        shadow.setColor(glow_color)
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        main = QVBoxLayout(self)
        main.setContentsMargins(18, 16, 18, 16)
        main.setSpacing(6)

        # Top row: icon + trend
        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 22px; color: {accent_color};")
        top.addWidget(icon_lbl)
        top.addStretch()
        if trend:
            trend_lbl = QLabel(trend)
            color = "#00E676" if trend.startswith("▲") else "#FF2D78"
            trend_lbl.setStyleSheet(f"font-size: 12px; color: {color}; font-weight:bold;")
            top.addWidget(trend_lbl)
        main.addLayout(top)

        # Value
        self.val_lbl = QLabel(value)
        self.val_lbl.setStyleSheet(
            f"font-size: 26px; font-weight: bold; color: {accent_color};"
        )
        main.addWidget(self.val_lbl)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setObjectName("labelMuted")
        title_lbl.setStyleSheet("font-size: 12px;")
        main.addWidget(title_lbl)

        # Accent top border via stylesheet
        self.setStyleSheet(
            f"QFrame#kpiCard {{ border-top: 3px solid {accent_color}; }}"
        )

    def set_value(self, value: str):
        self.val_lbl.setText(value)


class SectionHeader(QLabel):
    """Bold section heading label."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("heading2")


class MutedLabel(QLabel):
    """Muted secondary text label."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("labelMuted")


class StatusBadge(QLabel):
    """Colored status badge pill with explicit text colors."""

    STATUS_COLORS = {
        "Active":               ("#001A0A", "#00E676"),
        "Inactive":             ("#FFFFFF", "#4B5563"),
        "Maintenance":          ("#1A0F00", "#FFB800"),
        "Suspended":            ("#FFFFFF", "#F97316"),
        "Expired":              ("#FFFFFF", "#6B7280"),
        "Paid":                 ("#001A0A", "#00E676"),
        "Unpaid":               ("#FFFFFF", "#FF2D78"),
        "Partial":              ("#1A0F00", "#FFB800"),
        "Overdue":              ("#FCA5A5", "#7F1D1D"),
        "Pending":              ("#FFFFFF", "#3B82F6"),
        "Pending Verification": ("#1A0F00", "#FFB800"),
        "Trainer Approved":     ("#001A0A", "#00E676"),
        "Approved":             ("#001A0A", "#00E676"),
        "Draft":                ("#FFFFFF", "#6B7280"),
        "Completed":            ("#F0F6FF", "#1D4ED8"),
        "Rejected":             ("#FFFFFF", "#FF2D78"),
        "New":                  ("#001A0A", "#00E676"),
        "Good":                 ("#001F20", "#00F5FF"),
        "Fair":                 ("#1A0F00", "#FFB800"),
        "Damaged":              ("#FFFFFF", "#FF2D78"),
        "Retired":              ("#FFFFFF", "#6B7280"),
        "Present":              ("#001A0A", "#00E676"),
        "Absent":               ("#FFFFFF", "#FF2D78"),
        "Late":                 ("#1A0F00", "#FFB800"),
    }

    STATUS_LABELS = {
        "Active":    "✓ Active",
        "Inactive":  "✗ Inactive",
        "Maintenance":"🔧 Maintenance",
        "Suspended": "⛔ Suspended",
        "Expired":   "⌛ Expired",
        "Paid":      "✓ Paid",
        "Unpaid":    "✗ Unpaid",
        "Partial":   "~ Partial",
        "Overdue":   "⚠ Overdue",
        "Pending":   "⏳ Pending",
        "Approved":  "✓ Approved",
        "Rejected":  "✗ Rejected",
        "Present":   "✓ Present",
        "Absent":    "✗ Absent",
        "Late":      "~ Late",
        "Good":      "✓ Good",
        "Fair":      "~ Fair",
        "Damaged":   "⚠ Damaged",
        "Retired":   "⌛ Retired",
    }

    def __init__(self, status: str, parent=None):
        super().__init__(status, parent)
        self.set_status(status)

    def set_status(self, status: str):
        display = self.STATUS_LABELS.get(status, status)
        self.setText(display)
        # text_color (fg) is the foreground text, bg is the background fill
        fg, bg = self.STATUS_COLORS.get(status, ("#FFFFFF", "#374151"))
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {bg};
                border-radius: 12px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: bold;
                min-width: 70px;
            }}
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
