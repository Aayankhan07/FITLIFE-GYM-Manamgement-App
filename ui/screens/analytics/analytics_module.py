"""FitLife — Analytics Dashboard Module (redesigned charts)"""
import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QComboBox, QPushButton, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont

from ui.components.glass_card import KPICard, SectionHeader
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
import services.analytics_service as analytics_svc
import services.branch_service as branch_svc
from config.constants import ROLE_ADMIN

# Try matplotlib; fall back to inline bar chart if unavailable
try:
    import matplotlib
    matplotlib.use('QtAgg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


# ── Fallback inline bar chart ─────────────────────────────────────────────────
class _FallbackBarChart(QFrame):
    """Simple vertical bar chart — no external lib needed."""

    def __init__(self, title: str, data: list, accent="#0066FF",
                 value_prefix="", parent=None):
        super().__init__(parent)
        self._title = title
        self._data = data
        self._accent = QColor(accent)
        self._prefix = value_prefix
        self.setMinimumHeight(200)
        self.setStyleSheet(
            "background:rgba(13,17,23,0.8);border:1px solid rgba(0, 102, 255, 0.2);"
            "border-radius:14px;"
        )

    def set_data(self, data: list):
        self._data = data
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        pad_l, pad_r, pad_t, pad_b = 40, 16, 36, 40

        # Title
        p.setPen(QColor("#E6EDF3"))
        f = QFont(); f.setPointSize(10); f.setBold(True); p.setFont(f)
        p.drawText(pad_l, 22, self._title)

        chart_w = W - pad_l - pad_r
        chart_h = H - pad_t - pad_b
        n = len(self._data)
        if n == 0:
            p.end()
            return
        max_val = max((v for _, v in self._data), default=1) or 1
        bar_w = max(8, chart_w // n - 8)
        spacing = (chart_w - bar_w * n) // (n + 1)

        # Grid lines
        for gi in range(4):
            gy = pad_t + int(chart_h * gi / 3)
            p.setPen(QPen(QColor("#21262D"), 1, Qt.PenStyle.DashLine))
            p.drawLine(pad_l, gy, W - pad_r, gy)

        # Bars
        for i, (label, val) in enumerate(self._data):
            x = pad_l + spacing + i * (bar_w + spacing)
            bar_h = int((val / max_val) * chart_h) if max_val else 0
            y = pad_t + chart_h - bar_h

            # Bar shadow
            p.setPen(Qt.PenStyle.NoPen)
            shadow_col = QColor(self._accent); shadow_col.setAlpha(30)
            p.setBrush(QBrush(shadow_col))
            p.drawRoundedRect(x + 2, y + 4, bar_w, bar_h, 4, 4)

            # Bar fill
            bar_col = QColor(self._accent); bar_col.setAlpha(220)
            p.setBrush(QBrush(bar_col))
            p.drawRoundedRect(x, y, bar_w, bar_h, 4, 4)

            # Value label on top
            p.setPen(QColor("#E6EDF3"))
            f2 = QFont(); f2.setPointSize(8); f2.setBold(True); p.setFont(f2)
            val_str = f"{self._prefix}{val:,.0f}" if isinstance(val, float) else f"{self._prefix}{val}"
            p.drawText(x - 10, y - 4, bar_w + 20, 16, Qt.AlignmentFlag.AlignCenter, val_str)

            # X-axis label
            p.setPen(QColor("#9CA3AF"))
            f3 = QFont(); f3.setPointSize(8); p.setFont(f3)
            short = label[:8] if len(label) > 8 else label
            p.drawText(x - 10, pad_t + chart_h + 6, bar_w + 20, 24,
                       Qt.AlignmentFlag.AlignCenter, short)

        # X-axis line
        p.setPen(QPen(QColor("#374151"), 1))
        p.drawLine(pad_l, pad_t + chart_h, W - pad_r, pad_t + chart_h)
        p.end()


# ── Matplotlib chart helpers ──────────────────────────────────────────────────
def _apply_chart_theme(fig, axes):
    """Apply dark FitLife theme to a matplotlib figure and axes list."""
    fig.patch.set_facecolor('#0D1117')
    for ax in axes:
        ax.set_facecolor('#0D1117')
        ax.tick_params(colors='#9CA3AF', labelsize=9)
        ax.xaxis.label.set_color('#9CA3AF')
        ax.yaxis.label.set_color('#9CA3AF')
        ax.title.set_color('#E6EDF3')
        ax.title.set_fontsize(12)
        ax.title.set_fontweight('bold')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#21262D')
        ax.spines['bottom'].set_color('#21262D')
        ax.yaxis.grid(True, color='#21262D', linestyle='--', alpha=0.5)
        ax.xaxis.grid(False)
        ax.set_axisbelow(True)


def _make_vertical_bar_chart(title, data, color='#0066FF', prefix=''):
    """Create a dark-themed vertical bar chart."""
    fig = Figure(figsize=(4, 3), dpi=96)
    ax = fig.add_subplot(111)
    _apply_chart_theme(fig, [ax])

    if not data:
        ax.set_title(title)
        return fig

    labels = [d[0] for d in data]
    values = [float(d[1]) for d in data]
    x = range(len(labels))

    bars = ax.bar(x, values, color=color, alpha=0.88, width=0.55,
                  edgecolor=_lighten(color), linewidth=0.8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=8)
    ax.set_title(title, pad=10)

    max_val = max(values) if values else 1
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            lbl = f"{prefix}{h:,.0f}" if '.' in f"{h}" else f"{prefix}{int(h):,}"
            ax.text(bar.get_x() + bar.get_width() / 2,
                    h + max_val * 0.01,
                    lbl, ha='center', va='bottom',
                    color='#E6EDF3', fontsize=8, fontweight='bold')

    fig.tight_layout(pad=1.2)
    return fig


def _make_line_chart(title, data, color='#00F5FF'):
    """Create an area line chart."""
    fig = Figure(figsize=(4, 3), dpi=96)
    ax = fig.add_subplot(111)
    _apply_chart_theme(fig, [ax])

    if not data:
        ax.set_title(title)
        return fig

    labels = [d[0] for d in data]
    values = [float(d[1]) for d in data]
    x = range(len(labels))

    ax.plot(list(x), values, color=color, linewidth=2.5, zorder=5)
    ax.fill_between(list(x), values, alpha=0.15, color=color)
    ax.scatter(list(x), values, color=color, s=40, zorder=6)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=8)
    ax.set_title(title, pad=10)
    fig.tight_layout(pad=1.2)
    return fig


def _make_donut_chart(title, data, colors=None):
    """Create a donut pie chart."""
    fig = Figure(figsize=(3.5, 3), dpi=96)
    ax = fig.add_subplot(111)
    fig.patch.set_facecolor('#0D1117')
    ax.set_facecolor('#0D1117')
    ax.set_title(title, color='#E6EDF3', fontsize=12, fontweight='bold', pad=10)

    if not data:
        return fig

    labels = [str(d[0]) for d in data]
    values = [float(d[1]) for d in data]
    default_colors = ['#00E676', '#FFB800', '#FF2D78', '#6B7280', '#0066FF', '#00F5FF']
    clrs = colors if colors else default_colors[:len(values)]

    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=clrs,
        autopct='%1.0f%%', startangle=90,
        wedgeprops={'width': 0.55, 'edgecolor': '#0D1117', 'linewidth': 2},
        textprops={'color': '#9CA3AF', 'fontsize': 8}
    )
    for at in autotexts:
        at.set_color('#E6EDF3')
        at.set_fontsize(8)
        at.set_fontweight('bold')

    fig.tight_layout(pad=1.0)
    return fig


