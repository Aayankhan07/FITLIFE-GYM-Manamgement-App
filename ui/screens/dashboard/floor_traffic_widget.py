"""
FitLife — Live Gym Floor Traffic Widget (Custom QPainter)
Matches GYM-MANAGEMENT GymFloorTraffic.tsx:
- Semi-circular 180° analog gauge dial with dynamic needle sweep
- Dynamic status badge pill (Open Floor / Steady Flow / Peak Traffic)
- 16-hour crowd density forecast bar chart (6 AM to 10 PM)
"""
import math
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QLinearGradient, QPainterPath, QFont
)
from ui.theme.theme_manager import ThemeManager
from ui.components.icons import get_icon


class FloorTrafficDial(QWidget):
    """Semi-circular needle meter with colored arc bands."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(120)
        self._occupancy_percent = 54  # Default sample or dynamic

    def set_occupancy(self, pct: int):
        self._occupancy_percent = max(0, min(100, pct))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_dark = ThemeManager.current_theme() == "dark"
        W, H = self.width(), self.height()

        cx = W / 2.0
        cy = H - 15.0
        r = min(cx - 20, cy - 10)

        # Draw outer track arc
        track_pen = QPen(QColor("#24272D") if is_dark else QColor("#E2E6ED"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        rect_arc = QRectF(cx - r, cy - r, 2 * r, 2 * r)
        painter.drawArc(rect_arc, 0 * 16, 180 * 16)

        # Draw filled progress arc (Green -> Amber -> Coral)
        progress_angle = int((self._occupancy_percent / 100.0) * 180)
        prog_pen = QPen(QColor("#FA5A3C"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(prog_pen)
        # Note: In Qt drawArc, 180 is left, 0 is right. We sweep clockwise from 180 down.
        painter.drawArc(rect_arc, 180 * 16, -progress_angle * 16)

        # Draw Needle
        # needle angle: 0% = 180 deg (left), 100% = 0 deg (right)
        rad = math.radians(180 - (self._occupancy_percent / 100.0 * 180))
        needle_len = r - 12
        nx = cx + needle_len * math.cos(rad)
        ny = cy - needle_len * math.sin(rad)

        needle_pen = QPen(QColor("#FA5A3C"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(needle_pen)
        painter.drawLine(QPointF(cx, cy), QPointF(nx, ny))

        # Center Pivot Dot
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#F4F5F8") if is_dark else QColor("#18181B")))
        painter.drawEllipse(QPointF(cx, cy), 6, 6)

        # Draw occupancy percentage in center
        painter.setFont(QFont("Inter", 13, QFont.Weight.ExtraBold))
        painter.setPen(QColor("#F4F5F8") if is_dark else QColor("#18181B"))
        painter.drawText(QRectF(cx - 50, cy - 40, 100, 24), Qt.AlignmentFlag.AlignCenter, f"{self._occupancy_percent}%")

        painter.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        painter.setPen(QColor("#9CA3AF") if is_dark else QColor("#8C93A3"))
        painter.drawText(QRectF(cx - 50, cy - 20, 100, 16), Qt.AlignmentFlag.AlignCenter, "CAPACITY")


class HourlyForecastBars(QWidget):
    """16-hour crowd density bar forecast (6 AM to 10 PM)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(85)
        self._forecast = [
            ("6A", 35), ("7A", 68), ("8A", 72), ("9A", 55),
            ("10A", 40), ("11A", 32), ("12P", 58), ("1P", 52),
            ("2P", 28), ("3P", 30), ("4P", 48), ("5P", 82),
            ("6P", 94), ("7P", 88), ("8P", 65), ("9P", 42),
        ]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_dark = ThemeManager.current_theme() == "dark"
        W, H = self.width(), self.height()
        n = len(self._forecast)
        bar_w = max(4.0, (W - (n * 3)) / n)

        current_hr = datetime.now().hour
        current_idx = max(0, min(current_hr - 6, n - 1))

        bar_bottom = H - 20
        max_h = bar_bottom - 8

        for i, (lbl, occ) in enumerate(self._forecast):
            x = i * (bar_w + 3) + 4
            bh = (occ / 100.0) * max_h
            by = bar_bottom - bh

            is_current = (i == current_idx)
            is_peak = (occ >= 75)

            if is_current:
                color = QColor("#FA5A3C")
            elif is_peak:
                color = QColor("#FA5A3C" if is_dark else "#E54829")
            else:
                color = QColor("#282C36" if is_dark else "#D4D4D8")

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(QRectF(x, by, bar_w, bh), 2, 2)

            # Hour label on every 2nd or 3rd bar
            if i % 3 == 0 or is_current:
                painter.setFont(QFont("Inter", 7, QFont.Weight.Bold if is_current else QFont.Weight.Medium))
                painter.setPen(QColor("#FA5A3C" if is_current else ("#9CA3AF" if is_dark else "#8C93A3")))
                painter.drawText(QRectF(x - 6, bar_bottom + 3, bar_w + 12, 14), Qt.AlignmentFlag.AlignCenter, lbl)


