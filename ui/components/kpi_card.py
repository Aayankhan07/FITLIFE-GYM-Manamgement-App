"""FitLife — KPI Card Component (standalone, also exported by glass_card)"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class KPICard(QFrame):
    """
    Glassmorphism KPI card with icon, title, value, and trend.
    """
    def __init__(self, title: str, value: str, icon: str = "📊",
                 trend: str = "", accent: str = "#7C3AED", parent=None):
        super().__init__(parent)
        self._title = title
        self.setObjectName("kpiCard")
        self.setMinimumWidth(160)
        self.setMinimumHeight(100)
        self.setStyleSheet(f"""
            QFrame#kpiCard {{
                background: rgba(255,255,255,0.06);
                border: 1px solid {accent}55;
                border-radius: 16px;
                border-left: 3px solid {accent};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        # Icon + Title row
        top_row = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 22px;")
        top_row.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 12px; color: #9CA3AF; font-weight: 500;")
        title_lbl.setWordWrap(True)
        top_row.addWidget(title_lbl, 1)
        layout.addLayout(top_row)

        # Value
        self._value_lbl = QLabel(value)
        self._value_lbl.setStyleSheet(
            f"font-size: 26px; font-weight: 900; color: {accent}; letter-spacing: -0.5px;"
        )
        layout.addWidget(self._value_lbl)

        # Trend
        if trend:
            self._trend_lbl = QLabel(trend)
            self._trend_lbl.setStyleSheet("font-size: 11px; color: #6B7280;")
            layout.addWidget(self._trend_lbl)
        else:
            self._trend_lbl = QLabel("")
            layout.addWidget(self._trend_lbl)

    def set_value(self, value: str) -> None:
        self._value_lbl.setText(str(value))

    def set_trend(self, trend: str) -> None:
        self._trend_lbl.setText(trend)
