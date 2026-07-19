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


EMOJI_MAP = {
    "🏠": "dashboard",
    "👥": "members",
    "💪": "trainers",
    "🏢": "branches",
    "📋": "plans",
    "📅": "attendance",
    "💳": "finance",
    "🏋️": "workout_plans",
    "🏋": "workout_plans",
    "🥗": "diet_plans",
    "📈": "progress",
    "🔧": "equipment",
    "👔": "staff",
    "📊": "analytics",
    "📄": "reports",
    "📓": "diary",
    "🔍": "audit",
    "⚙️": "settings",
    "⚙": "settings",
    "💰": "finance",
    "⏳": "schedule",
    "🕐": "schedule",
    "🏆": "progress",
    "🔴": "error",
    "⚠️": "warning",
    "❌": "error",
    "✅": "success",
    "🔥": "progress",
    "🌾": "plans",
    "🥑": "diet_plans",
    "⚖️": "progress",
    "⚖": "progress",
    "🔔": "bell"
}


class KPICard(QFrame):
    """KPI metric card with title, value, icon, and trend indicator."""

    def __init__(self, title: str, value: str, icon: str = "",
                 trend: str = "", accent_color: str = "#0066FF", parent=None):
        super().__init__(parent)
        self.setObjectName("kpiCard")
        self.setMinimumSize(180, 115)
        self.setMaximumHeight(135)
        self._icon_str = icon
        
        # Map color to standard names for style properties
        h = accent_color.upper()
        if "0066FF" in h or "PRIMARY" in h:
            self._accent_name = "primary"
        elif "00F5FF" in h or "SECONDARY" in h:
            self._accent_name = "secondary"
        elif "00E676" in h or "SUCCESS" in h or "16A34A" in h:
            self._accent_name = "success"
        elif "FFB800" in h or "WARNING" in h or "D97706" in h:
            self._accent_name = "warning"
        elif "FF2D78" in h or "DANGER" in h or "DC2626" in h or "C0155A" in h:
            self._accent_name = "danger"
        else:
            self._accent_name = "primary"

        self.setProperty("accent", self._accent_name)

        # Soft colored glow shadow
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        main = QVBoxLayout(self)
        main.setContentsMargins(18, 16, 18, 16)
        main.setSpacing(6)

        # Top row: icon badge + trend
        top = QHBoxLayout()
        self.icon_lbl = QLabel()
        self.icon_lbl.setObjectName("kpiIconBadge")
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.refresh_icon()
        
        top.addWidget(self.icon_lbl)
        top.addStretch()
        if trend:
            trend_lbl = QLabel(trend)
            color = "#10B981" if trend.startswith("▲") else "#F43F5E"
            trend_lbl.setStyleSheet(f"font-size: 12px; color: {color}; font-weight: bold;")
            top.addWidget(trend_lbl)
        main.addLayout(top)

        # Value
        self.val_lbl = QLabel(value)
        self.val_lbl.setObjectName("kpiValue")
        main.addWidget(self.val_lbl)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setObjectName("kpiTitle")
        main.addWidget(title_lbl)

    def refresh_icon(self):
        from ui.components.icons import get_icon, SVG_ICONS
        from ui.theme.theme_manager import ThemeManager
        
        icon_key = EMOJI_MAP.get(self._icon_str, self._icon_str)
        if icon_key in SVG_ICONS:
            color = ThemeManager.color("accent_" + self._accent_name)
            self.icon_lbl.setPixmap(get_icon(icon_key, color=color, size=18).pixmap(18, 18))
        else:
            self.icon_lbl.setText(self._icon_str)

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
        "Active":    "Active",
        "Inactive":  "Inactive",
        "Maintenance":"Maintenance",
        "Suspended": "Suspended",
        "Expired":   "Expired",
        "Paid":      "Paid",
        "Unpaid":    "Unpaid",
        "Partial":   "Partial",
        "Overdue":   "Overdue",
        "Pending":   "Pending",
        "Approved":  "Approved",
        "Rejected":  "Rejected",
        "Present":   "Present",
        "Absent":    "Absent",
        "Late":      "Late",
        "Good":      "Good",
        "Fair":      "Fair",
        "Damaged":   "Damaged",
        "Retired":   "Retired",
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