class FloorTrafficWidget(QFrame):
    """Full card container for real-time traffic dial & hourly forecast."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("floorTrafficCard")
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 16)
        root.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        hdr_icon = QLabel()
        hdr_icon.setPixmap(get_icon("user_check", color="#FA5A3C", size=18).pixmap(18, 18))
        hdr.addWidget(hdr_icon)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        self.title_lbl = QLabel("Live Floor Traffic")
        self.title_lbl.setStyleSheet("font-size: 13px; font-weight: 800;")
        self.sub_lbl = QLabel("Realtime turnstiles & crowd sensor")
        self.sub_lbl.setStyleSheet("font-size: 10px; color: #8C93A3;")
        title_box.addWidget(self.title_lbl)
        title_box.addWidget(self.sub_lbl)
        hdr.addLayout(title_box)

        hdr.addStretch()

        self.status_badge = QLabel(" Moderate Traffic · Steady ")
        self.status_badge.setStyleSheet("""
            font-size: 10px; font-weight: 700;
            padding: 2px 8px; border-radius: 10px;
            background-color: rgba(245, 158, 11, 0.12);
            color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.3);
        """)
        hdr.addWidget(self.status_badge)
        root.addLayout(hdr)

        # Dial Meter
        self.dial = FloorTrafficDial()
        root.addWidget(self.dial)

        # Hourly Crowd Forecast
        lbl_forecast = QLabel("16-Hour Crowd Forecast (6 AM – 10 PM)")
        lbl_forecast.setStyleSheet("font-size: 10px; font-weight: 700; color: #8C93A3; text-transform: uppercase;")
        root.addWidget(lbl_forecast)

        self.bars = HourlyForecastBars()
        root.addWidget(self.bars)

        self.update_styles()

    def set_live_traffic(self, current_count: int, max_capacity: int = 30):
        pct = int((current_count / max(1, max_capacity)) * 100)
        self.dial.set_occupancy(pct)

        if pct >= 75:
            self.status_badge.setText(" Peak Traffic · Busy ")
            self.status_badge.setStyleSheet("""
                font-size: 10px; font-weight: 700;
                padding: 2px 8px; border-radius: 10px;
                background-color: rgba(250, 90, 60, 0.15);
                color: #FA5A3C; border: 1px solid rgba(250, 90, 60, 0.3);
            """)
        elif pct >= 40:
            self.status_badge.setText(" Moderate Traffic · Steady ")
            self.status_badge.setStyleSheet("""
                font-size: 10px; font-weight: 700;
                padding: 2px 8px; border-radius: 10px;
                background-color: rgba(245, 158, 11, 0.12);
                color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.3);
            """)
        else:
            self.status_badge.setText(" Low Traffic · Open Floor ")
            self.status_badge.setStyleSheet("""
                font-size: 10px; font-weight: 700;
                padding: 2px 8px; border-radius: 10px;
                background-color: rgba(16, 185, 129, 0.12);
                color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3);
            """)

    def update_styles(self):
        is_dark = ThemeManager.current_theme() == "dark"
        card_bg = "#141518" if is_dark else "#FFFFFF"
        border_color = "#24272D" if is_dark else "#E6E9EE"

        self.setStyleSheet(f"""
            QFrame#floorTrafficCard {{
                background-color: {card_bg};
                border: 1px solid {border_color};
                border-radius: 16px;
            }}
        """)
        self.dial.update()
        self.bars.update()
