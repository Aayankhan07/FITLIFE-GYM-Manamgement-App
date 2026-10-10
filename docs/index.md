# FitLife Gym Management System — Documentation Portal

Welcome to the official technical and operational documentation for **FitLife**, a production-ready desktop ERP application tailored for male fitness chains and gym management.

---

## Quick Links

- [Architecture Overview](architecture.md) — Deep dive into system design, layers, threading model, and security architecture.
- [Setup & Installation Guide](setup-guide.md) — Step-by-step instructions for installation, database setup (MS SQL Server & SQLite), configuration, and launch.
- [Database Schema Reference](database-schema.md) — Complete database documentation detailing 35+ tables, schemas, relations, and dual DB engine support.
- [Services API Reference](services-api-reference.md) — Developer documentation for all 22 business logic service modules.
- [User Guide & Manual](user-guide.md) — Step-by-step feature manual for Admin, Manager, Trainer, and Member user roles.
- [Developer Guide](developer-guide.md) — Code style, ThemeManager integration, custom PyQt6 components, QThread patterns, and debugging.
- [UI/UX Modernization Plan](ui-ux-modernization-plan.md) — Comprehensive plan to implement the design and UX from GYM-MANAGEMENT.

---

## Key System Features

- **PyQt6 Modern UI**: Dark glassmorphic theme with custom widgets, smooth responsiveness, scalable vector icons, and custom components.
- **Dual Database Support**: Primary enterprise integration with **MS SQL Server 2019+** via `pyodbc` (with thread-safe connection pooling) and full **SQLite** local fallback mode.
- **Role-Based Access Control (RBAC)**: Fine-grained security permissions for 4 distinct user roles: `Admin`, `Manager`, `Trainer`, and `Member`.
- **Comprehensive Business Modules**:
  - Member management & subscriptions
  - Staff management, payroll & salary processing
  - Trainer scheduling & client assignments
  - Attendance tracking & biometric/manual logging
  - Billing, invoices, payments & financial ledgers
  - Workout plans, exercise libraries & custom routines
  - Nutrition & diet plan management
  - Equipment tracking, maintenance & status monitoring
  - Analytics, dashboard KPIs & automated CSV report exports
  - Smart Ask AI Assistant (integrated via OpenAI/custom API)
  - Audit logging & security tracking
- **Asynchronous Architecture**: Non-blocking background worker threads using `QThread` and signals to maintain dynamic UI responsiveness.

---

## Project Structure Overview

```
FitLife/
├── docs/                      # Technical & User Documentation
├── main.py                    # Application Entry Point & Exception Handler
├── app.py                     # PyQt6 Application Controller & Navigation
├── config/                    # Application Configuration & Constants
├── database/                  # SQL Schemas, Connection Pools & Seed Scripts
├── models/                    # Dataclass Entities Mapping DB Records
├── services/                  # Business Logic Layer (22 Service Modules)
├── ui/                        # PyQt6 Graphical Interface Layer
│   ├── components/            # Reusable UI Widgets & Vector Icons
│   ├── screens/               # 19 Feature Module Views
│   ├── theme/                 # Glassmorphic Styling & Theme Manager
│   └── windows/               # Shell Application Windows
├── utils/                     # Helpers (QThread, Logging, Health Check, Validators)
├── logs/                      # Rotating Log Destination
└── reports/                   # Exported CSV / Financial Reports
```

---

## Maintainers & Licensing

- **License**: Proprietary — FitLife Gym Management System © 2025
- **Version**: 1.0.0
