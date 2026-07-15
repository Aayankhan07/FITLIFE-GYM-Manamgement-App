"""FitLife — Smart Ask Module (Phase 6)
Rule-based gym assistant + DB query responses. No external API required.
Falls back to graceful "I don't know" for unsupported questions.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from utils.thread_worker import Worker
from database.connection import DatabaseConnection
from config.constants import ROLE_ADMIN, ROLE_MANAGER
import logging, re
from datetime import date

logger = logging.getLogger(__name__)


# ── Smart Engine ──────────────────────────────────────────────────────────────
class SmartEngine:
    """Rule-based Q&A engine that queries the FitLife DB for answers."""

    def __init__(self, session):
        self._session = session
        self._bid = session.branch_id

    def answer(self, question: str) -> str:
        q = question.lower().strip()
        try:
            if self._matches(q, ["how many member", "total member", "member count"]):
                return self._member_count()
            if self._matches(q, ["active member"]):
                return self._member_count(status="Active")
            if self._matches(q, ["expir", "membership expir", "renew"]):
                return self._expiring()
            if self._matches(q, ["today attendance", "who came today", "attendance today", "present today"]):
                return self._attendance_today()
            if self._matches(q, ["revenue", "income", "earning", "this month"]):
                return self._monthly_revenue()
            if self._matches(q, ["pending payment", "unpaid", "overdue"]):
                return self._pending_payments()
            if self._matches(q, ["trainer", "how many trainer", "trainer count"]):
                return self._trainer_count()
            if self._matches(q, ["equipment", "how many equipment", "equipment count"]):
                return self._equipment_count()
            if self._matches(q, ["maintenance", "service due"]):
                return self._maintenance_due()
            if self._matches(q, ["top trainer", "best trainer"]):
                return self._top_trainer()
            if self._matches(q, ["salary", "unpaid salary", "pending salary"]):
                return self._salary_status()
            if self._matches(q, ["goal", "fitness goal", "popular goal"]):
                return self._popular_goal()
            if self._matches(q, ["help", "what can you", "commands"]):
                return self._help()
            import services.ai_service as ai
            res = ai.ask_question(question, self._session.role, self._session.user_id)
            return res.get("answer", "🤖  I'm not sure how to answer that yet.")
        except Exception as e:
            logger.error(f"SmartEngine error: {e}")
            return f"⚠️  Query error: {e}"

    def _matches(self, q, keywords):
        return any(k in q for k in keywords)

    def _q(self, sql, params=()):
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params); return cursor.fetchone()

    def _b_filter(self, alias="m"):
        if self._bid:
            return f" AND {alias}.branch_id=?", (self._bid,)
        return "", ()

    def _member_count(self, status=None):
        bf, bp = self._b_filter("m")
        sql = f"SELECT COUNT(*) FROM members m WHERE 1=1 {bf}"
        p = list(bp)
        if status: sql += " AND m.status=?"; p.append(status)
        row = self._q(sql, p)
        tag = f"({status})" if status else "(all)"
        return f"👥  Members {tag}: **{row[0]}**"

    def _expiring(self):
        bf, bp = self._b_filter()
        sql = f"""
            SELECT COUNT(*), MIN(expiry_date), MAX(expiry_date)
            FROM members WHERE status='Active'
            AND expiry_date BETWEEN CAST(GETDATE() AS DATE)
            AND DATEADD(day,7,CAST(GETDATE() AS DATE)) {bf}
        """
        row = self._q(sql, list(bp))
        if not row[0]: return "✅  No memberships expiring in the next 7 days."
        return f"⚠️  **{row[0]}** membership(s) expiring in the next 7 days.\nEarliest: {row[1]}  |  Latest: {row[2]}"

    def _attendance_today(self):
        bf, bp = self._b_filter()
        sql = f"""
            SELECT COUNT(*),
                   SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN a.status='Late' THEN 1 ELSE 0 END)
            FROM attendance a
            JOIN members m ON a.member_id=m.id
            WHERE a.date=CAST(GETDATE() AS DATE) {bf}
        """
        row = self._q(sql, list(bp))
        return (f"📅  Attendance today ({date.today().strftime('%d %b %Y')}):\n"
                f"   Total checked in: **{row[0]}**\n"
                f"   Present on time:  **{row[1] or 0}**\n"
                f"   Late arrivals:    **{row[2] or 0}**")

    def _monthly_revenue(self):
        bf, bp = self._b_filter()
        sql = f"""
            SELECT ISNULL(SUM(py.amount),0)
            FROM payments py JOIN members m ON py.member_id=m.id
            WHERE py.status='Paid'
            AND MONTH(py.payment_date)=MONTH(GETDATE())
            AND YEAR(py.payment_date)=YEAR(GETDATE()) {bf}
        """
        row = self._q(sql, list(bp))
        return f"💰  Revenue collected this month: **Rs. {float(row[0]):,.0f}**"

    def _pending_payments(self):
        bf, bp = self._b_filter()
        sql = f"""
            SELECT COUNT(*), ISNULL(SUM(py.amount),0)
            FROM payments py JOIN members m ON py.member_id=m.id
            WHERE py.status IN ('Unpaid','Overdue') {bf}
        """
        row = self._q(sql, list(bp))
        return (f"📄  Pending / Overdue Payments:\n"
                f"   Count:  **{row[0]}** invoice(s)\n"
                f"   Amount: **Rs. {float(row[1]):,.0f}**")

    def _trainer_count(self):
        bf, bp = self._b_filter("t")
        sql = f"SELECT COUNT(*) FROM trainers t WHERE t.status='Active' {bf}"
        row = self._q(sql, list(bp))
        return f"💪  Active Trainers: **{row[0]}**"

    def _equipment_count(self):
        bf, bp = self._b_filter("e")
        sql = f"SELECT COUNT(*), SUM(quantity) FROM equipment e WHERE 1=1 {bf}"
        row = self._q(sql, list(bp))
        return f"🏋️  Equipment: **{row[0]}** types, **{row[1] or 0}** total units"

    def _maintenance_due(self):
        bf, bp = self._b_filter("e")
        sql = f"""
            SELECT COUNT(*) FROM equipment e
            WHERE (e.last_maintenance_date IS NULL
                OR DATEDIFF(day,e.last_maintenance_date,GETDATE())>90) {bf}
        """
        row = self._q(sql, list(bp))
        if not row[0]: return "✅  All equipment maintenance is up to date."
        return f"⚠️  **{row[0]}** equipment item(s) need maintenance (90+ days since last service)."

    def _top_trainer(self):
        bf, bp = self._b_filter("t")
        sql = f"""
            SELECT TOP 1 t.full_name, COUNT(m.id) AS cnt, t.performance_rating
            FROM trainers t LEFT JOIN members m ON m.trainer_id=t.id AND m.status='Active'
            WHERE t.status='Active' {bf}
            GROUP BY t.id, t.full_name, t.performance_rating ORDER BY cnt DESC
        """
        row = self._q(sql, list(bp))
        if not row: return "No trainer data available."
        return f"🏆  Top Trainer: **{row[0]}**\n   Active members: {row[1]}  |  Rating: ⭐ {row[2] or 'N/A'}"

    def _salary_status(self):
        bf, bp = self._b_filter("t")
        sql = f"""
            SELECT COUNT(*) FROM salary_records sr
            JOIN trainers t ON sr.trainer_id=t.id
            WHERE sr.status='Pending'
            AND sr.month=MONTH(GETDATE()) AND sr.year=YEAR(GETDATE()) {bf}
        """
        row = self._q(sql, list(bp))
        if not row[0]: return "✅  All salaries paid for this month."
        return f"💸  **{row[0]}** trainer salary(ies) still unpaid for this month."

    def _popular_goal(self):
        bf, bp = self._b_filter()
        sql = f"""
            SELECT TOP 1 fitness_goal, COUNT(*) AS cnt
            FROM members WHERE status='Active' {bf}
            GROUP BY fitness_goal ORDER BY cnt DESC
        """
        row = self._q(sql, list(bp))
        return f"🎯  Most popular fitness goal: **{row[0]}** ({row[1]} members)" if row else "No data."

    def _help(self):
        return ("🤖  **FitLife Smart Ask** — I can answer questions about your gym data:\n\n"
                "• Member counts and status\n"
                "• Today's attendance\n"
                "• Monthly revenue\n"
                "• Pending / overdue payments\n"
                "• Expiring memberships\n"
                "• Trainer statistics\n"
                "• Equipment inventory & maintenance\n"
                "• Salary status\n"
                "• Popular fitness goals\n"
                "• 🏋️ Workout & Diet Plan generation\n\n"
                "Just type your question naturally! (Configure OpenAI key for advanced AI features)")


# ── Smart Ask UI ──────────────────────────────────────────────────────────────
class SmartAskModule(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self._engine = SmartEngine(session)
        self._history = []
        self.setStyleSheet("background:transparent;")
        self._build_ui()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(20)

        # ── LEFT: Chat Pane ──
        chat_pane = QWidget()
        chat_pane.setStyleSheet("background:transparent;")
        m = QVBoxLayout(chat_pane)
        m.setContentsMargins(10, 10, 10, 10)
        m.setSpacing(16)

        hdr = QHBoxLayout()
        t = QLabel("🤖  Smart Ask"); t.setStyleSheet("QWidget { font-size:26px;font-weight:900;color:#F0F4FF; }")
        hdr.addWidget(t); hdr.addStretch()
        clr = QPushButton("🗑 Clear Chat"); clr.setObjectName("btnSecondary"); clr.setFixedHeight(36)
        clr.clicked.connect(self._clear); hdr.addWidget(clr)
        m.addLayout(hdr)

        sub = QLabel("Ask any question about your gym data — members, revenue, attendance, equipment and more.")
        sub.setStyleSheet("QWidget { color:#9CA3AF;font-size:13px; }"); m.addWidget(sub)

        # Chat area
        self._chat_scroll = QScrollArea(); self._chat_scroll.setWidgetResizable(True)
        self._chat_scroll.setStyleSheet("QWidget { border:1px solid rgba(0, 102, 255, 0.2);border-radius:14px;background:rgba(0,0,0,0.15); }")
        self._chat_container = QWidget(); self._chat_container.setStyleSheet("background:transparent;")
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setContentsMargins(16,16,16,16); self._chat_layout.setSpacing(12)
        self._chat_layout.addStretch()
        self._chat_scroll.setWidget(self._chat_container)
        m.addWidget(self._chat_scroll, 1)

        # Quick questions
        quick_label = QLabel("💡 Quick Questions:")
        quick_label.setStyleSheet("QWidget { color:#9CA3AF;font-size: 13px;font-weight:bold; }"); m.addWidget(quick_label)
        qrow = QHBoxLayout(); qrow.setSpacing(8)
        for q in ["Revenue this month?","Pending payments?","Expiring memberships?"]:
            qb = QPushButton(q); qb.setFixedHeight(32)
            qb.setStyleSheet("QPushButton{background:rgba(0, 102, 255, 0.15);border:1px solid rgba(0, 102, 255, 0.3);border-radius:16px;color:#9CA3AF;font-size: 13px;padding:0 12px;}QPushButton:hover{background:rgba(0, 102, 255, 0.3);color:#F0F4FF;}")
            qb.clicked.connect(lambda _, qq=q: self._send(qq)); qrow.addWidget(qb)
        qrow.addStretch(); m.addLayout(qrow)

        # Input row
        inp_row = QHBoxLayout(); inp_row.setSpacing(10)
        self._inp = QLineEdit(); self._inp.setPlaceholderText("Message FitLife AI...")
        self._inp.setMinimumHeight(44)
        self._inp.setStyleSheet("QLineEdit{background:rgba(255,255,255,0.06);border:1px solid rgba(0, 102, 255, 0.3);border-radius:12px;color:#F0F4FF;font-size:14px;padding:0 16px;}QLineEdit:focus{border:1px solid #0066FF;}")
        self._inp.returnPressed.connect(self._on_send); inp_row.addWidget(self._inp,1)
        sb = QPushButton("➤ Ask"); sb.setObjectName("btnPrimary"); sb.setMinimumHeight(44); sb.setMinimumWidth(80)
        sb.clicked.connect(self._on_send); inp_row.addWidget(sb)
        m.addLayout(inp_row)

        main_layout.addWidget(chat_pane, 5) # 50% width

        # ── RIGHT: Canvas Pane ──
        self._canvas_pane = QFrame()
        self._canvas_pane.setStyleSheet("QWidget { background:rgba(0,0,0,0.25); border:1px solid rgba(0, 102, 255, 0.3); border-radius:14px; }")
        canvas_layout = QVBoxLayout(self._canvas_pane)
        canvas_layout.setContentsMargins(20, 20, 20, 20)
        
        canvas_hdr = QHBoxLayout()
        ctitle = QLabel("📄 Smart Canvas")
        ctitle.setStyleSheet("QWidget { font-size:18px; font-weight:bold; color:#F0F4FF; }")
        canvas_hdr.addWidget(ctitle)
        canvas_hdr.addStretch()
        cclear = QPushButton("✖ Close")
        cclear.setStyleSheet("QWidget { background:transparent; color:#9CA3AF; font-size:14px; }")
        cclear.setCursor(Qt.CursorShape.PointingHandCursor)
        cclear.clicked.connect(self._hide_canvas)
        canvas_hdr.addWidget(cclear)
        canvas_layout.addLayout(canvas_hdr)
        
        self._canvas_text = QTextEdit()
        self._canvas_text.setReadOnly(True)
        self._canvas_text.setStyleSheet("QWidget { background:transparent; border:none; color:#E2E8F0; font-size:15px; }")
        canvas_layout.addWidget(self._canvas_text)
        
        main_layout.addWidget(self._canvas_pane, 6) # 60% width when visible
        self._canvas_pane.hide()

        # Greeting
        self._add_bot_bubble("👋  Hello! I'm your **FitLife Smart Assistant**.\n\nAsk me anything about your gym — members, revenue, attendance, equipment, and more!\n\nType **'help'** to see what I can answer.")

    def _on_send(self):
        q = self._inp.text().strip()
        if not q: return
        self._send(q)

    def _send(self, q):
        self._inp.clear()
        self._add_user_bubble(q)
        self._add_bot_bubble("⏳  Thinking…", temp=True)
        self._w = Worker(self._engine.answer, q)
        self._w.result.connect(lambda ans: self._on_answer(ans))
        self._w.error.connect(lambda e: self._on_answer(f"⚠️ Error: {e}"))
        self._w.start()

    def _on_answer(self, ans):
        # Remove "thinking" bubble
        item = self._chat_layout.itemAt(self._chat_layout.count()-1)
        if item and item.widget():
            w = item.widget()
            if "Thinking" in w.findChild(QLabel).text():
                self._chat_layout.removeWidget(w); w.deleteLater()
                
        # Send long plans to the Canvas
        if len(ans) > 400 or "```" in ans or "|-" in ans or "###" in ans:
            self._show_in_canvas(ans)
            self._add_bot_bubble("✨ I've generated the detailed content for you. I've opened it in the **Smart Canvas** on the right!")
        else:
            self._add_bot_bubble(ans)

    def _show_in_canvas(self, text):
        self._canvas_text.setMarkdown(text)
        self._canvas_pane.show()
        
    def _hide_canvas(self):
        self._canvas_pane.hide()

    def _add_user_bubble(self, text):
        f = QFrame(); f.setStyleSheet("QWidget { background:#2F2F2F; border-radius:16px; }")
        l = QVBoxLayout(f); l.setContentsMargins(16,12,16,12)
        lbl = QLabel(text); lbl.setWordWrap(True); lbl.setStyleSheet("QWidget { color:#F0F4FF;font-size:14px; }")
        l.addWidget(lbl)
        row = QHBoxLayout(); row.addStretch(); row.addWidget(f)
        row.setContentsMargins(0, 10, 0, 10)
        wrap = QWidget(); wrap.setLayout(row); wrap.setStyleSheet("background:transparent;")
        idx = self._chat_layout.count()-1
        self._chat_layout.insertWidget(idx, wrap)
        QTimer.singleShot(50, self._scroll_bottom)

    def _add_bot_bubble(self, text, temp=False):
        wrap = QWidget(); wrap.setStyleSheet("background:transparent;")
        row = QHBoxLayout(wrap); row.setContentsMargins(0, 10, 0, 10); row.setSpacing(16)
        
        # Avatar
        ava = QLabel("🤖"); ava.setStyleSheet("QWidget { font-size:20px; background:rgba(255,255,255,0.1); border-radius:18px; }")
        ava.setFixedSize(36, 36); ava.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_ava = QVBoxLayout(); v_ava.addWidget(ava); v_ava.addStretch()
        row.addLayout(v_ava)
        
        lbl = QLabel(); lbl.setWordWrap(True)
        lbl.setStyleSheet("QWidget { color:#E2E8F0;font-size:14px;line-height:1.6; }")
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        lbl.setOpenExternalLinks(True)
        
        if not temp:
            lbl.setTextFormat(Qt.TextFormat.MarkdownText)
            lbl.setText(text)
        else:
            lbl.setTextFormat(Qt.TextFormat.PlainText)
            lbl.setText(text)
            
        row.addWidget(lbl, 1)
        
        idx = self._chat_layout.count()-1
        self._chat_layout.insertWidget(idx, wrap)
        QTimer.singleShot(50, self._scroll_bottom)

    def _scroll_bottom(self):
        sb = self._chat_scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _clear(self):
        while self._chat_layout.count() > 1:
            w = self._chat_layout.takeAt(0).widget()
            if w: w.deleteLater()
        self._add_bot_bubble("💬  Chat cleared. Ask me anything!")
