# FitLife — Male Fitness Chain Management System

> Production-ready gym ERP built with **PyQt6** + **MS SQL Server** · Phases 1–9 complete

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and configure settings
copy config\settings_template.json config\settings.json
# Edit config/settings.json with your SQL Server connection details

# 3. Create database (run once)
sqlcmd -S YOUR_SERVER -i database/schema.sql
sqlcmd -S YOUR_SERVER -i database/seed_data.sql

# 4. Launch
python main.py
```

---

## Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `Admin@123` |
| Manager (Branch 1) | `manager1` | `Manager@123` |
| Manager (Branch 2) | `manager2` | `Manager@123` |
| Trainer | `trainer1` | `Trainer@123` |
| Member | `member1` | `Member@123` |

---

## Feature Matrix

| Phase | Module | Status |
|-------|--------|--------|
| 1 | Auth (login, RBAC, session, bcrypt) | ✅ |
| 2 | Members, Trainers, Branches, Membership Plans | ✅ |
| 3 | Attendance, Billing, Payments, Salary | ✅ |
| 4 | Workout Plans, Diet Plans, Equipment, Progress | ✅ |
| 5 | Staff Management, Trainer Scheduling | ✅ |
| 6 | Analytics, Reports + CSV, Smart Ask, Diary, Audit Logs | ✅ |
| 7 | Settings (profile, password, notifications, system config, alerts) | ✅ |
| 8 | Global crash handler, rotating logs, input validators, health check | ✅ |
| 9 | Sidebar polish, main.py hardened, full verification | ✅ |

---

## Architecture

```
FitLife/
├── main.py                    # Entry point — logging + crash handler + QApplication
├── app.py                     # FitLifeApp: DB init, login flow, main window
├── config/
│   ├── constants.py           # All app-wide constants
│   ├── settings_template.json # Copy → settings.json and fill credentials
│   └── settings.json          # ⚠ gitignored — contains real DB/API credentials
├── database/
│   ├── connection.py          # Thread-safe connection pool (pyodbc)
│   ├── schema.sql             # Full DB schema (35+ tables, Phases 1–5)
│   └── seed_data.sql          # Demo roles, branches, users, plans
├── services/                  # Business logic layer (16 modules)
│   ├── auth_service.py        # Login, sessions, bcrypt, RBAC
│   ├── member_service.py
│   ├── trainer_service.py
│   ├── branch_service.py
│   ├── billing_service.py
│   ├── salary_service.py
│   ├── attendance_service.py
│   ├── workout_service.py
│   ├── diet_service.py
│   ├── progress_service.py
│   ├── equipment_service.py
│   ├── schedule_service.py
│   ├── staff_service.py
│   ├── analytics_service.py
│   ├── reports_service.py
│   └── settings_service.py
├── ui/
│   ├── theme/                 # ThemeManager: dark/light glassmorphism
│   ├── components/            # Sidebar, TopBar, DataTable, GlassCard, Dialogs, Spinner
│   │   └── icons.py           # Centralized dynamic XML SVG icon engine
│   ├── windows/
│   │   ├── login_window.py    # Animated login window with credentials verification
│   │   └── main_window.py     # Shell: stack of all 19 screens + RBAC gating
│   └── screens/               # 19 feature modules
│       ├── dashboard_placeholder.py
│       ├── members/
│       ├── trainers/
│       ├── branches/
│       ├── billing/
│       ├── attendance/
│       ├── workout_plans/
│       ├── diet_plans/
│       ├── progress/
│       ├── equipment/
│       ├── staff/             # StaffModule + ScheduleModule
│       ├── analytics/         # AnalyticsDashboard + AuditLogsModule
│       ├── reports/
│       ├── smart_ask/
│       ├── diary/
│       └── settings/
├── utils/
│   ├── thread_worker.py       # QThread Worker — keeps UI responsive
│   ├── error_handler.py       # Global crash handler (sys.excepthook)
│   ├── logging_config.py      # Rotating 10MB file log + console
│   ├── validators.py          # Sanitizers + validators for all input types
│   ├── health_check.py        # Startup check: packages, services, DB
│   ├── formatters.py          # Date, currency, name text formatting utilities
│   └── bmi_calculator.py      # Body Mass Index metrics processor
├── models/                    # Dataclass entities mapping database records
│   ├── user.py
│   ├── member.py
│   ├── trainer.py
│   ├── branch.py
│   ├── attendance.py
│   ├── payment.py
│   └── ...
├── logs/                      # Auto-created, rotating log destination
└── reports/                   # CSV export output
```

---

## Security

- Passwords hashed with **bcrypt** (rounds=12) — never stored plain-text
- All SQL uses **parameterized queries** — no string concatenation
- `config/settings.json` is **gitignored** — never committed
- **RBAC** enforced at sidebar, screen-load, service, and query levels
- Account lockout after **5 failed logins** (15-minute cooldown)
- **Session timeout** at 30 minutes inactivity with 5-minute warning

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | PyQt6 (glassmorphism, custom widgets) |
| DB | MS SQL Server 2019+ via pyodbc |
| Auth | bcrypt password hashing |
| Async | QThread Workers (no UI freeze) |
| Logging | Python logging + RotatingFileHandler |
| Export | Built-in csv module (no openpyxl required) |

---

## License

Proprietary — FitLife Gym Management System © 2025
