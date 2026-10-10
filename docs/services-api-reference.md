# FitLife Services API Reference

This document provides developer reference documentation for the 22 business logic service modules located in `services/`.

---

## Service Architecture Pattern

All service modules follow these design principles:
- **Stateless Operation**: Services instantiate db connection instances from `DatabaseConnection` or thread worker context.
- **Data Encapsulation**: Input parameters are parsed and returned as strongly-typed `@dataclass` entities from `models/` or standard Python dictionaries/lists.
- **Transaction Safety**: Data mutations (`INSERT`, `UPDATE`, `DELETE`) execute within explicit database transactions (`commit()` / `rollback()`).

---

## 1. Authentication & Security Services

### `auth_service.py` (`AuthService`)
Handles user authentication, login validation, session state, and password security.
- `login(username: str, password_plain: str) -> tuple[bool, User | str]`: Validates credentials against Bcrypt hash. Enforces 5-attempt lockout (15-minute cooldown). Resets failed counter on success and returns `(True, User)` or `(False, "Error message")`.
- `hash_password(password: str) -> str`: Generates salt and hashes password with Bcrypt (rounds=12).
- `verify_password(password: str, hashed: str) -> bool`: Checks plain text string against stored hash.
- `check_permission(role_id: int, module: str, action: str) -> bool`: Evaluates role permission matrix (`can_view`, `can_create`, `can_edit`, `can_delete`).
- `change_password(user_id: int, old_pass: str, new_pass: str) -> tuple[bool, str]`: Verifies existing password and updates hash.

### `audit_service.py` (`AuditService`)
Logs security audit records.
- `log_action(user_id: int, action: str, details: str = "", ip_address: str = "127.0.0.1") -> bool`: Appends record to `audit_logs`.
- `get_recent_logs(limit: int = 100, branch_id: int = None) -> list[dict]`: Queries recent audit events.

---

## 2. Membership & Personnel Services

### `member_service.py` (`MemberService`)
Manages gym member lifecycle, registration, and searches.
- `get_all_members(branch_id: int = None, status: str = None) -> list[Member]`: Fetches member directory.
- `get_member_by_id(member_id: int) -> Member | None`: Retrieves single member details.
- `create_member(data: dict) -> tuple[bool, int | str]`: Registers new member, calculates subscription end date based on plan, and creates audit log.
- `update_member(member_id: int, data: dict) -> tuple[bool, str]`: Updates member profile.
- `renew_membership(member_id: int, plan_id: int, payment_method: str) -> tuple[bool, str]`: Extends expiry date and logs payment.
- `freeze_membership(member_id: int, duration_days: int) -> tuple[bool, str]`: Pauses active subscription.

### `trainer_service.py` (`TrainerService`)
Manages gym trainers and assigned client rosters.
- `get_trainers(branch_id: int = None) -> list[Trainer]`: Lists trainers.
- `create_trainer(data: dict) -> tuple[bool, int | str]`: Adds new trainer profile.
- `get_assigned_members(trainer_id: int) -> list[Member]`: Retrieves members assigned to trainer.

### `branch_service.py` (`BranchService`)
Manages gym branch locations.
- `get_all_branches() -> list[Branch]`: Lists branches.
- `create_branch(data: dict) -> tuple[bool, int | str]`: Provisions new branch location.
- `get_branch_stats(branch_id: int) -> dict`: Returns active member count, trainer count, and total revenue.

---

## 3. Financial & Payroll Services

### `billing_service.py` (`BillingService`)
Handles member payments, invoices, and revenue tracking.
- `record_payment(member_id: int, amount: float, method: str, note: str = "") -> tuple[bool, str]`: Generates unique invoice number (`INV-YYYYMMDD-XXXX`), records payment, and updates member balance.
- `get_member_invoices(member_id: int) -> list[Payment]`: Retrieves invoice history.
- `get_financial_summary(start_date: str, end_date: str, branch_id: int = None) -> dict`: Calculates total revenue, pending balances, and breakdown by payment method.

### `salary_service.py` (`SalaryService`)
Manages staff payroll.
- `process_monthly_salary(month_year: str, branch_id: int = None) -> tuple[bool, str]`: Generates salary records for active trainers and staff.
- `pay_salary(salary_id: int, payment_method: str) -> tuple[bool, str]`: Marks salary disbursement as `Paid`.

### `expense_service.py` (`ExpenseService`)
Tracks branch operational expenses (rent, utilities, equipment repairs).
- `add_expense(branch_id: int, category: str, amount: float, description: str) -> tuple[bool, str]`
- `get_expenses(branch_id: int = None, month: str = None) -> list[dict]`

---

## 4. Operational & Health Services

### `attendance_service.py` (`AttendanceService`)
Tracks daily member and trainer check-ins.
- `check_in_member(member_id: int) -> tuple[bool, str]`: Verifies active membership status before recording check-in timestamp.
- `check_out_member(attendance_id: int) -> tuple[bool, str]`: Records check-out timestamp.
- `get_daily_attendance(date: str, branch_id: int = None) -> list[dict]`

### `workout_service.py` (`WorkoutService`)
Manages exercise library and member workout routines.
- `create_workout_plan(member_id: int, trainer_id: int, plan_name: str, exercises: list[dict]) -> tuple[bool, int | str]`
- `get_member_workout(member_id: int) -> dict | None`
- `get_exercise_catalog() -> list[dict]`

### `diet_service.py` (`DietService`)
Manages nutrition and meal plans.
- `create_diet_plan(member_id: int, trainer_id: int, data: dict) -> tuple[bool, int | str]`
- `get_member_diet(member_id: int) -> dict | None`

### `progress_service.py` (`ProgressService`)
Tracks physical transformation metrics.
- `log_progress(member_id: int, weight: float, height: float, body_fat: float = None) -> tuple[bool, str]`: Calculates BMI metrics via `bmi_calculator` and saves progress entry.
- `get_progress_history(member_id: int) -> list[Progress]`

### `equipment_service.py` (`EquipmentService`)
Branch equipment inventory and maintenance schedules.
- `get_equipment(branch_id: int = None) -> list[Equipment]`
- `update_equipment_status(equipment_id: int, status: str) -> tuple[bool, str]`

---

## 5. Analytics, Reporting & AI Services

### `analytics_service.py` (`AnalyticsService`)
Generates executive dashboards and trend charts.
- `get_dashboard_kpis(branch_id: int = None) -> dict`: Returns active members, monthly revenue, attendance counts, and upcoming expirations.
- `get_revenue_trend(months: int = 6) -> list[dict]`

### `reports_service.py` (`ReportsService`)
Exports system data to CSV or printable formats.
- `export_members_csv(file_path: str, branch_id: int = None) -> bool`
- `export_financial_report_csv(file_path: str, start_date: str, end_date: str) -> bool`

### `ai_service.py` (`AIService`)
Integrates **Smart Ask AI** assistant.
- `ask_assistant(prompt: str, user_context: dict) -> str`: Connects to OpenAI or custom LLM backend to answer fitness, workout, diet, or system navigation queries.

### `notification_service.py` (`NotificationService`)
Internal system alert dispatching.
- `create_notification(user_id: int, title: str, message: str) -> bool`
- `get_unread_notifications(user_id: int) -> list[dict]`

### `settings_service.py` (`SettingsService`)
Manages application configuration, branding, and system preferences.
- `get_settings() -> dict`
- `update_settings(new_settings: dict) -> bool`
