"""FitLife — Staff Management Module (Phase 5)"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QLineEdit, QGridLayout,
    QStackedWidget, QDialog, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.components.glass_card import KPICard, StatusBadge, SectionHeader
from ui.components.data_table import DataTable
from ui.components.confirm_dialog import ConfirmDialog, InfoDialog
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
import services.staff_service as staff_svc
import services.member_service as member_svc
import services.branch_service as branch_svc
from config.constants import ROLE_ADMIN, ROLE_MANAGER


def _pill(label, color):
    return (f"QPushButton{{background:rgba(0,0,0,0.2);border:1px solid {color};"
            f"border-radius:6px;color:{color};font-size: 13px;padding:0 8px;min-height:28px;}}"
            f"QPushButton:hover{{background:{color}22;}}")


class StaffModule(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setStyleSheet("background:transparent;")
        self._stack = QStackedWidget(); self._stack.setStyleSheet("background:transparent;")
        QVBoxLayout(self).addWidget(self._stack); self.layout().setContentsMargins(0,0,0,0)
        self._list = _StaffList(session)
        self._list.open_add.connect(self._show_add)
        self._list.open_edit.connect(self._show_edit)
        self._stack.addWidget(self._list); self._stack.setCurrentWidget(self._list)

    def _show_add(self):
        w = _StaffForm(self._session)
        w.saved.connect(self._back); w.cancelled.connect(self._back)
        self._stack.addWidget(w); self._stack.setCurrentWidget(w)

    def _show_edit(self, uid):
        w = _StaffForm(self._session, user_id=uid)
        w.saved.connect(self._back); w.cancelled.connect(self._back)
        self._stack.addWidget(w); self._stack.setCurrentWidget(w)

    def _back(self):
        while self._stack.count() > 1:
            w = self._stack.widget(1); self._stack.removeWidget(w); w.deleteLater()
        self._stack.setCurrentWidget(self._list); self._list.refresh()

    def refresh(self):
        if hasattr(self._stack.currentWidget(), "refresh"):
            self._stack.currentWidget().refresh()


class _StaffList(QWidget):
    open_add  = pyqtSignal()
    open_edit = pyqtSignal(int)

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self._branch_id = session.branch_id if session.role == ROLE_MANAGER else None
        self.setStyleSheet("background:transparent;")
        self._build_ui(); self._load()

    def _build_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;background:transparent;")
        c = QWidget(); c.setStyleSheet("background:transparent;")
        m = QVBoxLayout(c); m.setContentsMargins(28,24,28,24); m.setSpacing(18)

        hdr = QHBoxLayout()
        t = QLabel("👤  Staff Management"); t.setStyleSheet("font-size:26px;font-weight:900;color:#F0F4FF;")
        hdr.addWidget(t); hdr.addStretch()
        if self._session.role == ROLE_ADMIN:
            b = QPushButton("➕ Add Staff"); b.setObjectName("btnPrimary"); b.setMinimumHeight(40)
            b.clicked.connect(self.open_add.emit); hdr.addWidget(b)
        m.addLayout(hdr)

        kr = QHBoxLayout(); kr.setSpacing(14)
        self._k_total    = KPICard("Total Staff","—","👥","","#7C3AED")
        self._k_active   = KPICard("Active","—","✅","","#00E676")
        self._k_inactive = KPICard("Inactive","—","🔴","","#FF2D78")
        for k in [self._k_total,self._k_active,self._k_inactive]: kr.addWidget(k)
        kr.addStretch(); m.addLayout(kr)

        # Filters
        ff = QFrame(); ff.setStyleSheet("background:rgba(255,255,255,0.04);border:1px solid rgba(124,58,237,0.2);border-radius:12px;")
        fr = QHBoxLayout(ff); fr.setContentsMargins(16,10,16,10); fr.setSpacing(10)
        fr.addWidget(QLabel("Role:"))
        self._rf = QComboBox(); self._rf.setFixedHeight(34)
        self._rf.addItem("All Roles",None)
        for rid, rname in staff_svc.get_roles_dropdown(): self._rf.addItem(rname,rname)
        self._rf.currentIndexChanged.connect(self._load); fr.addWidget(self._rf)

        fr.addWidget(QLabel("Status:"))
        self._sf = QComboBox(); self._sf.setFixedHeight(34)
        self._sf.addItem("All",None); self._sf.addItem("Active","Active"); self._sf.addItem("Inactive","Inactive")
        self._sf.currentIndexChanged.connect(self._load); fr.addWidget(self._sf)

        self._search = QLineEdit(); self._search.setPlaceholderText("Search name / username...")
        self._search.setFixedHeight(34); self._search.returnPressed.connect(self._load)
        fr.addWidget(self._search); fr.addStretch()
        rb = QPushButton("🔄"); rb.setObjectName("btnSecondary"); rb.setFixedHeight(34)
        rb.clicked.connect(self._load); fr.addWidget(rb)
        m.addWidget(ff)

        cols = ["ID","Username","Full Name","Email","Phone","Role","Branch","Status","Last Login","Actions"]
        self.table = DataTable(cols)
        tc = QFrame(); tc.setStyleSheet("background:rgba(255,255,255,0.04);border:1px solid rgba(124,58,237,0.2);border-radius:16px;")
        QVBoxLayout(tc).addWidget(self.table); m.addWidget(tc)

        self._overlay = LoadingOverlay(self)
        scroll.setWidget(c); QVBoxLayout(self).addWidget(scroll); self.layout().setContentsMargins(0,0,0,0)

    def _load(self):
        self._overlay.show_loading("Loading staff...")
        role   = self._rf.currentData()
        status = self._sf.currentData()
        srch   = self._search.text().strip() or None
        self._w = Worker(staff_svc.get_all_staff, self._branch_id, role, status, srch)
        self._w.result.connect(self._on_data)
        self._w.error.connect(lambda e: self._overlay.hide_loading())
        self._w.start()

    def _on_data(self, staff):
        self._overlay.hide_loading()
        stats = staff_svc.get_staff_stats(self._branch_id)
        self._k_total.set_value(str(stats["total"]))
        self._k_active.set_value(str(stats["active"]))
        self._k_inactive.set_value(str(stats["inactive"]))

        rows = [[s[0],s[1],s[2],s[3] or "—",s[4] or "—",s[5],s[6] or "—",
                 "Active" if s[7] else "Inactive",
                 str(s[8])[:16] if s[8] else "Never",""] for s in staff]
        self.table.set_data(rows)
        tw = self.table.table
        vis = staff[self.table._current_page*self.table._page_size:(self.table._current_page+1)*self.table._page_size]
        for ri, s in enumerate(vis):
            uid, is_active = s[0], s[7]
            cell = QWidget(); bl = QHBoxLayout(cell); bl.setContentsMargins(4,2,4,2); bl.setSpacing(4)
            if self._session.role == ROLE_ADMIN:
                eb = QPushButton("✏️ Edit"); eb.setStyleSheet(_pill("",c:="#7C3AED"))
                eb.clicked.connect(lambda _, i=uid: self.open_edit.emit(i)); bl.addWidget(eb)
                tb = QPushButton("🔒 Deactivate" if is_active else "✅ Activate")
                tb.setStyleSheet(_pill("",c:="#FF2D78" if is_active else "#00E676"))
                tb.clicked.connect(lambda _, i=uid, n=s[2]: self._toggle(i,n)); bl.addWidget(tb)
                pb = QPushButton("🔑 Reset PW"); pb.setStyleSheet(_pill("",c:="#FFB800"))
                pb.clicked.connect(lambda _, i=uid, n=s[2]: self._reset_pw(i,n)); bl.addWidget(pb)
            tw.setCellWidget(ri,9,cell)
            tw.setCellWidget(ri,7,StatusBadge("Active" if is_active else "Inactive"))

    def _toggle(self, uid, name):
        dlg = ConfirmDialog("Toggle Account",f"Change status for '{name}'?","Confirm","primary",self)
        if dlg.exec():
            result = staff_svc.toggle_staff_status(uid, self._session.user_id)
            InfoDialog("Result",result["message"],"success" if result["success"] else "error",self).exec()
            if result["success"]: self._load()

    def _reset_pw(self, uid, name):
        dlg = _ResetPasswordDialog(uid, name, self._session.user_id, self)
        dlg.exec(); self._load()

    def refresh(self): self._load()


class _StaffForm(QWidget):
    saved = pyqtSignal(); cancelled = pyqtSignal()

    def __init__(self, session, user_id=None, parent=None):
        super().__init__(parent)
        self._session = session; self._user_id = user_id; self._is_edit = user_id is not None
        self.setStyleSheet("background:transparent;")
        self._build_ui()
        if self._is_edit: self._load()

    def _inp(self, ph=""): f=QLineEdit(); f.setPlaceholderText(ph); f.setMinimumHeight(38); return f
    def _lbl(self, t): l=QLabel(t); l.setStyleSheet("color:#9CA3AF;font-size:13px;"); return l

    def _build_ui(self):
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;background:transparent;")
        c = QWidget(); c.setStyleSheet("background:transparent;")
        m = QVBoxLayout(c); m.setContentsMargins(28,24,28,28); m.setSpacing(18)

        hdr = QHBoxLayout()
        back = QPushButton("← Back"); back.setObjectName("btnSecondary"); back.setFixedHeight(36)
        back.clicked.connect(self.cancelled.emit); hdr.addWidget(back)
        hdr.addWidget(QLabel(f"{'✏️ Edit' if self._is_edit else '➕ Add'} Staff Account")); hdr.addStretch()
        sv = QPushButton("💾 Save"); sv.setObjectName("btnPrimary"); sv.setMinimumHeight(40)
        sv.clicked.connect(self._save); hdr.addWidget(sv)
        m.addLayout(hdr)

        card = QFrame(); card.setStyleSheet("background:rgba(255,255,255,0.05);border:1px solid rgba(124,58,237,0.25);border-radius:16px;")
        g = QGridLayout(card); g.setContentsMargins(28,24,28,28); g.setSpacing(14)
        g.setColumnStretch(1,1); g.setColumnStretch(3,1)

        g.addWidget(self._lbl("Username *"),0,0); self._user=self._inp("username"); g.addWidget(self._user,0,1)
        if self._is_edit: self._user.setEnabled(False)
        g.addWidget(self._lbl("Full Name *"),0,2); self._name=self._inp("Full Name"); g.addWidget(self._name,0,3)

        g.addWidget(self._lbl("Email"),1,0); self._email=self._inp("email@example.com"); g.addWidget(self._email,1,1)
        g.addWidget(self._lbl("Phone"),1,2); self._phone=self._inp("+92..."); g.addWidget(self._phone,1,3)

        g.addWidget(self._lbl("Role *"),2,0)
        self._role = QComboBox(); self._role.setMinimumHeight(38)
        self._roles_data = staff_svc.get_roles_dropdown()
        for rid, rname in self._roles_data: self._role.addItem(rname, rid)
        g.addWidget(self._role,2,1)

        g.addWidget(self._lbl("Branch"),2,2)
        self._branch = QComboBox(); self._branch.setMinimumHeight(38)
        self._branch.addItem("— No Branch —",None)
        for bid, bname in branch_svc.get_all_branches_dropdown(): self._branch.addItem(bname, bid)
        g.addWidget(self._branch,2,3)
        # Optional member linking dropdown
        g.addWidget(self._lbl("Link Member (optional)"),3,0)
        self._member_link = QComboBox(); self._member_link.setMinimumHeight(38)
        self._member_link.addItem("— None —", None)
        for mid, mname in member_svc.get_unlinked_members():
            self._member_link.addItem(mname, mid)
        g.addWidget(self._member_link,3,1)

        if not self._is_edit:
            g.addWidget(self._lbl("Password *"),4,0)
            self._pw = QLineEdit(); self._pw.setEchoMode(QLineEdit.EchoMode.Password)
            self._pw.setPlaceholderText("Min. 8 characters"); self._pw.setMinimumHeight(38)
            g.addWidget(self._pw,4,1)
            g.addWidget(self._lbl("Confirm Password *"),4,2)
            self._pw2 = QLineEdit(); self._pw2.setEchoMode(QLineEdit.EchoMode.Password)
            self._pw2.setPlaceholderText("Repeat password"); self._pw2.setMinimumHeight(38)
            g.addWidget(self._pw2,4,3)

        m.addWidget(card); m.addStretch(); scroll.setWidget(c)
        QVBoxLayout(self).addWidget(scroll); self.layout().setContentsMargins(0,0,0,0)

    def _load(self):
        s = staff_svc.get_staff_by_id(self._user_id)
        if not s: return
        self._user.setText(s[1])
        self._name.setText(s[2])
        self._email.setText(s[3] or "")
        self._phone.setText(s[4] or "")
        idx = self._role.findData(s[6]); self._role.setCurrentIndex(max(0,idx))
        if s[7]:
            idx = self._branch.findData(s[7]); self._branch.setCurrentIndex(max(0,idx))

    def _save(self):
        if not self._name.text().strip():
            InfoDialog("Error","Full name required.","error",self).exec(); return
        if not self._is_edit and not self._user.text().strip():
            InfoDialog("Error","Username required.","error",self).exec(); return
        data = {
            "full_name": self._name.text().strip(),
            "email":     self._email.text().strip(),
            "phone":     self._phone.text().strip(),
            "role_id":   self._role.currentData(),
            "branch_id": self._branch.currentData(),
        }
        if not self._is_edit:
            pw = self._pw.text(); pw2 = self._pw2.text()
            if pw != pw2:
                InfoDialog("Error","Passwords do not match.","error",self).exec(); return
            data["username"] = self._user.text().strip()
            data["password"] = pw
            result = staff_svc.create_staff(data, self._session.user_id)
        else:
            result = staff_svc.update_staff(self._user_id, data, self._session.user_id)
        InfoDialog("Result",result["message"],"success" if result["success"] else "error",self).exec()
        if result["success"]:
            # If a member is linked, associate the newly created staff user with the member
            member_id = self._member_link.currentData()
            if member_id:
                link_res = member_svc.link_member_user(member_id, result.get("user_id"))
                InfoDialog("Member Link", link_res["message"], "success" if link_res["success"] else "error", self).exec()
            self.saved.emit()


class _ResetPasswordDialog(QDialog):
    def __init__(self, user_id, username, admin_id, parent=None):
        super().__init__(parent)
        self._user_id = user_id; self._admin_id = admin_id
        self.setWindowTitle(f"Reset Password — {username}")
        self.setMinimumWidth(400); self.setStyleSheet("background:#0D1B2A;color:#F0F4FF;")
        layout = QVBoxLayout(self); layout.setContentsMargins(24,20,24,20); layout.setSpacing(12)
        layout.addWidget(QLabel(f"🔑  Reset password for: {username}"))
        self._pw = QLineEdit(); self._pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw.setPlaceholderText("New password (min. 8 chars)"); self._pw.setMinimumHeight(38)
        self._pw2 = QLineEdit(); self._pw2.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw2.setPlaceholderText("Confirm new password"); self._pw2.setMinimumHeight(38)
        layout.addWidget(self._pw); layout.addWidget(self._pw2)
        brow = QHBoxLayout(); brow.addStretch()
        cancel = QPushButton("Cancel"); cancel.setFixedHeight(36); cancel.clicked.connect(self.reject)
        brow.addWidget(cancel)
        save = QPushButton("✅ Reset Password")
        save.setStyleSheet("QPushButton{background:#7C3AED;border:none;border-radius:10px;color:#fff;font-size:14px;padding:0 20px;}QPushButton:hover{background:#8B5CF6;}")
        save.setFixedHeight(36); save.clicked.connect(self._save); brow.addWidget(save)
        layout.addLayout(brow)

    def _save(self):
        pw = self._pw.text(); pw2 = self._pw2.text()
        if pw != pw2:
            InfoDialog("Error","Passwords do not match.","error",self).exec(); return
        result = staff_svc.reset_staff_password(self._user_id, pw, self._admin_id)
        InfoDialog("Result",result["message"],"success" if result["success"] else "error",self).exec()
        if result["success"]: self.accept()
