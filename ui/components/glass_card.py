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
            color = ThemeManager.color("accent_primary")
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
        "Active":               ("#10B981", "rgba(16, 185, 129, 0.15)"),
        "Inactive":             ("#6B7280", "rgba(107, 114, 128, 0.15)"),
        "Maintenance":          ("#F59E0B", "rgba(245, 158, 11, 0.15)"),
        "Suspended":            ("#FA5A3C", "rgba(250, 90, 60, 0.15)"),
        "Expired":              ("#EF4444", "rgba(239, 68, 68, 0.15)"),
        "Paid":                 ("#10B981", "rgba(16, 185, 129, 0.15)"),
        "Unpaid":               ("#EF4444", "rgba(239, 68, 68, 0.15)"),
        "Partial":              ("#F59E0B", "rgba(245, 158, 11, 0.15)"),
        "Overdue":              ("#EF4444", "rgba(239, 68, 68, 0.15)"),
        "Pending":              ("#3B82F6", "rgba(59, 130, 246, 0.15)"),
        "Pending Verification": ("#F59E0B", "rgba(245, 158, 11, 0.15)"),
        "Trainer Approved":     ("#10B981", "rgba(16, 185, 129, 0.15)"),
        "Approved":             ("#10B981", "rgba(16, 185, 129, 0.15)"),
        "Draft":                ("#6B7280", "rgba(107, 114, 128, 0.15)"),
        "Completed":            ("#3B82F6", "rgba(59, 130, 246, 0.15)"),
        "Rejected":             ("#EF4444", "rgba(239, 68, 68, 0.15)"),
        "New":                  ("#10B981", "rgba(16, 185, 129, 0.15)"),
        "Good":                 ("#10B981", "rgba(16, 185, 129, 0.15)"),
        "Fair":                 ("#F59E0B", "rgba(245, 158, 11, 0.15)"),
        "Damaged":              ("#EF4444", "rgba(239, 68, 68, 0.15)"),
        "Retired":              ("#6B7280", "rgba(107, 114, 128, 0.15)"),
        "Present":              ("#10B981", "rgba(16, 185, 129, 0.15)"),
        "Absent":               ("#EF4444", "rgba(239, 68, 68, 0.15)"),
        "Late":                 ("#F59E0B", "rgba(245, 158, 11, 0.15)"),
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

    STATUS_COLORS_LIGHT = {
        "Active":               ("#047857", "rgba(16, 185, 129, 0.16)", "#A7F3D0"),
        "Inactive":             ("#4B5563", "rgba(107, 114, 128, 0.14)", "#E5E7EB"),
        "Maintenance":          ("#B45309", "rgba(245, 158, 11, 0.16)", "#FDE68A"),
        "Suspended":            ("#C93A1E", "rgba(250, 90, 60, 0.16)", "#FECACA"),
        "Expired":              ("#B91C1C", "rgba(239, 68, 68, 0.16)", "#FECACA"),
        "Paid":                 ("#047857", "rgba(16, 185, 129, 0.16)", "#A7F3D0"),
        "Unpaid":               ("#B91C1C", "rgba(239, 68, 68, 0.16)", "#FECACA"),
        "Partial":              ("#B45309", "rgba(245, 158, 11, 0.16)", "#FDE68A"),
        "Overdue":              ("#B91C1C", "rgba(239, 68, 68, 0.16)", "#FECACA"),
        "Pending":              ("#1D4ED8", "rgba(59, 130, 246, 0.16)", "#BFDBFE"),
        "Pending Verification": ("#B45309", "rgba(245, 158, 11, 0.16)", "#FDE68A"),
        "Trainer Approved":     ("#047857", "rgba(16, 185, 129, 0.16)", "#A7F3D0"),
        "Approved":             ("#047857", "rgba(16, 185, 129, 0.16)", "#A7F3D0"),
        "Draft":                ("#4B5563", "rgba(107, 114, 128, 0.14)", "#E5E7EB"),
        "Completed":            ("#1D4ED8", "rgba(59, 130, 246, 0.16)", "#BFDBFE"),
        "Rejected":             ("#B91C1C", "rgba(239, 68, 68, 0.16)", "#FECACA"),
        "New":                  ("#047857", "rgba(16, 185, 129, 0.16)", "#A7F3D0"),
        "Good":                 ("#047857", "rgba(16, 185, 129, 0.16)", "#A7F3D0"),
        "Fair":                 ("#B45309", "rgba(245, 158, 11, 0.16)", "#FDE68A"),
        "Damaged":              ("#B91C1C", "rgba(239, 68, 68, 0.16)", "#FECACA"),
        "Retired":              ("#4B5563", "rgba(107, 114, 128, 0.14)", "#E5E7EB"),
        "Present":              ("#047857", "rgba(16, 185, 129, 0.16)", "#A7F3D0"),
        "Absent":               ("#B91C1C", "rgba(239, 68, 68, 0.16)", "#FECACA"),
        "Late":                 ("#B45309", "rgba(245, 158, 11, 0.16)", "#FDE68A"),
    }

    def __init__(self, status: str, parent=None):
        super().__init__(status, parent)
        self.set_status(status)

    def set_status(self, status: str):
        from ui.theme.theme_manager import ThemeManager
        display = self.STATUS_LABELS.get(status, status)
        self.setText(display)
        
        is_dark = ThemeManager.current_theme() == "dark"
        if is_dark:
            fg, bg = self.STATUS_COLORS.get(status, ("#FFFFFF", "#374151"))
            border_col = bg
        else:
            cfg = self.STATUS_COLORS_LIGHT.get(status, ("#18181B", "rgba(0,0,0,0.06)", "#E2E6ED"))
            fg, bg, border_col = cfg[0], cfg[1], cfg[2]

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border_col};
                border-radius: 12px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 700;
                min-width: 70px;
            }}
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