def _lighten(hex_color: str) -> str:
    """Return a slightly lighter version of a hex color."""
    try:
        h = hex_color.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r = min(255, r + 40)
        g = min(255, g + 40)
        b = min(255, b + 40)
        return f"#{r:02X}{g:02X}{b:02X}"
    except Exception:
        return hex_color


def _make_chart_widget(fig):
    """Wrap matplotlib figure in a glass-styled QFrame."""
    canvas = FigureCanvas(fig)
    canvas.setStyleSheet("background: transparent;")
    frame = QFrame()
    frame.setStyleSheet(
        "QFrame{background:rgba(13,17,23,0.8);"
        "border:1px solid rgba(0, 102, 255, 0.2);border-radius:14px;}"
    )
    frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    frame.setMinimumHeight(280)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(8, 8, 8, 8)
    lay.addWidget(canvas)
    plt.close(fig)
    return frame


# ── Analytics Dashboard ───────────────────────────────────────────────────────
class AnalyticsDashboard(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self._branch_id = session.branch_id
        self.setStyleSheet("background:transparent;")
        self._build_ui()
        self._load()

    def _build_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QWidget { border:none;background:transparent; }")
        c = QWidget(); c.setStyleSheet("background:transparent;")
        m = QVBoxLayout(c); m.setContentsMargins(28, 24, 28, 28); m.setSpacing(20)

        # Header + filter
        hdr = QHBoxLayout()
        t = QLabel("📊  Analytics Dashboard")
        t.setStyleSheet("QWidget { font-size:26px;font-weight:900;color:#F0F4FF; }")
        hdr.addWidget(t); hdr.addStretch()
        if self._session.role == ROLE_ADMIN:
            hdr.addWidget(QLabel("Branch:"))
            self._bf = QComboBox(); self._bf.setFixedHeight(36)
            self._bf.addItem("All Branches", None)
            for bid, bn in branch_svc.get_all_branches_dropdown():
                self._bf.addItem(bn, bid)
            self._bf.currentIndexChanged.connect(self._load); hdr.addWidget(self._bf)
        else:
            self._bf = None
        rb = QPushButton("🔄 Refresh"); rb.setObjectName("btnSecondary"); rb.setFixedHeight(36)
        rb.clicked.connect(self._load); hdr.addWidget(rb)
        m.addLayout(hdr)

        # KPI row 1
        kr1 = QHBoxLayout(); kr1.setSpacing(14)
        self._k_mem   = KPICard("Total Members",    "—", "👥", "", "#0066FF")
        self._k_act   = KPICard("Active Members",   "—", "✅", "", "#00E676")
        self._k_rev   = KPICard("Monthly Revenue",  "—", "💰", "", "#00F5FF")
        self._k_att   = KPICard("Attendance Today", "—", "📅", "", "#FFB800")
        for k in [self._k_mem, self._k_act, self._k_rev, self._k_att]:
            kr1.addWidget(k)
        m.addLayout(kr1)

        # KPI row 2
        kr2 = QHBoxLayout(); kr2.setSpacing(14)
        self._k_tr    = KPICard("Active Trainers",  "—", "💪", "", "#0066FF")
        self._k_exp   = KPICard("Expiring (7d)",    "—", "⚠️", "", "#FF2D78")
        self._k_ppay  = KPICard("Pending Payments", "—", "📄", "", "#FFB800")
        self._k_pamt  = KPICard("Pending Amount",   "—", "💸", "", "#FF2D78")
        for k in [self._k_tr, self._k_exp, self._k_ppay, self._k_pamt]:
            kr2.addWidget(k)
        m.addLayout(kr2)

        m.addWidget(SectionHeader("📈  Performance Charts"))

        # Charts grid — 2 columns
        self._charts_grid = QGridLayout()
        self._charts_grid.setSpacing(16)
        m.addLayout(self._charts_grid)

        # Chart placeholder frames
        self._chart_rev_frame   = self._placeholder_frame("Monthly Revenue")
        self._chart_grow_frame  = self._placeholder_frame("Member Growth")
        self._chart_att_frame   = self._placeholder_frame("Daily Attendance")
        self._chart_goal_frame  = self._placeholder_frame("Member Goals")
        self._charts_grid.addWidget(self._chart_rev_frame,  0, 0)
        self._charts_grid.addWidget(self._chart_grow_frame, 0, 1)
        self._charts_grid.addWidget(self._chart_att_frame,  1, 0)
        self._charts_grid.addWidget(self._chart_goal_frame, 1, 1)

        # Trainer leaderboard
        m.addWidget(SectionHeader("🏆  Top Trainers"))
        tf = QFrame()
        tf.setStyleSheet("QWidget { background:rgba(255,255,255,0.04);border:1px solid rgba(0, 102, 255, 0.2);border-radius:14px; }")
        tl = QVBoxLayout(tf); tl.setContentsMargins(16, 14, 16, 14); tl.setSpacing(8)
        self._trainer_rows = QVBoxLayout(); self._trainer_rows.setSpacing(6)
        tl.addLayout(self._trainer_rows)
        m.addWidget(tf)

        m.addStretch()
        self._overlay = LoadingOverlay(self)
        scroll.setWidget(c)
        QVBoxLayout(self).addWidget(scroll)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def _placeholder_frame(self, title):
        f = QFrame()
        f.setStyleSheet(
            "QFrame{background:rgba(13,17,23,0.8);"
            "border:1px solid rgba(0, 102, 255, 0.2);border-radius:14px;}"
        )
        f.setMinimumHeight(280)
        lbl = QLabel(f"⏳ Loading {title}...")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("QWidget { color:#6B7280;font-size:14px; }")
        QVBoxLayout(f).addWidget(lbl)
        return f

    def _load(self):
        self._overlay.show_loading("Crunching numbers...")
        bid = self._bf.currentData() if self._bf else self._branch_id
        self._w = Worker(self._fetch_all, bid)
        self._w.result.connect(self._on_data)
        self._w.error.connect(lambda e: self._overlay.hide_loading())
        self._w.start()

    def _fetch_all(self, bid):
        return {
            "kpis":     analytics_svc.get_dashboard_kpis(bid),
            "rev":      analytics_svc.get_monthly_revenue(bid, 6),
            "growth":   analytics_svc.get_member_growth(bid, 6),
            "att":      analytics_svc.get_attendance_by_day(bid, 14),
            "goals":    analytics_svc.get_goal_distribution(bid),
            "trainers": analytics_svc.get_top_trainers(bid, 5),
        }

    def _replace_chart(self, old_frame, new_frame, row, col):
        """Swap old placeholder/chart frame with new one in the grid."""
        self._charts_grid.removeWidget(old_frame)
        old_frame.hide()
        old_frame.deleteLater()
        self._charts_grid.addWidget(new_frame, row, col)
        return new_frame

    def _on_data(self, d):
        self._overlay.hide_loading()
        k = d["kpis"]
        self._k_mem.set_value(str(k["total_members"]))
        self._k_act.set_value(str(k["active_members"]))
        self._k_rev.set_value(f"Rs. {k['monthly_revenue']:,.0f}")
        self._k_att.set_value(str(k["today_attendance"]))
        self._k_tr.set_value(str(k["active_trainers"]))
        self._k_exp.set_value(str(k["expiring_soon"]))
        self._k_ppay.set_value(str(k["pending_payments"]))
        self._k_pamt.set_value(f"Rs. {k['pending_amount']:,.0f}")

        if HAS_MATPLOTLIB:
            # Revenue — vertical bar
            fig_rev = _make_vertical_bar_chart("Monthly Revenue", d["rev"],
                                               color='#0066FF', prefix='Rs.')
            self._chart_rev_frame = self._replace_chart(
                self._chart_rev_frame, _make_chart_widget(fig_rev), 0, 0)

            # Member growth — line chart
            fig_grow = _make_line_chart("Member Growth", d["growth"], color='#00F5FF')
            self._chart_grow_frame = self._replace_chart(
                self._chart_grow_frame, _make_chart_widget(fig_grow), 0, 1)

            # Attendance — line chart
            fig_att = _make_line_chart("Daily Attendance (Last 14 Days)",
                                       d["att"], color='#00E676')
            self._chart_att_frame = self._replace_chart(
                self._chart_att_frame, _make_chart_widget(fig_att), 1, 0)

            # Goals — donut
            if d["goals"]:
                fig_goal = _make_donut_chart("Member Goals", d["goals"])
                self._chart_goal_frame = self._replace_chart(
                    self._chart_goal_frame, _make_chart_widget(fig_goal), 1, 1)
            else:
                fig_goal = _make_vertical_bar_chart("Member Goals", d["goals"], '#FFB800')
                self._chart_goal_frame = self._replace_chart(
                    self._chart_goal_frame, _make_chart_widget(fig_goal), 1, 1)
        else:
            # Fallback inline charts
            rev_w = _FallbackBarChart("Monthly Revenue (Rs.)", d["rev"], "#0066FF", "Rs.")
            self._chart_rev_frame = self._replace_chart(self._chart_rev_frame, rev_w, 0, 0)
            grow_w = _FallbackBarChart("Member Growth", d["growth"], "#00F5FF")
            self._chart_grow_frame = self._replace_chart(self._chart_grow_frame, grow_w, 0, 1)
            att_w = _FallbackBarChart("Daily Attendance", d["att"], "#00E676")
            self._chart_att_frame = self._replace_chart(self._chart_att_frame, att_w, 1, 0)
            goal_w = _FallbackBarChart("Member Goals", d["goals"], "#FFB800")
            self._chart_goal_frame = self._replace_chart(self._chart_goal_frame, goal_w, 1, 1)

        # Trainer cards
        while self._trainer_rows.count():
            w = self._trainer_rows.takeAt(0).widget()
            if w:
                w.deleteLater()
        for i, t in enumerate(d["trainers"]):
            row = QFrame()
            row.setStyleSheet(
                "background:rgba(0, 102, 255, 0.08);"
                "border:1px solid rgba(0, 102, 255, 0.15);border-radius:10px;"
            )
            rl = QHBoxLayout(row); rl.setContentsMargins(14, 10, 14, 10)
            num = QLabel(f"#{i+1}")
            num.setStyleSheet("QWidget { font-size:16px;font-weight:900;color:#0066FF;min-width:28px; }")
            rl.addWidget(num)
            info = QVBoxLayout(); info.setSpacing(2)
            info.addWidget(_lbl(str(t[0]), "color:#F0F4FF;font-weight:bold;font-size:13px;"))
            info.addWidget(_lbl(str(t[1]), "color:#9CA3AF;font-size: 13px;"))
            rl.addLayout(info); rl.addStretch()
            rl.addWidget(_lbl(f"👥 {t[2]} members", "color:#00E676;font-size: 13px;"))
            rl.addWidget(_lbl(f"⭐ {float(t[3]):.1f}", "color:#FFB800;font-size: 13px;"))
            self._trainer_rows.addWidget(row)

    def refresh(self):
        self._load()


def _lbl(text, style=""):
    la = QLabel(text); la.setStyleSheet(style); return la
