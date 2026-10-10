# FitLife Installation & Setup Guide

This guide provides step-by-step instructions to install, configure, initialize the database, and run the **FitLife Gym Management System**.

---

## 1. System Requirements

### Hardware Requirements
- **CPU**: Dual-core 2.0 GHz or higher
- **RAM**: 4 GB minimum (8 GB recommended)
- **Disk Space**: 500 MB free storage for application and local logs

### Software Requirements
- **Operating System**: Windows 10/11 (64-bit recommended) or Linux/macOS
- **Python**: Version 3.10, 3.11, or 3.12
- **Database Options**:
  - **MS SQL Server**: 2019 / 2022 / Express Edition with Microsoft ODBC Driver 17 or 18 for SQL Server installed.
  - **SQLite**: Included natively with Python (no external service required).

---

## 2. Installation Steps

### Step 1: Clone or Extract Codebase
Ensure you are in the project root directory:
```bash
cd "d:\PROJECT REPOS\FITLIFE-GYM-Manamgement-App"
```

### Step 2: Create & Activate Virtual Environment
```bash
# Windows (PowerShell / CMD)
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
Install all required Python packages using `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

## 3. Configuration & Settings Setup

Copy `config/settings_template.json` to create `config/settings.json`:

```bash
# Windows (CMD)
copy config\settings_template.json config\settings.json

# Linux / PowerShell
cp config/settings_template.json config/settings.json
```

Edit `config/settings.json` to specify your database engine and credentials:

### Option A: Configuration for MS SQL Server (Enterprise Mode)
```json
{
  "database": {
    "engine": "mssql",
    "server": "localhost",
    "database": "FitLifeDB",
    "username": "sa",
    "password": "YourStrongPassword123!",
    "driver": "ODBC Driver 17 for SQL Server",
    "pool_size": 10
  },
  "app": {
    "theme": "dark_glass",
    "session_timeout_minutes": 30,
    "max_login_attempts": 5
  },
  "ai": {
    "enabled": false,
    "api_key": ""
  }
}
```

### Option B: Configuration for SQLite (Local / Offline Mode)
```json
{
  "database": {
    "engine": "sqlite",
    "database_path": "database/fitlife.db"
  },
  "app": {
    "theme": "dark_glass",
    "session_timeout_minutes": 30,
    "max_login_attempts": 5
  }
}
```

---

## 4. Database Setup & Initialization

### Option A: Setting Up MS SQL Server
Run the schema creation and initial seed scripts against your SQL Server instance:

```bash
# Execute Schema Creation
sqlcmd -S localhost -U sa -P "YourStrongPassword123!" -i database/schema.sql

# Execute Seed Data Insertion
sqlcmd -S localhost -U sa -P "YourStrongPassword123!" -i database/seed_data.sql
```
*(Alternatively, open SQL Server Management Studio (SSMS), execute `database/schema.sql`, then execute `database/seed_data.sql`).*

### Option B: Setting Up SQLite
Run the SQLite initialization scripts using Python or the SQLite CLI:

```bash
# Using Python command line
python -c "import sqlite3; con = sqlite3.connect('database/fitlife.db'); con.executescript(open('database/schema_sqlite.sql').read()); con.executescript(open('database/seed_data_sqlite.sql').read()); con.close()"
```

---

## 5. Launching the Application

Execute `main.py` or double-click `run.bat` (Windows):

```bash
python main.py
```

### Demo Login Credentials

Upon launching, log in using any of the seeded roles:

| Role | Username | Password | Access Scope |
|------|----------|----------|--------------|
| **Admin** | `admin` | `Admin@123` | Full system access across all branches |
| **Manager (Branch 1)** | `manager1` | `Manager@123` | Branch 1 operations, members, staff |
| **Manager (Branch 2)** | `manager2` | `Manager@123` | Branch 2 operations, members, staff |
| **Trainer** | `trainer1` | `Trainer@123` | Assigned members, workouts, diet plans |
| **Member** | `member1` | `Member@123` | Personal profile, workout/diet views |

---

## 6. Troubleshooting Common Issues

### Issue 1: `pyodbc.Error: ('08001', '[08001] [Microsoft][ODBC Driver 17...]')`
- **Cause**: MS SQL Server connection failed or ODBC driver is missing.
- **Solution**:
  1. Verify MS SQL Server service is running in Windows Services (`services.msc`).
  2. Download and install **ODBC Driver 17 for SQL Server** from Microsoft.
  3. Ensure server name and port in `config/settings.json` match SQL Server configuration (e.g. `localhost\\SQLEXPRESS`).

### Issue 2: `PyQt6 qt.qpa.plugin: Could not load the Qt platform plugin "windows"`
- **Cause**: Corrupted PyQt6 installation or environment path conflict.
- **Solution**: Reinstall PyQt6: `pip install --force-reinstall PyQt6`.

### Issue 3: SQLite Database Locked
- **Cause**: Multiple open connections locking the database file.
- **Solution**: Ensure no other processes are inspecting `database/fitlife.db` simultaneously.
