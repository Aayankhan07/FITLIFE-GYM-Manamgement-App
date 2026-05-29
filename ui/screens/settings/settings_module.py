"""FitLife — Settings Module (Phase 7)"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QComboBox, QTabWidget,
    QGridLayout, QCheckBox, QSpinBox, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.components.glass_card import SectionHeader
from ui.components.confirm_dialog import ConfirmDialog, InfoDialog
from config.constants import ROLE_ADMIN, ROLE_MANAGER
import services.settings_service as svc


def _lbl(text, style="color:#9CA3AF;font-size:13px;"):
    l = QLabel(text); l.setStyleSheet(style); return l

def _inp(placeholder="", echo=False):
    f = QLineEdit(); f.setPlaceholderText(placeholder); f.setMinimumHeight(38)
    if echo: f.setEchoMode(QLineEdit.EchoMode.Password)
    return f


class SettingsModule(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setStyleSheet("background:transparent;")
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;background:transparent;")
        c = QWidget(); c.setStyleSheet("background:transparent;")
        m = QVBoxLayout(c); m.setContentsMargins(28,24,28,28); m.setSpacing(18)

        hdr = QHBoxLayout()
        t = QLabel("⚙️  Settings"); t.setStyleSheet("font-size:26px;font-weight:900;color:#F0F4FF;")
        hdr.addWidget(t); hdr.addStretch(); m.addLayout(hdr)

        tabs = QTabWidget(); tabs.setStyleSheet("""
            QTabWidget::pane{background:rgba(255,255,255,0.04);border:1px solid rgba(124,58,237,0.2);border-radius:12px;}
            QTabBar::tab{background:rgba(0,0,0,0.2);color:#9CA3AF;padding:10px 20px;border-radius:8px;margin-right:4px;}
            QTabBar::tab:selected{background:rgba(124,58,237,0.3);color:#7C3AED;font-weight:bold;}
        """)
        tabs.addTab(self._build_profile(), "👤 Profile")
        tabs.addTab(self._build_notifications(), "🔔 Notifications")
        if self._session.role == ROLE_ADMIN:
            tabs.addTab(self._build_system(), "🛠 System Config")
            tabs.addTab(self._build_reminders(), "⚠️ Alerts Preview")
        m.addWidget(tabs); m.addStretch()
        scroll.setWidget(c)
        QVBoxLayout(self).addWidget(scroll); self.layout().setContentsMargins(0,0,0,0)

    # ── Profile Tab ──────────────────────────────────────────────────────────
    def _build_profile(self):
        w = QWidget(); w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w); lay.setContentsMargins(20,20,20,20); lay.setSpacing(20)
        lay.addWidget(SectionHeader("👤  My Profile"))

        info_card = QFrame(); info_card.setStyleSheet("background:rgba(255,255,255,0.05);border:1px solid rgba(124,58,237,0.2);border-radius:14px;")
        ig = QGridLayout(info_card); ig.setContentsMargins(24,20,24,20); ig.setSpacing(12)
        ig.setColumnStretch(1,1); ig.setColumnStretch(3,1)

        s = svc.get_setting  # not user data, but we can show session
        session = self._session
        ig.addWidget(_lbl("Full Name:"),0,0); name_lbl=_lbl(session.full_name,"color:#F0F4FF;font-size:14px;font-weight:bold;"); ig.addWidget(name_lbl,0,1)
        ig.addWidget(_lbl("Role:"),0,2); ig.addWidget(_lbl(session.role,"color:#7C3AED;font-size:14px;font-weight:bold;"),0,3)
        lay.addWidget(info_card)

        lay.addWidget(SectionHeader("🔑  Change Password"))
        pw_card = QFrame(); pw_card.setStyleSheet("background:rgba(255,255,255,0.05);border:1px solid rgba(124,58,237,0.2);border-radius:14px;")
        pg = QGridLayout(pw_card); pg.setContentsMargins(24,20,24,20); pg.setSpacing(12)
        pg.setColumnStretch(1,1)

        pg.addWidget(_lbl("Current Password:"),0,0); self._cur_pw=_inp("Current password",echo=True); pg.addWidget(self._cur_pw,0,1)
        pg.addWidget(_lbl("New Password:"),1,0); self._new_pw=_inp("Min. 8 characters",echo=True); pg.addWidget(self._new_pw,1,1)
        pg.addWidget(_lbl("Confirm New:"),2,0); self._conf_pw=_inp("Repeat new password",echo=True); pg.addWidget(self._conf_pw,2,1)

        save_pw = QPushButton("🔑 Change Password"); save_pw.setObjectName("btnPrimary"); save_pw.setFixedHeight(40)
        save_pw.clicked.connect(self._change_password)
        pg.addWidget(save_pw,3,1); lay.addWidget(pw_card)
        lay.addStretch(); return w

    def _change_password(self):
        cur=self._cur_pw.text(); new=self._new_pw.text(); conf=self._conf_pw.text()
        if new != conf:
            InfoDialog("Error","New passwords do not match.","error",self).exec(); return
        if len(new) < 8:
            InfoDialog("Error","Password must be at least 8 characters.","error",self).exec(); return
        r = svc.change_own_password(self._session.user_id, cur, new)
        InfoDialog("Result",r["message"],"success" if r["success"] else "error",self).exec()
        if r["success"]:
            for f in [self._cur_pw, self._new_pw, self._conf_pw]: f.clear()

    # ── Notifications Tab ────────────────────────────────────────────────────
    def _build_notifications(self):
        w = QWidget(); w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w); lay.setContentsMargins(20,20,20,20); lay.setSpacing(16)
        lay.addWidget(SectionHeader("🔔  Notification Preferences"))

        ns = svc.get_notification_settings(self._session.user_id)
        card = QFrame(); card.setStyleSheet("background:rgba(255,255,255,0.05);border:1px solid rgba(124,58,237,0.2);border-radius:14px;")
        g = QGridLayout(card); g.setContentsMargins(24,20,24,20); g.setSpacing(14)
        g.setColumnStretch(1,1)

        self._em_notif = QCheckBox("Enable Email Notifications"); self._em_notif.setChecked(ns["email_notif"])
        self._wa_notif = QCheckBox("Enable WhatsApp Notifications"); self._wa_notif.setChecked(ns["whatsapp_notif"])
        g.addWidget(self._em_notif,0,0,1,2)
        g.addWidget(self._wa_notif,1,0,1,2)

        g.addWidget(_lbl("Email Address:"),2,0); self._notif_email=_inp("your@email.com"); self._notif_email.setText(ns["email"]); g.addWidget(self._notif_email,2,1)
        g.addWidget(_lbl("WhatsApp/Phone:"),3,0); self._notif_phone=_inp("+92300..."); self._notif_phone.setText(ns["phone"]); g.addWidget(self._notif_phone,3,1)

        sv = QPushButton("💾 Save Preferences"); sv.setObjectName("btnPrimary"); sv.setFixedHeight(40)
        sv.clicked.connect(self._save_notifications); g.addWidget(sv,4,1)
        lay.addWidget(card); lay.addStretch(); return w

    def _save_notifications(self):
        data={"email_notif":self._em_notif.isChecked(),"whatsapp_notif":self._wa_notif.isChecked(),
              "email":self._notif_email.text().strip(),"phone":self._notif_phone.text().strip()}
        r=svc.save_notification_settings(self._session.user_id,data)
        InfoDialog("Result",r["message"],"success" if r["success"] else "error",self).exec()

    # ── System Config Tab (Admin only) ───────────────────────────────────────
    def _build_system(self):
        w = QWidget(); w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w); lay.setContentsMargins(20,20,20,20); lay.setSpacing(16)
        lay.addWidget(SectionHeader("🛠  System Configuration"))

        all_s = svc.get_all_settings()
        card = QFrame(); card.setStyleSheet("background:rgba(255,255,255,0.05);border:1px solid rgba(124,58,237,0.2);border-radius:14px;")
        g = QGridLayout(card); g.setContentsMargins(24,20,24,20); g.setSpacing(14)
        g.setColumnStretch(1,1)

        DEFAULTS = [
            ("app_name",         "Application Name",         "FitLife"),
            ("gym_address",      "Gym HQ Address",            ""),
            ("support_email",    "Support Email",             ""),
            ("support_phone",    "Support Phone",             ""),
            ("invoice_prefix",   "Invoice Prefix",            "INV-"),
            ("currency_symbol",  "Currency Symbol",           "Rs."),
            ("renewal_reminder_days", "Renewal Reminder (days)", "7"),
            ("overdue_check_day","Overdue Check Day",         "10"),
            ("page_size",        "Default Page Size",         "25"),
        ]
        self._sys_fields = {}
        for i, (key, label, default) in enumerate(DEFAULTS):
            g.addWidget(_lbl(f"{label}:"),i,0)
            val = all_s.get(key, default)
            f = _inp(default); f.setText(val)
            self._sys_fields[key] = f; g.addWidget(f,i,1)

        sv = QPushButton("💾 Save System Settings"); sv.setObjectName("btnPrimary"); sv.setFixedHeight(40)
        sv.clicked.connect(self._save_system)
        g.addWidget(sv,len(DEFAULTS),1)
        lay.addWidget(card); lay.addStretch(); return w

    def _save_system(self):
        settings = {k: f.text().strip() for k, f in self._sys_fields.items()}
        r = svc.bulk_save_settings(settings, self._session.user_id)
        InfoDialog("Result",r["message"],"success" if r["success"] else "error",self).exec()

    # ── AI Config Tab (Admin only) ───────────────────────────────────────────
    def _build_ai(self):
        w = QWidget(); w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w); lay.setContentsMargins(20,20,20,20); lay.setSpacing(16)
        lay.addWidget(SectionHeader("🤖  OpenAI / LLM Integration"))

        desc = QLabel("Configure your API key below to unlock intelligent responses, automatic diet plan generation, and personalized workout programs in the Smart Ask module.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color:#9CA3AF;font-size:13px;")
        lay.addWidget(desc)

        ai_s = svc.get_ai_settings()
        card = QFrame(); card.setStyleSheet("background:rgba(255,255,255,0.05);border:1px solid rgba(124,58,237,0.2);border-radius:14px;")
        g = QGridLayout(card); g.setContentsMargins(24,20,24,20); g.setSpacing(14)
        g.setColumnStretch(1,1)

        g.addWidget(_lbl("Provider:"),0,0); self._ai_prov = _inp("openai"); self._ai_prov.setText(ai_s.get("provider", "openai")); g.addWidget(self._ai_prov,0,1)
        g.addWidget(_lbl("API Key:"),1,0); self._ai_key = _inp("sk-...", echo=True); self._ai_key.setText(ai_s.get("api_key", "")); g.addWidget(self._ai_key,1,1)
        g.addWidget(_lbl("Model:"),2,0); self._ai_model = _inp("gpt-3.5-turbo"); self._ai_model.setText(ai_s.get("model", "gpt-3.5-turbo")); g.addWidget(self._ai_model,2,1)

        sv = QPushButton("💾 Save AI Settings"); sv.setObjectName("btnPrimary"); sv.setFixedHeight(40)
        sv.clicked.connect(self._save_ai)
        g.addWidget(sv,3,1)
        lay.addWidget(card); lay.addStretch(); return w

    def _save_ai(self):
        r = svc.save_ai_settings(self._ai_prov.text().strip(), self._ai_key.text().strip(), self._ai_model.text().strip())
        InfoDialog("Result",r["message"],"success" if r["success"] else "error",self).exec()

    # ── Alerts Preview Tab ───────────────────────────────────────────────────
    def _build_reminders(self):
        w = QWidget(); w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w); lay.setContentsMargins(20,20,20,20); lay.setSpacing(16)
        lay.addWidget(SectionHeader("⚠️  Upcoming Alerts"))

        hdr = QHBoxLayout(); hdr.addStretch()
        rb = QPushButton("🔄 Refresh"); rb.setObjectName("btnSecondary"); rb.setFixedHeight(36)
        rb.clicked.connect(self._load_alerts); hdr.addWidget(rb); lay.addLayout(hdr)

        self._alerts_area = QTextEdit(); self._alerts_area.setReadOnly(True)
        self._alerts_area.setStyleSheet("background:rgba(0,0,0,0.2);border:1px solid rgba(124,58,237,0.2);border-radius:12px;color:#F0F4FF;font-size:13px;padding:12px;")
        self._alerts_area.setMinimumHeight(300)
        lay.addWidget(self._alerts_area); lay.addStretch()
        self._load_alerts(); return w

    def _load_alerts(self):
        lines = ["=== EXPIRING MEMBERSHIPS (next 7 days) ===\n"]
        expiring = svc.get_expiring_memberships(7)
        if expiring:
            for e in expiring:
                lines.append(f"  • {e[0]} | 📞 {e[1]} | Expires: {e[3]} | Plan: {e[5] or '—'}")
        else:
            lines.append("  ✅ No memberships expiring in 7 days.")

        lines.append("\n=== OVERDUE PAYMENTS ===\n")
        overdue = svc.get_overdue_payments()
        if overdue:
            for o in overdue:
                lines.append(f"  • {o[0]} | 📞 {o[1]} | Invoice: {o[2]} | Rs. {o[3]:,.0f} | Due: {o[4]}")
        else:
            lines.append("  ✅ No overdue payments.")

        self._alerts_area.setPlainText("\n".join(lines))
