
-- FitLife Gym Management System — SQLite Schema
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS roles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name   TEXT NOT NULL UNIQUE,
    description TEXT NULL
);

CREATE TABLE IF NOT EXISTS branches (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_name  TEXT NOT NULL,
    city         TEXT NOT NULL,
    address      TEXT NOT NULL,
    phone        TEXT NOT NULL,
    email        TEXT NULL,
    capacity     INTEGER NOT NULL DEFAULT 100,
    opening_date TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active','Closed','Under Renovation')),
    manager_id   INTEGER NULL,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role_id         INTEGER NOT NULL REFERENCES roles(id),
    full_name       TEXT NOT NULL,
    email           TEXT NULL,
    phone           TEXT NULL,
    branch_id       INTEGER NULL REFERENCES branches(id) ON DELETE SET NULL,
    is_active       INTEGER NOT NULL DEFAULT 1,
    last_login      DATETIME NULL,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until    DATETIME NULL,
    theme_pref      TEXT NOT NULL DEFAULT 'dark',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS role_permissions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id     INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    module_name TEXT NOT NULL,
    can_view    INTEGER NOT NULL DEFAULT 0,
    can_create  INTEGER NOT NULL DEFAULT 0,
    can_edit    INTEGER NOT NULL DEFAULT 0,
    can_delete  INTEGER NOT NULL DEFAULT 0,
    UNIQUE (role_id, module_name)
);

