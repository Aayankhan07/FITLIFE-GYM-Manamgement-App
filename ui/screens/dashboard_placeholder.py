"""
FitLife — Dashboard Placeholder
Shows role-specific welcome dashboard with KPI cards.
This is replaced by full dashboards in Phase 7.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QCalendarWidget, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QTextCharFormat, QColor, QFont
from ui.components.glass_card import KPICard, SectionHeader, MutedLabel
from config.constants import ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER


class DashboardPlaceholder(QWidget):
    """Welcome dashboard shown immediately after login."""
    nav_requested = pyqtSignal(str)

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self.setStyleSheet("background: transparent;")
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QWidget { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(24)

        # ── Welcome Header ─────────────────────────────────────────────────────
        header_row = QHBoxLayout()
        greeting = QLabel(f"Welcome back, {self._session.full_name} 👋")
        greeting.setObjectName("heading1")
        header_row.addWidget(greeting)
        header_row.addStretch()

        role_badge = QLabel(f"  {self._session.role}  ")
        role_badge.setStyleSheet(
            "background: rgba(0, 102, 255, 0.2); color: #0066FF;"
            "border: 1px solid #0066FF; border-radius: 12px;"
            "padding: 6px 14px; font-size: 13px; font-weight: bold;"
        )
        header_row.addWidget(role_badge)
        layout.addLayout(header_row)

        sub_lbl = MutedLabel("Here's your FitLife overview for today.")
        layout.addWidget(sub_lbl)

        # ── KPI Cards ─────────────────────────────────────────────────────────
        role = self._session.role
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(16)

        if role == ROLE_ADMIN:
            import services.analytics_service as analytics
            import services.branch_service as branch_svc
            stats = analytics.get_dashboard_kpis(None)
            branches = branch_svc.get_all_branches_dropdown()
            kpis = [
                ("Total Branches",   str(len(branches)),      "🏢", "",    "#0066FF"),
                ("Total Members",    str(stats.get("total_members", 0)),     "👥", "",   "#00F5FF"),
                ("Net Profit",       f"Rs. {stats.get('monthly_profit', 0):,.0f}",  "💰", "",    "#00E676"),
                ("Active Trainers",  str(stats.get("active_trainers", 0)),      "💪", "",         "#FFB800"),
            ]
        elif role == ROLE_MANAGER:
            import services.analytics_service as analytics
            stats = analytics.get_dashboard_kpis(self._session.branch_id)
            kpis = [
                ("Branch Members",   str(stats.get("total_members", 0)),  "👥", "", "#00F5FF"),
                ("Net Profit",       f"Rs. {stats.get('monthly_profit', 0):,.0f}",  "💰", "", "#00E676"),
                ("Attendance Today", str(stats.get("today_attendance", 0)),  "📅", "", "#0066FF"),
                ("Pending Invoices", str(stats.get("pending_payments", 0)),  "📄", "", "#FFB800"),
            ]
        elif role == ROLE_TRAINER:
            import services.trainer_service as t_svc
            import services.attendance_service as att_svc
            from datetime import date
            
            trainer = t_svc.get_trainer_by_user_id(self._session.user_id)
            tid = trainer[0] if trainer else None
            
            assigned_count = "0"
            monthly_days = "0"
            
            if tid:
                members = t_svc.get_assigned_members(tid)
                assigned_count = str(len(members))
                
                today = date.today()
                cal_data = att_svc.get_calendar_data(self._session.branch_id, today.year, today.month, tid, is_trainer=True)
                monthly_days = str(len(cal_data))
                
            kpis = [
                ("Assigned Members", assigned_count, "👥", "", "#0066FF"),
                ("Days Present (Month)", monthly_days, "📅", "", "#00F5FF"),
            ]
        else:  # MEMBER
            kpis = [
                ("Membership Status","Active","💳", "", "#00E676"),
                ("Days Remaining",   "—",    "⏳", "", "#00F5FF"),
                ("Attendance %",     "—",    "📅", "", "#0066FF"),
                ("Current Plan",     "—",    "🏋️","", "#FFB800"),
            ]

        self._cards = []
        for title, value, icon, trend, color in kpis:
            card = KPICard(title, value, icon, trend, color)
            self._cards.append(card)
            kpi_row.addWidget(card)
        layout.addLayout(kpi_row)

        if role == ROLE_TRAINER:
            self._setup_trainer_panels(layout)
        elif role == ROLE_MEMBER:
            self._setup_member_panels(layout)

        # ── Quick Navigation ───────────────────────────────────────────────────
        layout.addSpacing(8)
        quick_lbl = SectionHeader("Quick Actions")
        layout.addWidget(quick_lbl)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(12)

        from PyQt6.QtWidgets import QPushButton
        if role in (ROLE_ADMIN, ROLE_MANAGER):
            actions = [
                ("➕ Add Member",    "members"),
                ("📅 Record Attendance", "attendance"),
                ("💰 Finance Center", "finance"),
                ("📊 View Analytics", "analytics"),
            ]
        elif role == ROLE_TRAINER:
            actions = [
                ("📅 View Attendance", "attendance"),
                ("📈 Log Progress",  "progress"),
                ("⏰ Manage Schedule", "schedule"),
            ]
        else:
            actions = [
                ("🏋️ My Workout",   "workout_plans"),
                ("🥗 My Diet Plan", "diet_plans"),
                ("📅 My Attendance","attendance"),
            ]

        for label, key in actions:
            btn = QPushButton(label)
            btn.setObjectName("btnSecondary")
            btn.setMinimumHeight(46)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self.nav_requested.emit(k))
            quick_row.addWidget(btn)
        layout.addLayout(quick_row)

        # ── System Info Banner ─────────────────────────────────────────────────
        layout.addSpacing(12)
        info_frame = QFrame()
        info_frame.setObjectName("infoBanner")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(20, 16, 20, 16)

        info_lbl = QLabel(
            "ℹ️  FitLife v1.0.0  |  Phase 1 Foundation Complete  |  "
            "Full modules load in Phase 2+  |  Database Connected"
        )
        info_lbl.setObjectName("infoBannerText")
        info_layout.addWidget(info_lbl)
        layout.addWidget(info_frame)

        layout.addStretch()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self):
        role = self._session.role
        if role == ROLE_ADMIN:
            import services.analytics_service as analytics
            import services.branch_service as branch_svc
            stats = analytics.get_dashboard_kpis(None)
            branches = branch_svc.get_all_branches_dropdown()
            if len(self._cards) >= 4:
                self._cards[0].set_value(str(len(branches)))
                self._cards[1].set_value(str(stats.get("total_members", 0)))
                self._cards[2].set_value(f"Rs. {stats.get('monthly_profit', 0):,.0f}")
                self._cards[3].set_value(str(stats.get("active_trainers", 0)))
        elif role == ROLE_MANAGER:
            import services.analytics_service as analytics
            stats = analytics.get_dashboard_kpis(self._session.branch_id)
            if len(self._cards) >= 4:
                self._cards[0].set_value(str(stats.get("total_members", 0)))
                self._cards[1].set_value(f"Rs. {stats.get('monthly_profit', 0):,.0f}")
                self._cards[2].set_value(str(stats.get("today_attendance", 0)))
                self._cards[3].set_value(str(stats.get("pending_payments", 0)))
        elif role == ROLE_TRAINER:
            import services.trainer_service as t_svc
            import services.attendance_service as att_svc
            from datetime import date
            
            trainer = t_svc.get_trainer_by_user_id(self._session.user_id)
            tid = trainer[0] if trainer else None
            
            assigned_count = "0"
            monthly_days = "0"
            if tid:
                members = t_svc.get_assigned_members(tid)
                assigned_count = str(len(members))
                today = date.today()
                cal_data = att_svc.get_calendar_data(self._session.branch_id, today.year, today.month, tid, is_trainer=True)
                monthly_days = str(len(cal_data))
                
            if len(self._cards) >= 2:
                self._cards[0].set_value(assigned_count)
                self._cards[1].set_value(monthly_days)
            self._refresh_trainer_panels()
        elif role == ROLE_MEMBER:
            import services.member_service as m_svc
            import services.attendance_service as att_svc
            from datetime import date
            
            member = m_svc.get_member_by_user_id(self._session.user_id)
            if member:
                status = member[16] # m.status
                expiry = member[15] # m.expiry_date
                plan_name = member[25] # mp.plan_name
                
                days_rem = "—"
                if expiry:
                    diff = (expiry - date.today()).days
                    days_rem = str(max(0, diff))
                    
                today = date.today()
                cal_data = att_svc.get_calendar_data(self._session.branch_id, today.year, today.month, member[0], is_trainer=False)
                att_days = len(cal_data)
                days_passed = today.day
                att_pct = f"{int((att_days / days_passed) * 100)}%" if days_passed > 0 else "0%"
                
                if len(self._cards) >= 4:
                    self._cards[0].set_value(status)
                    self._cards[1].set_value(days_rem)
                    self._cards[2].set_value(att_pct)
                    self._cards[3].set_value(plan_name or "None")
            
            self._refresh_member_panels()

    def _setup_trainer_panels(self, layout):
        layout.addSpacing(16)
        
        # Grid for panels
        grid = QGridLayout()
        grid.setSpacing(20)
        
        # 1. Calendar Panel
        cal_frame = QFrame()
        cal_frame.setStyleSheet("QFrame { background:rgba(255,255,255,0.05); border:1px solid rgba(0, 102, 255, 0.3); border-radius:12px; }")
        cal_layout = QVBoxLayout(cal_frame)
        cal_layout.addWidget(SectionHeader("📅  My Attendance"))
        self.cal_widget = QCalendarWidget()
        self.cal_widget.setStyleSheet("""
            QCalendarWidget QWidget { alternate-background-color: transparent; }
            QCalendarWidget QAbstractItemView:enabled { color: #F0F4FF; background-color: transparent; selection-background-color: #0066FF; }
            QCalendarWidget QToolButton { color: #00F5FF; font-weight: bold; }
        """)
        cal_layout.addWidget(self.cal_widget)
        grid.addWidget(cal_frame, 0, 0)
        
        # 2. Assigned Members & Progress
        mem_frame = QFrame()
        mem_frame.setStyleSheet("QFrame { background:rgba(255,255,255,0.05); border:1px solid rgba(0, 102, 255, 0.3); border-radius:12px; }")
        mem_layout = QVBoxLayout(mem_frame)
        mem_layout.addWidget(SectionHeader("👥  Assigned Members"))
        self.mem_table = QTableWidget()
        self.mem_table.setColumnCount(3)
        self.mem_table.setHorizontalHeaderLabels(["Member Name", "Status", "Goal"])
        self.mem_table.horizontalHeader().setStretchLastSection(True)
        self.mem_table.verticalHeader().setVisible(False)
        self.mem_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.mem_table.setStyleSheet("QTableWidget { background: transparent; color: #F0F4FF; border: none; } QHeaderView::section { background: rgba(0, 102, 255, 0.2); color: #00F5FF; padding: 4px; } QTableWidget::item { padding: 4px; border-bottom: 1px solid rgba(0, 102, 255, 0.1); }")
        mem_layout.addWidget(self.mem_table)
        grid.addWidget(mem_frame, 0, 1)
        
        # 3. Pending Approvals
        app_frame = QFrame()
        app_frame.setStyleSheet("QFrame { background:rgba(255,255,255,0.05); border:1px solid rgba(0, 102, 255, 0.3); border-radius:12px; }")
        app_layout = QVBoxLayout(app_frame)
        app_layout.addWidget(SectionHeader("📋  Pending Approvals"))
        self.app_table = QTableWidget()
        self.app_table.setColumnCount(4)
        self.app_table.setHorizontalHeaderLabels(["Type", "Plan Name", "Member", "Action"])
        self.app_table.horizontalHeader().setStretchLastSection(True)
        self.app_table.verticalHeader().setVisible(False)
        self.app_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.app_table.setStyleSheet("QTableWidget { background: transparent; color: #F0F4FF; border: none; } QHeaderView::section { background: rgba(0, 102, 255, 0.2); color: #FFB800; padding: 4px; } QTableWidget::item { padding: 4px; border-bottom: 1px solid rgba(0, 102, 255, 0.1); }")
        app_layout.addWidget(self.app_table)
        grid.addWidget(app_frame, 1, 0)
        
        # 4. Schedule Panel
        sch_frame = QFrame()
        sch_frame.setStyleSheet("QFrame { background:rgba(255,255,255,0.05); border:1px solid rgba(0, 102, 255, 0.3); border-radius:12px; }")
        sch_layout = QVBoxLayout(sch_frame)
        sch_layout.addWidget(SectionHeader("⏰  My Schedule"))
        self.sch_table = QTableWidget()
        self.sch_table.setColumnCount(3)
        self.sch_table.setHorizontalHeaderLabels(["Time", "Member", "Status"])
        self.sch_table.horizontalHeader().setStretchLastSection(True)
        self.sch_table.verticalHeader().setVisible(False)
        self.sch_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sch_table.setStyleSheet("QTableWidget { background: transparent; color: #F0F4FF; border: none; } QHeaderView::section { background: rgba(0, 102, 255, 0.2); color: #FFB800; padding: 4px; } QTableWidget::item { padding: 4px; border-bottom: 1px solid rgba(0, 102, 255, 0.1); }")
        sch_layout.addWidget(self.sch_table)
        grid.addWidget(sch_frame, 1, 1)
        
        layout.addLayout(grid)

    def _refresh_trainer_panels(self):
        import services.trainer_service as t_svc
        import services.attendance_service as att_svc
        import services.workout_service as workout_svc
        import services.diet_service as diet_svc
        import services.schedule_service as sch_svc
        
        trainer = t_svc.get_trainer_by_user_id(self._session.user_id)
        if not trainer: return
        tid = trainer[0]
        
        # Refresh Calendar
        today = QDate.currentDate()
        cal_data = att_svc.get_calendar_data(self._session.branch_id, today.year(), today.month(), tid, is_trainer=True)
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(0, 230, 118, 100)) # Green highlight
        fmt.setFontWeight(QFont.Weight.Bold)
        for day in cal_data.keys():
            self.cal_widget.setDateTextFormat(QDate(today.year(), today.month(), day), fmt)
            
        # Refresh Members
        members = t_svc.get_assigned_members(tid)
        self.mem_table.setRowCount(0)
        for m in members:
            r = self.mem_table.rowCount()
            self.mem_table.insertRow(r)
            self.mem_table.setItem(r, 0, QTableWidgetItem(m[1]))
            self.mem_table.setItem(r, 1, QTableWidgetItem(m[4]))
            self.mem_table.setItem(r, 2, QTableWidgetItem(m[3] or "—"))
            
        # Refresh Approvals
        from config.constants import PLAN_STATUS_PENDING
        workouts = workout_svc.get_all_plans(trainer_id=tid, status=PLAN_STATUS_PENDING)
        diets = diet_svc.get_all_diet_plans(trainer_id=tid, status=PLAN_STATUS_PENDING)
        
        self.app_table.setRowCount(0)
        
        def add_approval(ptype, plan, approve_fn):
            r = self.app_table.rowCount()
            self.app_table.insertRow(r)
            self.app_table.setItem(r, 0, QTableWidgetItem(ptype))
            self.app_table.setItem(r, 1, QTableWidgetItem(plan[3]))
            self.app_table.setItem(r, 2, QTableWidgetItem(plan[1]))
            btn = QPushButton("✅ Approve")
            btn.setStyleSheet("QPushButton{background:#00E676; color:#000; font-weight:bold; border-radius:4px;} QPushButton:hover{background:#00B248;}")
            btn.clicked.connect(lambda _, pid=plan[0]: self._do_approve(ptype, pid, approve_fn))
            self.app_table.setCellWidget(r, 3, btn)
            
        for w in workouts: add_approval("Workout", w, workout_svc.approve_plan)
        for d in diets: add_approval("Diet", d, diet_svc.approve_diet_plan)
        
        # Refresh Schedule
        today_obj = today.toPyDate() if hasattr(today, 'toPyDate') else today
        schedule = sch_svc.get_schedule(trainer_id=tid, slot_date=today_obj)
        self.sch_table.setRowCount(0)
        for s in schedule:
            r = self.sch_table.rowCount()
            self.sch_table.insertRow(r)
            # time format start - end
            t_str = f"{s[4]} - {s[5]}"
            self.sch_table.setItem(r, 0, QTableWidgetItem(t_str))
            self.sch_table.setItem(r, 1, QTableWidgetItem(s[2] or "Class"))
            self.sch_table.setItem(r, 2, QTableWidgetItem(s[7]))
        
    def _do_approve(self, ptype, pid, approve_fn):
        import services.trainer_service as t_svc
        from ui.components.confirm_dialog import InfoDialog
        trainer = t_svc.get_trainer_by_user_id(self._session.user_id)
        if trainer:
            res = approve_fn(pid, trainer[0])
            InfoDialog("Approval", res["message"], "success" if res["success"] else "error", self).exec()
            if res["success"]:
                self.refresh()

    def _setup_member_panels(self, layout):
        layout.addSpacing(16)
        
        # Grid for panels
        grid = QGridLayout()
        grid.setSpacing(20)
        
        # 1. Calendar Panel
        cal_frame = QFrame()
        cal_frame.setStyleSheet("QFrame { background:rgba(255,255,255,0.05); border:1px solid rgba(0, 102, 255, 0.3); border-radius:12px; }")
        cal_layout = QVBoxLayout(cal_frame)
        cal_layout.addWidget(SectionHeader("📅  My Attendance"))
        self.mem_cal_widget = QCalendarWidget()
        self.mem_cal_widget.setStyleSheet("""
            QCalendarWidget QWidget { alternate-background-color: transparent; }
            QCalendarWidget QAbstractItemView:enabled { color: #F0F4FF; background-color: transparent; selection-background-color: #0066FF; }
            QCalendarWidget QToolButton { color: #00F5FF; font-weight: bold; }
        """)
        cal_layout.addWidget(self.mem_cal_widget)
        grid.addWidget(cal_frame, 0, 0)
        
        # 2. My Workout Plan
        wo_frame = QFrame()
        wo_frame.setStyleSheet("QFrame { background:rgba(255,255,255,0.05); border:1px solid rgba(0, 102, 255, 0.3); border-radius:12px; }")
        wo_layout = QVBoxLayout(wo_frame)
        self.wo_header = SectionHeader("🏋️  My Workout Plan")
        wo_layout.addWidget(self.wo_header)
        self.mem_wo_table = QTableWidget()
        self.mem_wo_table.setColumnCount(4)
        self.mem_wo_table.setHorizontalHeaderLabels(["Exercise", "Sets", "Reps", "Day"])
        self.mem_wo_table.horizontalHeader().setStretchLastSection(True)
        self.mem_wo_table.verticalHeader().setVisible(False)
        self.mem_wo_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.mem_wo_table.setStyleSheet("QTableWidget { background: transparent; color: #F0F4FF; border: none; } QHeaderView::section { background: rgba(0, 102, 255, 0.2); color: #00F5FF; padding: 4px; } QTableWidget::item { padding: 4px; border-bottom: 1px solid rgba(0, 102, 255, 0.1); }")
        wo_layout.addWidget(self.mem_wo_table)
        grid.addWidget(wo_frame, 0, 1)
        
        # 3. My Diet Plan
        dp_frame = QFrame()
        dp_frame.setStyleSheet("QFrame { background:rgba(255,255,255,0.05); border:1px solid rgba(0, 102, 255, 0.3); border-radius:12px; }")
        dp_layout = QVBoxLayout(dp_frame)
        self.dp_header = SectionHeader("🥗  My Diet Plan")
        dp_layout.addWidget(self.dp_header)
        self.mem_dp_table = QTableWidget()
        self.mem_dp_table.setColumnCount(4)
        self.mem_dp_table.setHorizontalHeaderLabels(["Type", "Food Item", "Qty (g)", "Calories"])
        self.mem_dp_table.horizontalHeader().setStretchLastSection(True)
        self.mem_dp_table.verticalHeader().setVisible(False)
        self.mem_dp_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.mem_dp_table.setStyleSheet("QTableWidget { background: transparent; color: #F0F4FF; border: none; } QHeaderView::section { background: rgba(0, 102, 255, 0.2); color: #FFB800; padding: 4px; } QTableWidget::item { padding: 4px; border-bottom: 1px solid rgba(0, 102, 255, 0.1); }")
        dp_layout.addWidget(self.mem_dp_table)
        grid.addWidget(dp_frame, 1, 0, 1, 2)
        
        layout.addLayout(grid)

    def _refresh_member_panels(self):
        import services.member_service as m_svc
        import services.attendance_service as att_svc
        import services.workout_service as workout_svc
        import services.diet_service as diet_svc
        from PyQt6.QtCore import QDate
        from PyQt6.QtGui import QTextCharFormat, QColor, QFont
        
        member = m_svc.get_member_by_user_id(self._session.user_id)
        if not member: return
        mid = member[0]
        
        # Refresh Calendar
        today = QDate.currentDate()
        cal_data = att_svc.get_calendar_data(self._session.branch_id, today.year(), today.month(), mid, is_trainer=False)
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(0, 230, 118, 100)) # Green highlight
        fmt.setFontWeight(QFont.Weight.Bold)
        for day in cal_data.keys():
            self.mem_cal_widget.setDateTextFormat(QDate(today.year(), today.month(), day), fmt)
            
        # Refresh Workout Plan
        workouts = workout_svc.get_all_plans(member_id=mid)
        # Find the active or approved plan
        active_w = next((w for w in workouts if w[6] in ('Active', 'Trainer Approved')), None)
        self.mem_wo_table.setRowCount(0)
        if active_w:
            self.wo_header.setText(f"🏋️  My Workout Plan: {active_w[3]}")
            exercises = workout_svc.get_exercises(active_w[0])
            for ex in exercises:
                r = self.mem_wo_table.rowCount()
                self.mem_wo_table.insertRow(r)
                self.mem_wo_table.setItem(r, 0, QTableWidgetItem(ex[1])) # exercise_name
                self.mem_wo_table.setItem(r, 1, QTableWidgetItem(str(ex[2]))) # sets
                self.mem_wo_table.setItem(r, 2, QTableWidgetItem(str(ex[3]))) # reps
                self.mem_wo_table.setItem(r, 3, QTableWidgetItem(ex[5])) # day_of_week
        else:
            self.wo_header.setText("🏋️  My Workout Plan (No Active Plan)")
            
        # Refresh Diet Plan
        diets = diet_svc.get_all_diet_plans(member_id=mid)
        active_d = next((d for d in diets if d[6] in ('Active', 'Trainer Approved')), None)
        self.mem_dp_table.setRowCount(0)
        if active_d:
            self.dp_header.setText(f"🥗  My Diet Plan: {active_d[3]}")
            meals = diet_svc.get_meals(active_d[0])
            for m in meals:
                r = self.mem_dp_table.rowCount()
                self.mem_dp_table.insertRow(r)
                self.mem_dp_table.setItem(r, 0, QTableWidgetItem(m[1])) # meal_type
                self.mem_dp_table.setItem(r, 1, QTableWidgetItem(m[2])) # food_item
                self.mem_dp_table.setItem(r, 2, QTableWidgetItem(str(m[3]))) # qty
                self.mem_dp_table.setItem(r, 3, QTableWidgetItem(str(m[4]))) # calories
        else:
            self.dp_header.setText("🥗  My Diet Plan (No Active Plan)")
