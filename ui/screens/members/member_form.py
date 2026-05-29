"""
FitLife — Member Add/Edit Form
Full validated form with QDateEdit, QComboBox, BMI auto-calculation.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDateEdit, QTextEdit,
    QFrame, QScrollArea, QDoubleSpinBox, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont

from ui.components.confirm_dialog import InfoDialog
import services.member_service as member_svc
import services.branch_service as branch_svc
import services.trainer_service as trainer_svc
import services.membership_service as membership_svc
from config.constants import (
    FITNESS_GOALS, MEMBER_STATUSES, ROLE_ADMIN, ROLE_MANAGER
)


class MemberForm(QWidget):
    """Add / Edit member form."""

    saved   = pyqtSignal()   # emitted on successful save
    cancelled = pyqtSignal()

    def __init__(self, session, member_id: int = None, parent=None):
        super().__init__(parent)
        self._session = session
        self._member_id = member_id
        self._is_edit = member_id is not None
        self._branch_map: dict = {}
        self._trainer_map: dict = {}
        self._plan_map: dict = {}
        self.setStyleSheet("background: transparent;")
        self._setup_ui()
        self._populate_dropdowns()
        if self._is_edit:
            self._load_member_data()

    def _field(self, placeholder="", required=False) -> QLineEdit:
        f = QLineEdit()
        f.setPlaceholderText(placeholder)
        f.setMinimumHeight(38)
        return f

    def _label(self, text: str, required=False) -> QLabel:
        lbl = QLabel(f"{'* ' if required else ''}{text}")
        lbl.setStyleSheet(
            "color:#9CA3AF; font-size:13px;"
            + (" font-weight:600;" if required else "")
        )
        return lbl

    def _err_label(self) -> QLabel:
        lbl = QLabel("")
        lbl.setStyleSheet("color:#FF2D78; font-size: 13px; margin-top:-6px;")
        return lbl

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")

        container = QWidget()
        container.setStyleSheet("background:transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(28, 24, 28, 28)
        main.setSpacing(20)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("btnSecondary")
        back_btn.setFixedHeight(36)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.cancelled.emit)
        hdr.addWidget(back_btn)

        title_text = "Edit Member" if self._is_edit else "Add New Member"
        title = QLabel(f"{'✏️' if self._is_edit else '➕'}  {title_text}")
        title.setStyleSheet("font-size:24px; font-weight:900; color:#F0F4FF;")
        hdr.addWidget(title)
        hdr.addStretch()

        self.save_btn = QPushButton("💾  Save Member")
        self.save_btn.setObjectName("btnPrimary")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self._save)
        hdr.addWidget(self.save_btn)
        main.addLayout(hdr)

        # ── Form Card ─────────────────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("glassCard")
        card.setStyleSheet("""
            QFrame#glassCard {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(124,58,237,0.25);
                border-radius: 16px;
            }
        """)
        grid = QGridLayout(card)
        grid.setContentsMargins(28, 24, 28, 28)
        grid.setSpacing(14)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        r = 0
        # Section: Personal Info
        sec1 = QLabel("Personal Information")
        sec1.setStyleSheet("font-size:15px; font-weight:bold; color:#7C3AED; margin-top:8px;")
        grid.addWidget(sec1, r, 0, 1, 4)
        r += 1

        # Full Name
        grid.addWidget(self._label("Full Name", True), r, 0)
        self.full_name = self._field("e.g. Ahmed Siddiqui")
        grid.addWidget(self.full_name, r, 1)
        self._err_fn = self._err_label()

        # CNIC
        grid.addWidget(self._label("CNIC (13 digits)", True), r, 2)
        self.cnic = self._field("e.g. 4210112345671")
        grid.addWidget(self.cnic, r, 3)
        r += 1
        grid.addWidget(self._err_fn, r, 1)
        self._err_cnic = self._err_label()
        grid.addWidget(self._err_cnic, r, 3)
        r += 1

        # Date of Birth
        grid.addWidget(self._label("Date of Birth", True), r, 0)
        self.dob = QDateEdit()
        self.dob.setCalendarPopup(True)
        self.dob.setDisplayFormat("dd/MM/yyyy")
        self.dob.setDate(QDate(1995, 1, 1))
        self.dob.setMinimumHeight(38)
        grid.addWidget(self.dob, r, 1)

        # Phone
        grid.addWidget(self._label("Phone", True), r, 2)
        self.phone = self._field("e.g. 03001234567")
        grid.addWidget(self.phone, r, 3)
        r += 1

        # Email
        grid.addWidget(self._label("Email"), r, 0)
        self.email = self._field("e.g. user@email.com")
        grid.addWidget(self.email, r, 1)

        # Emergency Contact
        grid.addWidget(self._label("Emergency Contact"), r, 2)
        self.emergency = self._field("e.g. 03009876543")
        grid.addWidget(self.emergency, r, 3)
        r += 1

        # Address
        grid.addWidget(self._label("Address"), r, 0)
        self.address = self._field("Full address")
        grid.addWidget(self.address, r, 1, 1, 3)
        r += 1

        # Section: Physical Info
        sec2 = QLabel("Physical Information")
        sec2.setStyleSheet("font-size:15px; font-weight:bold; color:#7C3AED; margin-top:8px;")
        grid.addWidget(sec2, r, 0, 1, 4)
        r += 1

        # Weight
        grid.addWidget(self._label("Weight (kg)"), r, 0)
        self.weight = QDoubleSpinBox()
        self.weight.setRange(30, 300)
        self.weight.setValue(75)
        self.weight.setSuffix(" kg")
        self.weight.setMinimumHeight(38)
        self.weight.valueChanged.connect(self._update_bmi)
        grid.addWidget(self.weight, r, 1)

        # Height
        grid.addWidget(self._label("Height (cm)"), r, 2)
        self.height = QDoubleSpinBox()
        self.height.setRange(100, 250)
        self.height.setValue(175)
        self.height.setSuffix(" cm")
        self.height.setMinimumHeight(38)
        self.height.valueChanged.connect(self._update_bmi)
        grid.addWidget(self.height, r, 3)
        r += 1

        # BMI display
        self.bmi_lbl = QLabel("BMI: — (auto-calculated)")
        self.bmi_lbl.setStyleSheet("color:#00F5FF; font-size:13px; font-weight:600;")
        grid.addWidget(self.bmi_lbl, r, 1, 1, 3)
        r += 1

        # Fitness Goal
        grid.addWidget(self._label("Fitness Goal"), r, 0)
        self.goal = QComboBox()
        for g in FITNESS_GOALS:
            self.goal.addItem(g, g)
        self.goal.setMinimumHeight(38)
        grid.addWidget(self.goal, r, 1)

        # Health Conditions
        grid.addWidget(self._label("Health Conditions"), r, 2)
        self.health = self._field("e.g. Diabetes, Hypertension")
        grid.addWidget(self.health, r, 3)
        r += 1

        # Section: Gym Assignment
        sec3 = QLabel("Gym Assignment")
        sec3.setStyleSheet("font-size:15px; font-weight:bold; color:#7C3AED; margin-top:8px;")
        grid.addWidget(sec3, r, 0, 1, 4)
        r += 1

        # Branch
        grid.addWidget(self._label("Branch", True), r, 0)
        self.branch_cb = QComboBox()
        self.branch_cb.setMinimumHeight(38)
        self.branch_cb.currentIndexChanged.connect(self._on_branch_changed)
        grid.addWidget(self.branch_cb, r, 1)

        # Trainer
        grid.addWidget(self._label("Assigned Trainer"), r, 2)
        self.trainer_cb = QComboBox()
        self.trainer_cb.addItem("— No Trainer —", None)
        self.trainer_cb.setMinimumHeight(38)
        grid.addWidget(self.trainer_cb, r, 3)
        r += 1

        # Membership Plan
        grid.addWidget(self._label("Membership Plan"), r, 0)
        self.plan_cb = QComboBox()
        self.plan_cb.addItem("— Select Plan —", None)
        self.plan_cb.setMinimumHeight(38)
        self.plan_cb.currentIndexChanged.connect(self._on_plan_changed)
        grid.addWidget(self.plan_cb, r, 1)

        # Status
        grid.addWidget(self._label("Status"), r, 2)
        self.status_cb = QComboBox()
        for s in MEMBER_STATUSES:
            self.status_cb.addItem(s, s)
        self.status_cb.setMinimumHeight(38)
        grid.addWidget(self.status_cb, r, 3)
        r += 1

        # Join Date
        grid.addWidget(self._label("Join Date", True), r, 0)
        self.join_date = QDateEdit()
        self.join_date.setCalendarPopup(True)
        self.join_date.setDisplayFormat("dd/MM/yyyy")
        self.join_date.setDate(QDate.currentDate())
        self.join_date.setMinimumHeight(38)
        self.join_date.dateChanged.connect(self._on_plan_changed)
        grid.addWidget(self.join_date, r, 1)

        # Expiry Date (auto or manual)
        grid.addWidget(self._label("Expiry Date"), r, 2)
        self.expiry_date = QDateEdit()
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setDisplayFormat("dd/MM/yyyy")
        self.expiry_date.setDate(QDate.currentDate().addDays(30))
        self.expiry_date.setMinimumHeight(38)
        grid.addWidget(self.expiry_date, r, 3)
        r += 1

        self.expiry_note = QLabel("🔄 Expiry auto-calculates when a plan is selected.")
        self.expiry_note.setStyleSheet("color:#6B7280; font-size: 13px;")
        grid.addWidget(self.expiry_note, r, 2, 1, 2)
        r += 1

        main.addWidget(card)
        main.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── Dropdowns ─────────────────────────────────────────────────────────────
    def _populate_dropdowns(self):
        branches = branch_svc.get_all_branches_dropdown()
        self.branch_cb.blockSignals(True)
        self.branch_cb.clear()
        self._branch_map = {}
        for bid, bname in branches:
            self.branch_cb.addItem(bname, bid)
            self._branch_map[bid] = bname

        # Manager-restricted to their branch
        if self._session.role == ROLE_MANAGER and self._session.branch_id:
            idx = self.branch_cb.findData(self._session.branch_id)
            if idx >= 0:
                self.branch_cb.setCurrentIndex(idx)
            self.branch_cb.setEnabled(False)

        self.branch_cb.blockSignals(False)
        self._on_branch_changed()

        # Plans
        plans = membership_svc.get_plans_dropdown()
        self.plan_cb.clear()
        self.plan_cb.addItem("— Select Plan —", None)
        self._plan_map = {}
        for pid, pname, pdays, pprice in plans:
            self.plan_cb.addItem(f"{pname} ({pdays}d — Rs.{pprice:,.0f})", pid)
            self._plan_map[pid] = (pname, pdays, pprice)

    def _on_branch_changed(self):
        branch_id = self.branch_cb.currentData()
        self.trainer_cb.clear()
        self.trainer_cb.addItem("— No Trainer —", None)
        if branch_id:
            trainers = trainer_svc.get_trainers_for_branch(branch_id)
            for tid, tname, spec in trainers:
                self.trainer_cb.addItem(f"{tname} ({spec})", tid)

    def _on_plan_changed(self):
        plan_id = self.plan_cb.currentData()
        if plan_id and plan_id in self._plan_map:
            _, duration_days, _ = self._plan_map[plan_id]
            start = self.join_date.date().toPyDate()
            from services.membership_service import calculate_expiry
            from datetime import date as dt_date
            exp = calculate_expiry(start, duration_days)
            self.expiry_date.setDate(QDate(exp.year, exp.month, exp.day))
            self.expiry_note.setText(f"✅ Expiry auto-set: {exp.strftime('%d %b %Y')} ({duration_days} days)")
            self.expiry_note.setStyleSheet("color:#00E676; font-size: 13px;")
        else:
            self.expiry_note.setText("🔄 Expiry auto-calculates when a plan is selected.")
            self.expiry_note.setStyleSheet("color:#6B7280; font-size: 13px;")

    def _update_bmi(self):
        try:
            w = self.weight.value()
            h = self.height.value() / 100
            if h > 0:
                bmi = round(w / (h * h), 1)
                cat = ""
                if bmi < 18.5:   cat = "Underweight"
                elif bmi < 25:   cat = "Normal"
                elif bmi < 30:   cat = "Overweight"
                else:            cat = "Obese"
                self.bmi_lbl.setText(f"BMI: {bmi} — {cat}")
        except Exception:
            pass

    # ── Load Existing Member (Edit Mode) ─────────────────────────────────────
    def _load_member_data(self):
        m = member_svc.get_member_by_id(self._member_id)
        if not m:
            return
        # m: id, full_name, cnic, dob, phone, email, emergency, address,
        #    photo_path, goal, health, weight, height, bmi,
        #    join_date, expiry_date, status, branch_id, trainer_id, plan_id,
        #    user_id, created_at, updated_at, branch_name, trainer_name, plan_name

        self.full_name.setText(m[1] or "")
        self.cnic.setText(m[2] or "")
        if m[3]:
            d = m[3]
            self.dob.setDate(QDate(d.year, d.month, d.day))
        self.phone.setText(m[4] or "")
        self.email.setText(m[5] or "")
        self.emergency.setText(m[6] or "")
        self.address.setText(m[7] or "")

        if m[11]: self.weight.setValue(float(m[11]))
        if m[12]: self.height.setValue(float(m[12]))
        self._update_bmi()

        idx = self.goal.findData(m[9])
        if idx >= 0: self.goal.setCurrentIndex(idx)
        self.health.setText(m[10] or "")

        # Branch
        idx = self.branch_cb.findData(m[17])
        if idx >= 0:
            self.branch_cb.setCurrentIndex(idx)
            self._on_branch_changed()

        # Trainer
        if m[18]:
            idx = self.trainer_cb.findData(m[18])
            if idx >= 0: self.trainer_cb.setCurrentIndex(idx)

        # Plan
        if m[19]:
            idx = self.plan_cb.findData(m[19])
            if idx >= 0: self.plan_cb.setCurrentIndex(idx)

        # Status
        idx = self.status_cb.findData(m[16])
        if idx >= 0: self.status_cb.setCurrentIndex(idx)

        # Dates
        if m[14]:
            jd = m[14]
            self.join_date.setDate(QDate(jd.year, jd.month, jd.day))
        if m[15]:
            ed = m[15]
            self.expiry_date.setDate(QDate(ed.year, ed.month, ed.day))

    # ── Validation & Save ─────────────────────────────────────────────────────
    def _validate(self) -> bool:
        valid = True
        self._err_fn.setText("")
        self._err_cnic.setText("")

        if not self.full_name.text().strip():
            self._err_fn.setText("Full name is required.")
            self.full_name.setStyleSheet("border: 1.5px solid #FF2D78;")
            valid = False
        else:
            self.full_name.setStyleSheet("")

        cnic = self.cnic.text().strip()
        if not cnic or not cnic.isdigit() or len(cnic) != 13:
            self._err_cnic.setText("CNIC must be exactly 13 digits.")
            self.cnic.setStyleSheet("border: 1.5px solid #FF2D78;")
            valid = False
        else:
            self.cnic.setStyleSheet("")

        phone = self.phone.text().strip()
        if not phone or not phone.replace("+", "").isdigit() or not (10 <= len(phone.replace("+", "")) <= 15):
            valid = False

        if not self.branch_cb.currentData():
            valid = False

        return valid

    def _save(self):
        if not self._validate():
            InfoDialog("Validation Error",
                       "Please fix the highlighted fields before saving.",
                       "error", self).exec()
            return

        data = {
            "full_name":         self.full_name.text().strip(),
            "cnic":              self.cnic.text().strip(),
            "date_of_birth":     self.dob.date().toPyDate(),
            "phone":             self.phone.text().strip(),
            "email":             self.email.text().strip() or None,
            "emergency_contact": self.emergency.text().strip() or None,
            "address":           self.address.text().strip() or None,
            "weight_kg":         self.weight.value(),
            "height_cm":         self.height.value(),
            "fitness_goal":      self.goal.currentData(),
            "health_conditions": self.health.text().strip() or None,
            "branch_id":         self.branch_cb.currentData(),
            "trainer_id":        self.trainer_cb.currentData(),
            "membership_plan_id":self.plan_cb.currentData(),
            "status":            self.status_cb.currentData(),
            "join_date":         self.join_date.date().toPyDate(),
            "expiry_date":       self.expiry_date.date().toPyDate(),
        }

        if self._is_edit:
            result = member_svc.update_member(self._member_id, data, self._session.user_id)
        else:
            result = member_svc.create_member(data, self._session.user_id)

        dlg = InfoDialog(
            "Saved" if result["success"] else "Error",
            result["message"],
            "success" if result["success"] else "error",
            self
        )
        dlg.exec()
        if result["success"]:
            self.saved.emit()