CREATE TABLE IF NOT EXISTS membership_plans (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_name     TEXT NOT NULL,
    duration_days INTEGER NOT NULL CHECK (duration_days > 0),
    price         REAL NOT NULL CHECK (price >= 0),
    description   TEXT NULL,
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trainers (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    branch_id          INTEGER NOT NULL REFERENCES branches(id),
    full_name          TEXT NOT NULL,
    cnic               TEXT NOT NULL UNIQUE CHECK (length(cnic) = 13),
    phone              TEXT NOT NULL,
    email              TEXT NULL,
    address            TEXT NULL,
    photo_path         TEXT NULL,
    specialization     TEXT NOT NULL DEFAULT 'General Fitness',
    monthly_salary     REAL NOT NULL CHECK (monthly_salary >= 0),
    hire_date          TEXT NOT NULL,
    qualification      TEXT NULL,
    certifications     TEXT NULL,
    status             TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active','Inactive','On Leave')),
    performance_rating REAL NULL CHECK (performance_rating BETWEEN 0.0 AND 5.0),
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS members (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    branch_id          INTEGER NOT NULL REFERENCES branches(id),
    trainer_id         INTEGER NULL REFERENCES trainers(id) ON DELETE SET NULL,
    full_name          TEXT NOT NULL,
    cnic               TEXT NOT NULL UNIQUE CHECK (length(cnic) = 13),
    date_of_birth      TEXT NOT NULL,
    phone              TEXT NOT NULL,
    email              TEXT NULL,
    emergency_contact  TEXT NULL,
    address            TEXT NULL,
    photo_path         TEXT NULL,
    fitness_goal       TEXT NOT NULL DEFAULT 'Maintenance',
    health_conditions  TEXT NULL,
    weight_kg          REAL NULL CHECK (weight_kg BETWEEN 30.0 AND 300.0),
    height_cm          REAL NULL CHECK (height_cm BETWEEN 100.0 AND 250.0),
    bmi                REAL NULL,
    join_date          TEXT NOT NULL DEFAULT CURRENT_DATE,
    membership_plan_id INTEGER NULL REFERENCES membership_plans(id),
    expiry_date        TEXT NULL,
    status             TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active','Inactive','Suspended','Expired')),
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memberships (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id  INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    plan_id    INTEGER NOT NULL REFERENCES membership_plans(id),
    start_date TEXT NOT NULL,
    end_date   TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active','Expired','Cancelled')),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id      INTEGER NOT NULL REFERENCES members(id),
    membership_id  INTEGER NULL REFERENCES memberships(id),
    amount         REAL NOT NULL CHECK (amount >= 0),
    payment_date   TEXT NOT NULL DEFAULT CURRENT_DATE,
    payment_method TEXT NOT NULL CHECK (payment_method IN ('Cash','Card','Online Transfer','Bank Deposit')),
    status         TEXT NOT NULL DEFAULT 'Unpaid' CHECK (status IN ('Paid','Unpaid','Partial','Overdue')),
    invoice_number TEXT NOT NULL UNIQUE,
    receipt_path   TEXT NULL,
    recorded_by    INTEGER NULL REFERENCES users(id),
    notes          TEXT NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invoices (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id          INTEGER NOT NULL REFERENCES payments(id),
    member_id           INTEGER NOT NULL REFERENCES members(id),
    invoice_number      TEXT NOT NULL UNIQUE,
    amount_due          REAL NOT NULL,
    due_date            TEXT NOT NULL,
    sent_via_email      INTEGER NOT NULL DEFAULT 0,
    sent_via_whatsapp   INTEGER NOT NULL DEFAULT 0,
    sent_at             DATETIME NULL,
    delivery_status     TEXT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS salary_records (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    trainer_id     INTEGER NOT NULL REFERENCES trainers(id),
    month          INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    year           INTEGER NOT NULL CHECK (year >= 2000),
    amount         REAL NOT NULL,
    payment_date   TEXT NULL,
    payment_method TEXT NULL,
    status         TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Paid','Pending')),
    paid_by        INTEGER NULL REFERENCES users(id),
    slip_sent      INTEGER NOT NULL DEFAULT 0,
    bonus          REAL NULL DEFAULT 0,
    deduction      REAL NULL DEFAULT 0,
    net_salary     REAL GENERATED ALWAYS AS (amount + coalesce(bonus,0) - coalesce(deduction,0)) STORED,
    notes          TEXT NULL,
    updated_at     DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (trainer_id, month, year)
);

CREATE TABLE IF NOT EXISTS attendance (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id      INTEGER NULL REFERENCES members(id),
    trainer_id     INTEGER NULL REFERENCES trainers(id),
    branch_id      INTEGER NOT NULL REFERENCES branches(id),
    check_in_time  DATETIME NULL,
    check_out_time DATETIME NULL,
    date           TEXT NOT NULL DEFAULT CURRENT_DATE,
    status         TEXT NOT NULL DEFAULT 'Present' CHECK (status IN ('Present','Absent','Late')),
    recorded_by    INTEGER NULL REFERENCES users(id),
    notes          TEXT NULL
);

CREATE TABLE IF NOT EXISTS workout_plans (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id        INTEGER NOT NULL REFERENCES members(id),
    created_by       INTEGER NOT NULL REFERENCES users(id),
    verified_by      INTEGER NULL REFERENCES users(id),
    plan_name        TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft','Pending Verification','Trainer Approved','Active','Completed','Rejected')),
    ai_generated     INTEGER NOT NULL DEFAULT 0,
    rejection_reason TEXT NULL,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    trainer_id       INTEGER NULL REFERENCES trainers(id),
    weeks            INTEGER NOT NULL DEFAULT 4,
    notes            TEXT NULL,
    goal             TEXT NOT NULL DEFAULT 'General Fitness'
);

CREATE TABLE IF NOT EXISTS workout_plan_exercises (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id       INTEGER NOT NULL REFERENCES workout_plans(id) ON DELETE CASCADE,
    exercise_name TEXT NOT NULL,
    sets          INTEGER NOT NULL DEFAULT 3,
    reps          INTEGER NULL DEFAULT 10,
    rest_seconds  INTEGER NULL DEFAULT 60,
    day_of_week   TEXT NOT NULL DEFAULT 'Monday',
    notes         TEXT NULL,
    order_index   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS diet_plans (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id           INTEGER NOT NULL REFERENCES members(id),
    created_by          INTEGER NOT NULL REFERENCES users(id),
    verified_by         INTEGER NULL REFERENCES users(id),
    plan_name           TEXT NOT NULL,
    duration_weeks      INTEGER NOT NULL DEFAULT 4 CHECK (duration_weeks > 0),
    status              TEXT NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft','Pending Verification','Trainer Approved','Active','Completed','Rejected')),
    ai_generated        INTEGER NOT NULL DEFAULT 0,
    rejection_reason    TEXT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    trainer_id          INTEGER NULL REFERENCES trainers(id),
    daily_calories      INTEGER NOT NULL DEFAULT 2000,
    protein_g           INTEGER NULL DEFAULT 150,
    carbs_g             INTEGER NULL DEFAULT 200,
    fat_g               INTEGER NULL DEFAULT 65,
    notes               TEXT NULL,
    goal                TEXT NOT NULL DEFAULT 'General Fitness'
);

CREATE TABLE IF NOT EXISTS diet_plan_meals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id     INTEGER NOT NULL REFERENCES diet_plans(id) ON DELETE CASCADE,
    meal_type   TEXT NOT NULL,
    food_item   TEXT NOT NULL,
    quantity_g  INTEGER NULL DEFAULT 100,
    calories    INTEGER NULL DEFAULT 0,
    protein_g   REAL NULL DEFAULT 0,
    carbs_g     REAL NULL DEFAULT 0,
    fat_g       REAL NULL DEFAULT 0,
    notes       TEXT NULL
);

CREATE TABLE IF NOT EXISTS equipment (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id             INTEGER NOT NULL REFERENCES branches(id),
    name                  TEXT NOT NULL,
    category              TEXT NOT NULL CHECK (category IN ('Cardio','Strength','Free Weights','Machines','Accessories')),
    quantity              INTEGER NOT NULL DEFAULT 1 CHECK (quantity >= 0),
    purchase_date         TEXT NULL,
    purchase_price        REAL NULL,
    condition             TEXT NOT NULL DEFAULT 'Good' CHECK (condition IN ('New','Good','Fair','Damaged','Retired')),
    status                TEXT NOT NULL DEFAULT 'Active',
    next_maintenance_date TEXT NULL,
    created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    equipment_name        TEXT NOT NULL DEFAULT '',
    brand                 TEXT NULL,
    model                 TEXT NULL,
    serial_number         TEXT NULL,
    condition_status      TEXT NOT NULL DEFAULT 'Good',
    last_maintenance_date TEXT NULL,
    notes                 TEXT NULL
);

CREATE TABLE IF NOT EXISTS maintenance_records (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    date         TEXT NOT NULL,
    description  TEXT NOT NULL,
    cost         REAL NULL,
    performed_by TEXT NULL,
    status       TEXT NOT NULL DEFAULT 'Completed',
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS progress_records (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id          INTEGER NOT NULL REFERENCES members(id),
    trainer_id         INTEGER NULL REFERENCES trainers(id),
    record_date        TEXT NOT NULL DEFAULT CURRENT_DATE,
    weight_kg          REAL NULL,
    bmi                REAL NULL,
    body_fat_pct       REAL NULL,
    chest_cm           REAL NULL,
    waist_cm           REAL NULL,
    arm_cm             REAL NULL,
    bench_press_max_kg REAL NULL,
    squat_max_kg       REAL NULL,
    notes              TEXT NULL,
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staff (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id   INTEGER NOT NULL REFERENCES branches(id),
    full_name   TEXT NOT NULL,
    role        TEXT NOT NULL,
    phone       TEXT NULL,
    email       TEXT NULL,
    shift_start TEXT NULL,
    shift_end   TEXT NULL,
    hire_date   TEXT NULL,
    salary      REAL NULL,
    status      TEXT NOT NULL DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS schedules (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id    INTEGER NOT NULL REFERENCES branches(id),
    staff_id     INTEGER NULL REFERENCES staff(id),
    trainer_id   INTEGER NULL REFERENCES trainers(id),
    day_of_week  TEXT NOT NULL,
    start_time   TEXT NOT NULL,
    end_time     TEXT NOT NULL,
    session_type TEXT NULL,
    notes        TEXT NULL
);

CREATE TABLE IF NOT EXISTS diary_entries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title      TEXT NOT NULL,
    body       TEXT NOT NULL,
    entry_date TEXT NOT NULL DEFAULT CURRENT_DATE,
    tags       TEXT NULL,
    is_pinned  INTEGER NOT NULL DEFAULT 0,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS smart_ask_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question   TEXT NOT NULL,
    answer     TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    action     TEXT NOT NULL,
    module     TEXT NULL,
    record_id  INTEGER NULL,
    old_value  TEXT NULL,
    new_value  TEXT NULL,
    ip_address TEXT NULL,
    timestamp  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    activity  TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details   TEXT NULL
);

CREATE TABLE IF NOT EXISTS notification_settings (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id              INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    email_notifications  INTEGER NOT NULL DEFAULT 1,
    whatsapp_notifications INTEGER NOT NULL DEFAULT 1,
    phone_number         TEXT NULL,
    email                TEXT NULL
);

CREATE TABLE IF NOT EXISTS system_settings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key   TEXT NOT NULL UNIQUE,
    setting_value TEXT NULL,
    description   TEXT NULL
);

CREATE TABLE IF NOT EXISTS trainer_schedule (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id   INTEGER NOT NULL REFERENCES branches(id),
    trainer_id  INTEGER NOT NULL REFERENCES trainers(id),
    member_id   INTEGER NULL REFERENCES members(id) ON DELETE SET NULL,
    slot_date   TEXT NOT NULL,
    start_time  TEXT NOT NULL,
    end_time    TEXT NOT NULL,
    class_type  TEXT NOT NULL DEFAULT 'Personal Training',
    status      TEXT NOT NULL DEFAULT 'Available' CHECK (status IN ('Available','Booked','Cancelled','Completed')),
    notes       TEXT NULL,
    created_by  INTEGER NULL REFERENCES users(id),
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS progress_logs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id    INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    log_date     TEXT NOT NULL DEFAULT CURRENT_DATE,
    weight_kg    REAL NULL,
    body_fat_pct REAL NULL,
    chest_cm     REAL NULL,
    waist_cm     REAL NULL,
    hips_cm      REAL NULL,
    arms_cm      REAL NULL,
    legs_cm      REAL NULL,
    notes        TEXT NULL,
    logged_by    INTEGER NULL REFERENCES users(id),
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS expenses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id    INTEGER NOT NULL REFERENCES branches(id),
    category     TEXT NOT NULL,
    amount       REAL NOT NULL CHECK (amount >= 0),
    expense_date TEXT NOT NULL,
    description  TEXT NULL,
    recorded_by  INTEGER NULL REFERENCES users(id),
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_members_branch    ON members(branch_id);
CREATE INDEX IF NOT EXISTS idx_members_status    ON members(status);
CREATE INDEX IF NOT EXISTS idx_attendance_member ON attendance(member_id);
CREATE INDEX IF NOT EXISTS idx_attendance_date   ON attendance(date);
CREATE INDEX IF NOT EXISTS idx_payments_member   ON payments(member_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp   ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_sched_date        ON trainer_schedule(slot_date);
CREATE INDEX IF NOT EXISTS idx_progress_member   ON progress_logs(member_id);
