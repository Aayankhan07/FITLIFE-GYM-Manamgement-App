"""
FitLife — Performance Trends Chart Widget (Custom QPainter)
Matches GYM-MANAGEMENT Bezier multi-series graph with interactive timeframe pills,
series checkboxes (Coral Check-ins + Blue Gross Rev), and hover tooltips.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QLinearGradient, QPainterPath, QFont
)
from ui.theme.theme_manager import ThemeManager


class PerformanceChartCanvas(QWidget):
    """Custom drawing canvas for anti-aliased smooth bezier trends."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumHeight(220)
        self._timeframe = "30D"
        self._show_checkins = True
        self._show_revenue = True
        self._hover_idx = -1

        # Dataset for each timeframe matching DashboardModule.tsx
        self._datasets = {
            "7D": {
                "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "checkins": [92, 124, 108, 145, 168, 195, 130],
                "revenue": [480, 620, 540, 780, 920, 1120, 710],
                "changes": ["+6.2%", "+9.4%", "+4.1%", "+12.5%", "+18.0%", "+22.4%", "+8.3%"],
            },
            "30D": {
                "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                "checkins": [840, 980, 1220, 1480],
                "revenue": [3850, 4420, 5890, 6950],
                "changes": ["+8.2%", "+11.5%", "+19.4%", "+24.1%"],
            },
            "90D": {
                "labels": ["January", "February", "March"],
                "checkins": [3450, 4120, 5280],
                "revenue": [16200, 19850, 24900],
                "changes": ["+14.0%", "+18.2%", "+27.6%"],
            },
            "YTD": {
                "labels": ["Q1", "Q2", "Q3", "Q4"],
                "checkins": [9800, 12400, 15100, 18900],
                "revenue": [48500, 59200, 72400, 89600],
                "changes": ["+15.2%", "+21.0%", "+26.8%", "+33.4%"],
            },
        }

    def set_timeframe(self, tf: str):
        if tf in self._datasets:
            self._timeframe = tf
            self._hover_idx = len(self._datasets[tf]["labels"]) - 1
            self.update()

    def set_series_visibility(self, checkins: bool, revenue: bool):
        self._show_checkins = checkins
        self._show_revenue = revenue
        self.update()

    def mouseMoveEvent(self, event):
        data = self._datasets[self._timeframe]
        n = len(data["labels"])
        W = self.width()
        margin_x = 50
        usable_w = W - 2 * margin_x

        step = usable_w / max(1, n - 1)
        x_mouse = event.pos().x()

        closest_idx = 0
        min_dist = 99999
        for i in range(n):
            px = margin_x + i * step
            dist = abs(px - x_mouse)
            if dist < min_dist:
                min_dist = dist
                closest_idx = i

        if self._hover_idx != closest_idx:
            self._hover_idx = closest_idx
            self.update()

    def leaveEvent(self, event):
        self._hover_idx = -1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_dark = ThemeManager.current_theme() == "dark"
        W, H = self.width(), self.height()

        grid_color = QColor("#22252C") if is_dark else QColor("#F0F2F5")
        text_color = QColor("#9CA3AF") if is_dark else QColor("#6B7280")
        base_line_color = QColor("#2B2F38") if is_dark else QColor("#E2E6ED")

        # Top and bottom padding
        pad_top = 25
        pad_bottom = 35
        margin_x = 50
        usable_h = H - pad_top - pad_bottom
        usable_w = W - 2 * margin_x

        # Horizontal subtle dashed gridlines
        pen_grid = QPen(grid_color, 1, Qt.PenStyle.DashLine)
        painter.setPen(pen_grid)
        for frac in [0.25, 0.5, 0.75]:
            y_grid = int(pad_top + frac * usable_h)
            painter.drawLine(margin_x, y_grid, W - margin_x, y_grid)

        # Baseline
        painter.setPen(QPen(base_line_color, 1, Qt.PenStyle.SolidLine))
        painter.drawLine(margin_x, H - pad_bottom, W - margin_x, H - pad_bottom)

        data = self._datasets[self._timeframe]
        labels = data["labels"]
        checkins = data["checkins"]
        revenues = data["revenue"]
        n = len(labels)
        step = usable_w / max(1, n - 1)

        # Draw X-axis labels
        painter.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        painter.setPen(text_color)
        for i, lbl in enumerate(labels):
            px = int(margin_x + i * step)
            rect = QRectF(px - 40, H - pad_bottom + 6, 80, 20)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, lbl.upper())

        max_c = max(checkins) * 1.15 if max(checkins) > 0 else 1
        max_r = max(revenues) * 1.15 if max(revenues) > 0 else 1

        c_points = []
        r_points = []
        for i in range(n):
            px = margin_x + i * step
            # Higher value = lower Y
            cy = pad_top + (1.0 - (checkins[i] / max_c)) * usable_h
            ry = pad_top + (1.0 - (revenues[i] / max_r)) * usable_h
            c_points.append(QPointF(px, cy))
            r_points.append(QPointF(px, ry))

        def make_smooth_path(pts):
            path = QPainterPath()
            if not pts:
                return path
            path.moveTo(pts[0])
            for i in range(len(pts) - 1):
                p0 = pts[max(0, i - 1)]
                p1 = pts[i]
                p2 = pts[i + 1]
                p3 = pts[min(len(pts) - 1, i + 2)]
                cp1 = QPointF(p1.x() + (p2.x() - p0.x()) / 5.0, p1.y() + (p2.y() - p0.y()) / 5.0)
                cp2 = QPointF(p2.x() - (p3.x() - p1.x()) / 5.0, p2.y() - (p3.y() - p1.y()) / 5.0)
                path.cubicTo(cp1, cp2, p2)
            return path

        # ── 1. Draw Check-Ins (Coral #FA5A3C) ──────────────────────────────────
        if self._show_checkins and len(c_points) > 1:
            c_path = make_smooth_path(c_points)
            fill_path = QPainterPath(c_path)
            fill_path.lineTo(c_points[-1].x(), H - pad_bottom)
            fill_path.lineTo(c_points[0].x(), H - pad_bottom)
            fill_path.closeSubpath()

            grad_c = QLinearGradient(0, pad_top, 0, H - pad_bottom)
            grad_c.setColorAt(0.0, QColor(250, 90, 60, 65))
            grad_c.setColorAt(1.0, QColor(250, 90, 60, 0))
            painter.fillPath(fill_path, QBrush(grad_c))

            pen_c = QPen(QColor("#FA5A3C"), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.strokePath(c_path, pen_c)

        # ── 2. Draw Gross Revenue (Blue #3B82F6) ───────────────────────────────
        if self._show_revenue and len(r_points) > 1:
            r_path = make_smooth_path(r_points)
            fill_r_path = QPainterPath(r_path)
            fill_r_path.lineTo(r_points[-1].x(), H - pad_bottom)
            fill_r_path.lineTo(r_points[0].x(), H - pad_bottom)
            fill_r_path.closeSubpath()

            grad_r = QLinearGradient(0, pad_top, 0, H - pad_bottom)
            grad_r.setColorAt(0.0, QColor(59, 130, 246, 50))
            grad_r.setColorAt(1.0, QColor(59, 130, 246, 0))
            painter.fillPath(fill_r_path, QBrush(grad_r))

            pen_r = QPen(QColor("#3B82F6"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.strokePath(r_path, pen_r)

        # ── 3. Hover Markers and Tooltip ──────────────────────────────────────
        active_idx = self._hover_idx if self._hover_idx >= 0 else len(labels) - 1
        if 0 <= active_idx < n:
            pt_c = c_points[active_idx]
            pt_r = r_points[active_idx]

            # Vertical guide line
            painter.setPen(QPen(QColor(156, 163, 175, 80), 1, Qt.PenStyle.DashLine))
            painter.drawLine(int(pt_c.x()), pad_top, int(pt_c.x()), H - pad_bottom)

            # Node circles
            if self._show_checkins:
                painter.setPen(QPen(QColor("#FFFFFF"), 2))
                painter.setBrush(QBrush(QColor("#FA5A3C")))
                painter.drawEllipse(pt_c, 5, 5)

            if self._show_revenue:
                painter.setPen(QPen(QColor("#FFFFFF"), 2))
                painter.setBrush(QBrush(QColor("#3B82F6")))
                painter.drawEllipse(pt_r, 4.5, 4.5)

            # Floating Tooltip Pill
            tt_w, tt_h = 160, 68
            tt_x = pt_c.x() - tt_w / 2
            tt_x = max(10, min(W - tt_w - 10, tt_x))
            tt_y = 12

            tt_rect = QRectF(tt_x, tt_y, tt_w, tt_h)
            tt_bg = QColor("#1A1D23") if is_dark else QColor("#FFFFFF")
            tt_border = QColor("#2B2F38") if is_dark else QColor("#E2E6ED")

            painter.setPen(QPen(tt_border, 1))
            painter.setBrush(QBrush(tt_bg))
            painter.drawRoundedRect(tt_rect, 10, 10)

            # Tooltip Text Content
            painter.setFont(QFont("Inter", 8, QFont.Weight.Bold))
            painter.setPen(QColor("#9CA3AF") if is_dark else QColor("#6B7280"))
            painter.drawText(QRectF(tt_x + 10, tt_y + 8, 80, 16), Qt.AlignmentFlag.AlignLeft, labels[active_idx])

            painter.setPen(QColor("#10B981"))
            painter.drawText(QRectF(tt_x + tt_w - 60, tt_y + 8, 50, 16), Qt.AlignmentFlag.AlignRight, data["changes"][active_idx])

            # Coral series value
            y_offset = tt_y + 26
            if self._show_checkins:
                painter.setPen(QPen(Qt.PenStyle.NoPen))
                painter.setBrush(QBrush(QColor("#FA5A3C")))
                painter.drawEllipse(QPointF(tt_x + 14, y_offset + 7), 3, 3)

                painter.setFont(QFont("Inter", 8, QFont.Weight.Medium))
                painter.setPen(QColor("#F4F5F8") if is_dark else QColor("#18181B"))
                painter.drawText(QRectF(tt_x + 22, y_offset, 70, 16), Qt.AlignmentFlag.AlignLeft, "Check-Ins")

                painter.setFont(QFont("Inter", 8, QFont.Weight.Bold))
                painter.setPen(QColor("#FA5A3C"))
                painter.drawText(QRectF(tt_x + tt_w - 60, y_offset, 50, 16), Qt.AlignmentFlag.AlignRight, str(checkins[active_idx]))
                y_offset += 18

            # Blue series value
            if self._show_revenue:
                painter.setPen(QPen(Qt.PenStyle.NoPen))
                painter.setBrush(QBrush(QColor("#3B82F6")))
                painter.drawEllipse(QPointF(tt_x + 14, y_offset + 7), 3, 3)

                painter.setFont(QFont("Inter", 8, QFont.Weight.Medium))
                painter.setPen(QColor("#F4F5F8") if is_dark else QColor("#18181B"))
                painter.drawText(QRectF(tt_x + 22, y_offset, 70, 16), Qt.AlignmentFlag.AlignLeft, "Gross Rev")

                painter.setFont(QFont("Inter", 8, QFont.Weight.Bold))
                painter.setPen(QColor("#3B82F6"))
                painter.drawText(QRectF(tt_x + tt_w - 60, y_offset, 50, 16), Qt.AlignmentFlag.AlignRight, f"${revenues[active_idx]:,}")


class PerformanceChartWidget(QFrame):
    """Container card with title, series toggle buttons, and timeframe segmented controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("performanceChartCard")
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(14)

        # Header Bar
        header = QHBoxLayout()
        header.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_title = QLabel("Facility Performance & Check-In Velocity")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: 800;")
        lbl_sub = QLabel("Multi-Series Telemetry Analysis")
        lbl_sub.setStyleSheet("font-size: 11px; font-weight: 500; color: #8C93A3;")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)
        header.addLayout(title_box)

        header.addStretch()

        # Series Toggles (Checkins Coral / Revenue Blue)
        self.checkins_toggle = QPushButton(" ● Check-ins ")
        self.checkins_toggle.setObjectName("chartSeriesToggle")
        self.checkins_toggle.setCheckable(True)
        self.checkins_toggle.setChecked(True)
        self.checkins_toggle.setFixedHeight(28)
        self.checkins_toggle.setCursor(Qt.CursorShape.PointingHandCursor)

        self.rev_toggle = QPushButton(" ● Revenue ")
        self.rev_toggle.setObjectName("chartSeriesToggle")
        self.rev_toggle.setCheckable(True)
        self.rev_toggle.setChecked(True)
        self.rev_toggle.setFixedHeight(28)
        self.rev_toggle.setCursor(Qt.CursorShape.PointingHandCursor)

        self.checkins_toggle.clicked.connect(self._on_series_toggled)
        self.rev_toggle.clicked.connect(self._on_series_toggled)

        header.addWidget(self.checkins_toggle)
        header.addWidget(self.rev_toggle)

        # Timeframe Pills
        self.tf_box = QFrame()
        self.tf_box.setObjectName("chartTfBox")
        self.tf_box.setFixedHeight(32)
        tf_layout = QHBoxLayout(self.tf_box)
        tf_layout.setContentsMargins(3, 3, 3, 3)
        tf_layout.setSpacing(2)

        self.tf_buttons = {}
        for tf in ["7D", "30D", "90D", "YTD"]:
            btn = QPushButton(tf)
            btn.setObjectName("chartTfBtn")
            btn.setFixedSize(38, 24)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, t=tf: self._set_timeframe(t))
            tf_layout.addWidget(btn)
            self.tf_buttons[tf] = btn

        header.addWidget(self.tf_box)
        root.addLayout(header)

        # Custom Canvas
        self.canvas = PerformanceChartCanvas()
        root.addWidget(self.canvas)

        self.update_styles()
        self._set_timeframe("30D")

    def _set_timeframe(self, tf: str):
        self._active_tf = tf
        self.canvas.set_timeframe(tf)
        self._update_tf_styles()

    def _on_series_toggled(self):
        self.canvas.set_series_visibility(
            self.checkins_toggle.isChecked(),
            self.rev_toggle.isChecked()
        )
        self._update_series_styles()

    def update_styles(self):
        is_dark = ThemeManager.current_theme() == "dark"
        card_bg = "#141518" if is_dark else "#FFFFFF"
        border_color = "#24272D" if is_dark else "#E6E9EE"
        tf_bg = "#1E2129" if is_dark else "#EEF0F4"

        self.setStyleSheet(f"""
            QFrame#performanceChartCard {{
                background-color: {card_bg};
                border: 1px solid {border_color};
                border-radius: 16px;
            }}
        """)

        self.tf_box.setStyleSheet(f"""
            QFrame#chartTfBox {{
                background-color: {tf_bg};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)

        self._update_series_styles()
        self._update_tf_styles()
        self.canvas.update()

    def _update_series_styles(self):
        is_dark = ThemeManager.current_theme() == "dark"
        c_active = self.checkins_toggle.isChecked()
        r_active = self.rev_toggle.isChecked()

        c_bg = ("#2A1715" if is_dark else "#FEECE8") if c_active else "transparent"
        c_border = "#FA5A3C" if c_active else ("#2B2F38" if is_dark else "#E2E6ED")
        c_color = "#FA5A3C" if c_active else ("#9CA3AF" if is_dark else "#6B7280")

        self.checkins_toggle.setStyleSheet(f"""
            QPushButton#chartSeriesToggle {{
                background-color: {c_bg};
                border: 1px solid {c_border};
                border-radius: 8px;
                color: {c_color};
                font-size: 11px;
                font-weight: 700;
                padding: 4px 10px;
                min-height: 20px;
            }}
            QPushButton#chartSeriesToggle:hover {{
                border-color: #FA5A3C;
            }}
        """)

        r_bg = ("#15233D" if is_dark else "#EFF6FF") if r_active else "transparent"
        r_border = "#3B82F6" if r_active else ("#2B2F38" if is_dark else "#E2E6ED")
        r_color = "#3B82F6" if r_active else ("#9CA3AF" if is_dark else "#6B7280")

        self.rev_toggle.setStyleSheet(f"""
            QPushButton#chartSeriesToggle {{
                background-color: {r_bg};
                border: 1px solid {r_border};
                border-radius: 8px;
                color: {r_color};
                font-size: 11px;
                font-weight: 700;
                padding: 4px 10px;
                min-height: 20px;
            }}
            QPushButton#chartSeriesToggle:hover {{
                border-color: #3B82F6;
            }}
        """)

    def _update_tf_styles(self):
        is_dark = ThemeManager.current_theme() == "dark"
        for tf, btn in self.tf_buttons.items():
            is_active = (tf == getattr(self, '_active_tf', '30D'))
            if is_active:
                btn.setStyleSheet(f"""
                    QPushButton#chartTfBtn {{
                        background-color: {"#282C36" if is_dark else "#FFFFFF"};
                        border: {"1px solid #353B47" if is_dark else "1px solid #D5D9E0"};
                        border-radius: 6px;
                        color: {"#FFFFFF" if is_dark else "#18181B"};
                        font-size: 11px;
                        font-weight: 800;
                        padding: 0px;
                        margin: 0px;
                        min-height: 20px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton#chartTfBtn {{
                        background-color: transparent;
                        border: none;
                        border-radius: 6px;
                        color: {"#9CA3AF" if is_dark else "#64748B"};
                        font-size: 11px;
                        font-weight: 600;
                        padding: 0px;
                        margin: 0px;
                        min-height: 20px;
                    }}
                    QPushButton#chartTfBtn:hover {{
                        background-color: {"rgba(255,255,255,0.06)" if is_dark else "rgba(0,0,0,0.05)"};
                        color: {"#FFFFFF" if is_dark else "#0F172A"};
                    }}
                """)
