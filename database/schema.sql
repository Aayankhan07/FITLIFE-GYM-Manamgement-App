-- ============================================================
-- FitLife Gym Management System — Full Database Schema
-- MS SQL Server 2019+
-- ============================================================

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'FitLifeDB')
BEGIN
    CREATE DATABASE FitLifeDB;
END
GO

USE FitLifeDB;
GO

-- ─── ROLES ────────────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'roles')
CREATE TABLE roles (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    role_name   NVARCHAR(50)  NOT NULL UNIQUE,
    description NVARCHAR(255) NULL
);
GO

-- ─── BRANCHES ─────────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'branches')
CREATE TABLE branches (
    id           INT IDENTITY(1,1) PRIMARY KEY,
    branch_name  NVARCHAR(100) NOT NULL,
    city         NVARCHAR(100) NOT NULL,
    address      NVARCHAR(255) NOT NULL,
    phone        NVARCHAR(20)  NOT NULL,
    email        NVARCHAR(150) NULL,
    capacity     INT           NOT NULL DEFAULT 100,
    opening_date DATE          NOT NULL,
    status       NVARCHAR(30)  NOT NULL DEFAULT 'Active'
                     CHECK (status IN ('Active','Closed','Under Renovation')),
    manager_id   INT           NULL,
    created_at   DATETIME2     NOT NULL DEFAULT GETDATE(),
    updated_at   DATETIME2     NOT NULL DEFAULT GETDATE()
);
GO

-- ─── USERS ────────────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
CREATE TABLE users (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    username        NVARCHAR(100) NOT NULL UNIQUE,
    password_hash   NVARCHAR(255) NOT NULL,
    role_id         INT           NOT NULL REFERENCES roles(id),
    full_name       NVARCHAR(150) NOT NULL,
    email           NVARCHAR(150) NULL,
    phone           NVARCHAR(20)  NULL,
    branch_id       INT           NULL REFERENCES branches(id) ON DELETE SET NULL,
    is_active       BIT           NOT NULL DEFAULT 1,
    last_login      DATETIME2     NULL,
    failed_attempts INT           NOT NULL DEFAULT 0,
    locked_until    DATETIME2     NULL,
    theme_pref      NVARCHAR(10)  NOT NULL DEFAULT 'dark',
    created_at      DATETIME2     NOT NULL DEFAULT GETDATE(),
    updated_at      DATETIME2     NOT NULL DEFAULT GETDATE()
);
GO

-- Add FK from branches.manager_id → users.id (after users created)
IF NOT EXISTS (
    SELECT * FROM sys.foreign_keys WHERE name = 'FK_branches_manager'
)
ALTER TABLE branches
    ADD CONSTRAINT FK_branches_manager FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE SET NULL;
GO

-- ─── ROLE PERMISSIONS ─────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'role_permissions')
CREATE TABLE role_permissions (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    role_id     INT          NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    module_name NVARCHAR(60) NOT NULL,
    can_view    BIT          NOT NULL DEFAULT 0,
    can_create  BIT          NOT NULL DEFAULT 0,
    can_edit    BIT          NOT NULL DEFAULT 0,
    can_delete  BIT          NOT NULL DEFAULT 0,
    UNIQUE (role_id, module_name)
);
GO

-- ─── MEMBERSHIP PLANS ─────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'membership_plans')
CREATE TABLE membership_plans (
    id            INT IDENTITY(1,1) PRIMARY KEY,
    plan_name     NVARCHAR(100) NOT NULL,
    duration_days INT           NOT NULL CHECK (duration_days > 0),
    price         DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    description   NVARCHAR(500) NULL,
    is_active     BIT           NOT NULL DEFAULT 1,
    created_at    DATETIME2     NOT NULL DEFAULT GETDATE()
);
GO

-- ─── TRAINERS ─────────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'trainers')
CREATE TABLE trainers (
    id               INT IDENTITY(1,1) PRIMARY KEY,
    user_id          INT           NULL REFERENCES users(id) ON DELETE SET NULL,
    branch_id        INT           NOT NULL REFERENCES branches(id),
    full_name        NVARCHAR(150) NOT NULL,
    cnic             NVARCHAR(13)  NOT NULL UNIQUE CHECK (LEN(cnic) = 13),
    phone            NVARCHAR(20)  NOT NULL,
    email            NVARCHAR(150) NULL,
    address          NVARCHAR(255) NULL,
    photo_path       NVARCHAR(300) NULL,
    specialization   NVARCHAR(60)  NOT NULL DEFAULT 'General Fitness',
    monthly_salary   DECIMAL(10,2) NOT NULL CHECK (monthly_salary >= 0),
    hire_date        DATE          NOT NULL,
    qualification    NVARCHAR(150) NULL,
    certifications   NVARCHAR(500) NULL,
    status           NVARCHAR(20)  NOT NULL DEFAULT 'Active'
                         CHECK (status IN ('Active','Inactive','On Leave')),
    performance_rating DECIMAL(3,1) NULL CHECK (performance_rating BETWEEN 0 AND 5),
    created_at       DATETIME2     NOT NULL DEFAULT GETDATE(),
    updated_at       DATETIME2     NOT NULL DEFAULT GETDATE()
);
GO

-- ─── MEMBERS ──────────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'members')
CREATE TABLE members (
    id                 INT IDENTITY(1,1) PRIMARY KEY,
    user_id            INT           NULL REFERENCES users(id) ON DELETE SET NULL,
    branch_id          INT           NOT NULL REFERENCES branches(id),
    trainer_id         INT           NULL REFERENCES trainers(id) ON DELETE SET NULL,
    full_name          NVARCHAR(150) NOT NULL,
    cnic               NVARCHAR(13)  NOT NULL UNIQUE CHECK (LEN(cnic) = 13),
    date_of_birth      DATE          NOT NULL,
    phone              NVARCHAR(20)  NOT NULL,
    email              NVARCHAR(150) NULL,
    emergency_contact  NVARCHAR(20)  NULL,
    address            NVARCHAR(255) NULL,
    photo_path         NVARCHAR(300) NULL,
    fitness_goal       NVARCHAR(50)  NOT NULL DEFAULT 'Maintenance',
    health_conditions  NVARCHAR(500) NULL,
    weight_kg          DECIMAL(5,1)  NULL CHECK (weight_kg BETWEEN 30 AND 300),
    height_cm          DECIMAL(5,1)  NULL CHECK (height_cm BETWEEN 100 AND 250),
    bmi                DECIMAL(4,1)  NULL,
    join_date          DATE          NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    membership_plan_id INT           NULL REFERENCES membership_plans(id),
    expiry_date        DATE          NULL,
    status             NVARCHAR(20)  NOT NULL DEFAULT 'Active'
                           CHECK (status IN ('Active','Inactive','Suspended','Expired')),
    created_at         DATETIME2     NOT NULL DEFAULT GETDATE(),
    updated_at         DATETIME2     NOT NULL DEFAULT GETDATE()
);
GO

-- ─── MEMBERSHIPS ──────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'memberships')
CREATE TABLE memberships (
    id         INT IDENTITY(1,1) PRIMARY KEY,
    member_id  INT          NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    plan_id    INT          NOT NULL REFERENCES membership_plans(id),
    start_date DATE         NOT NULL,
    end_date   DATE         NOT NULL,
    status     NVARCHAR(20) NOT NULL DEFAULT 'Active'
                   CHECK (status IN ('Active','Expired','Cancelled')),
    created_at DATETIME2    NOT NULL DEFAULT GETDATE()
);
GO

-- ─── PAYMENTS ─────────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'payments')
CREATE TABLE payments (
    id             INT IDENTITY(1,1) PRIMARY KEY,
    member_id      INT           NOT NULL REFERENCES members(id),
    membership_id  INT           NULL REFERENCES memberships(id),
    amount         DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
    payment_date   DATE          NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    payment_method NVARCHAR(30)  NOT NULL
                       CHECK (payment_method IN ('Cash','Card','Online Transfer','Bank Deposit')),
    status         NVARCHAR(20)  NOT NULL DEFAULT 'Unpaid'
                       CHECK (status IN ('Paid','Unpaid','Partial','Overdue')),
    invoice_number NVARCHAR(50)  NOT NULL UNIQUE,
    receipt_path   NVARCHAR(300) NULL,
    recorded_by    INT           NULL REFERENCES users(id),
    notes          NVARCHAR(500) NULL,
    created_at     DATETIME2     NOT NULL DEFAULT GETDATE()
);
GO

-- ─── INVOICES ─────────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'invoices')
CREATE TABLE invoices (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    payment_id          INT           NOT NULL REFERENCES payments(id),
    member_id           INT           NOT NULL REFERENCES members(id),
    invoice_number      NVARCHAR(50)  NOT NULL UNIQUE,
    amount_due          DECIMAL(10,2) NOT NULL,
    due_date            DATE          NOT NULL,
    sent_via_email      BIT           NOT NULL DEFAULT 0,
    sent_via_whatsapp   BIT           NOT NULL DEFAULT 0,
    sent_at             DATETIME2     NULL,
    delivery_status     NVARCHAR(50)  NULL,
    created_at          DATETIME2     NOT NULL DEFAULT GETDATE()
);
GO

-- ─── SALARY RECORDS ───────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'salary_records')
CREATE TABLE salary_records (
    id             INT IDENTITY(1,1) PRIMARY KEY,
    trainer_id     INT           NOT NULL REFERENCES trainers(id),
    month          INT           NOT NULL CHECK (month BETWEEN 1 AND 12),
    year           INT           NOT NULL CHECK (year >= 2000),
    amount         DECIMAL(10,2) NOT NULL,
    payment_date   DATE          NULL,
    payment_method NVARCHAR(30)  NULL,
    status         NVARCHAR(20)  NOT NULL DEFAULT 'Pending'
                       CHECK (status IN ('Paid','Pending')),
    paid_by        INT           NULL REFERENCES users(id),
    slip_sent      BIT           NOT NULL DEFAULT 0,
    created_at     DATETIME2     NOT NULL DEFAULT GETDATE(),
    UNIQUE (trainer_id, month, year)
);
GO

-- ─── ATTENDANCE ───────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'attendance')
CREATE TABLE attendance (
    id            INT IDENTITY(1,1) PRIMARY KEY,
    member_id     INT          NOT NULL REFERENCES members(id),
    branch_id     INT          NOT NULL REFERENCES branches(id),
    check_in_time DATETIME2    NULL,
    check_out_time DATETIME2   NULL,
    date          DATE         NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    status        NVARCHAR(20) NOT NULL DEFAULT 'Present'
                      CHECK (status IN ('Present','Absent','Late')),
    recorded_by   INT          NULL REFERENCES users(id),
    notes         NVARCHAR(255) NULL
);
GO

-- ─── WORKOUT PLANS ────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'workout_plans')
CREATE TABLE workout_plans (
    id               INT IDENTITY(1,1) PRIMARY KEY,
    member_id        INT           NOT NULL REFERENCES members(id),
    created_by       INT           NOT NULL REFERENCES users(id),
    verified_by      INT           NULL REFERENCES users(id),
    plan_name        NVARCHAR(150) NOT NULL,
    goal             NVARCHAR(50)  NOT NULL,
    duration_weeks   INT           NOT NULL DEFAULT 4 CHECK (duration_weeks > 0),
    status           NVARCHAR(30)  NOT NULL DEFAULT 'Draft'
                         CHECK (status IN ('Draft','Pending Verification','Trainer Approved','Active','Completed','Rejected')),
    ai_generated     BIT           NOT NULL DEFAULT 0,
    rejection_reason NVARCHAR(500) NULL,
    created_at       DATETIME2     NOT NULL DEFAULT GETDATE(),
    updated_at       DATETIME2     NOT NULL DEFAULT GETDATE()
);
GO

-- ─── WORKOUT EXERCISES ────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'workout_exercises')
CREATE TABLE workout_exercises (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    workout_plan_id INT           NOT NULL REFERENCES workout_plans(id) ON DELETE CASCADE,
    day_of_week     NVARCHAR(15)  NOT NULL,
    exercise_name   NVARCHAR(150) NOT NULL,
    sets            INT           NOT NULL DEFAULT 3 CHECK (sets > 0),
    reps            INT           NULL,
    rest_seconds    INT           NULL DEFAULT 60,
    duration_mins   INT           NULL,
    weight_kg       DECIMAL(5,1)  NULL,
    notes           NVARCHAR(300) NULL,
    order_index     INT           NOT NULL DEFAULT 1
);
GO

-- ─── DIET PLANS ───────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'diet_plans')
CREATE TABLE diet_plans (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    member_id           INT           NOT NULL REFERENCES members(id),
    created_by          INT           NOT NULL REFERENCES users(id),
    verified_by         INT           NULL REFERENCES users(id),
    plan_name           NVARCHAR(150) NOT NULL,
    goal                NVARCHAR(50)  NOT NULL,
    total_daily_calories INT          NOT NULL CHECK (total_daily_calories > 0),
    protein_g           INT           NOT NULL DEFAULT 0,
    carbs_g             INT           NOT NULL DEFAULT 0,
    fats_g              INT           NOT NULL DEFAULT 0,
    duration_weeks      INT           NOT NULL DEFAULT 4 CHECK (duration_weeks > 0),
    status              NVARCHAR(30)  NOT NULL DEFAULT 'Draft'
                            CHECK (status IN ('Draft','Pending Verification','Trainer Approved','Active','Completed','Rejected')),
    ai_generated        BIT           NOT NULL DEFAULT 0,
    rejection_reason    NVARCHAR(500) NULL,
    created_at          DATETIME2     NOT NULL DEFAULT GETDATE(),
    updated_at          DATETIME2     NOT NULL DEFAULT GETDATE()
);
GO

-- ─── DIET MEALS ───────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'diet_meals')
CREATE TABLE diet_meals (
    id           INT IDENTITY(1,1) PRIMARY KEY,
    diet_plan_id INT           NOT NULL REFERENCES diet_plans(id) ON DELETE CASCADE,
    meal_type    NVARCHAR(30)  NOT NULL,
    food_items   NVARCHAR(500) NOT NULL,
    portion_size NVARCHAR(100) NULL,
    calories     INT           NULL,
    protein_g    DECIMAL(6,1)  NULL,
    carbs_g      DECIMAL(6,1)  NULL,
    fats_g       DECIMAL(6,1)  NULL,
    notes        NVARCHAR(300) NULL
);
GO

-- ─── EQUIPMENT ────────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'equipment')
CREATE TABLE equipment (
    id                    INT IDENTITY(1,1) PRIMARY KEY,
    branch_id             INT           NOT NULL REFERENCES branches(id),
    name                  NVARCHAR(150) NOT NULL,
    category              NVARCHAR(50)  NOT NULL
                              CHECK (category IN ('Cardio','Strength','Free Weights','Machines','Accessories')),
    quantity              INT           NOT NULL DEFAULT 1 CHECK (quantity >= 0),
    purchase_date         DATE          NULL,
    purchase_price        DECIMAL(10,2) NULL,
    condition             NVARCHAR(20)  NOT NULL DEFAULT 'Good'
                              CHECK (condition IN ('New','Good','Fair','Damaged','Retired')),
    status                NVARCHAR(20)  NOT NULL DEFAULT 'Active',
    next_maintenance_date DATE          NULL,
    created_at            DATETIME2     NOT NULL DEFAULT GETDATE(),
    updated_at            DATETIME2     NOT NULL DEFAULT GETDATE()
);
GO

-- ─── MAINTENANCE RECORDS ──────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'maintenance_records')
CREATE TABLE maintenance_records (
    id           INT IDENTITY(1,1) PRIMARY KEY,
    equipment_id INT           NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    date         DATE          NOT NULL,
    description  NVARCHAR(500) NOT NULL,
    cost         DECIMAL(10,2) NULL,
    performed_by NVARCHAR(150) NULL,
    status       NVARCHAR(30)  NOT NULL DEFAULT 'Completed',
    created_at   DATETIME2     NOT NULL DEFAULT GETDATE()
);
GO

-- ─── PROGRESS RECORDS ─────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'progress_records')
CREATE TABLE progress_records (
    id                 INT IDENTITY(1,1) PRIMARY KEY,
    member_id          INT           NOT NULL REFERENCES members(id),
    trainer_id         INT           NULL REFERENCES trainers(id),
    record_date        DATE          NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    weight_kg          DECIMAL(5,1)  NULL,
    bmi                DECIMAL(4,1)  NULL,
    body_fat_pct       DECIMAL(4,1)  NULL,
    chest_cm           DECIMAL(5,1)  NULL,
    waist_cm           DECIMAL(5,1)  NULL,
    arm_cm             DECIMAL(5,1)  NULL,
    bench_press_max_kg DECIMAL(5,1)  NULL,
    squat_max_kg       DECIMAL(5,1)  NULL,
    notes              NVARCHAR(500) NULL,
    created_at         DATETIME2     NOT NULL DEFAULT GETDATE()
);
GO

-- ─── STAFF ────────────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'staff')
CREATE TABLE staff (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    branch_id   INT           NOT NULL REFERENCES branches(id),
    full_name   NVARCHAR(150) NOT NULL,
    role        NVARCHAR(80)  NOT NULL,
    phone       NVARCHAR(20)  NULL,
    email       NVARCHAR(150) NULL,
    shift_start TIME          NULL,
    shift_end   TIME          NULL,
    hire_date   DATE          NULL,
    salary      DECIMAL(10,2) NULL,
    status      NVARCHAR(20)  NOT NULL DEFAULT 'Active'
);
GO

-- ─── SCHEDULES ────────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'schedules')
CREATE TABLE schedules (
    id           INT IDENTITY(1,1) PRIMARY KEY,
    branch_id    INT          NOT NULL REFERENCES branches(id),
    staff_id     INT          NULL REFERENCES staff(id),
    trainer_id   INT          NULL REFERENCES trainers(id),
    day_of_week  NVARCHAR(15) NOT NULL,
    start_time   TIME         NOT NULL,
    end_time     TIME         NOT NULL,
    session_type NVARCHAR(60) NULL,
    notes        NVARCHAR(300) NULL
);
GO

-- ─── DIARY ENTRIES ────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'diary_entries')
CREATE TABLE diary_entries (
    id         INT IDENTITY(1,1) PRIMARY KEY,
    user_id    INT           NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title      NVARCHAR(200) NOT NULL,
    body       NVARCHAR(MAX) NOT NULL,
    entry_date DATE          NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    tags       NVARCHAR(100) NULL,
    is_pinned  BIT           NOT NULL DEFAULT 0,
    is_deleted BIT           NOT NULL DEFAULT 0,
    created_at DATETIME2     NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2     NOT NULL DEFAULT GETDATE()
);
GO

-- ─── SMART ASK LOGS ───────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'smart_ask_logs')
CREATE TABLE smart_ask_logs (
    id         INT IDENTITY(1,1) PRIMARY KEY,
    user_id    INT           NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question   NVARCHAR(MAX) NOT NULL,
    answer     NVARCHAR(MAX) NOT NULL,
    created_at DATETIME2     NOT NULL DEFAULT GETDATE()
);
GO

-- ─── AUDIT LOGS ───────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'audit_logs')
CREATE TABLE audit_logs (
    id         INT IDENTITY(1,1) PRIMARY KEY,
    user_id    INT           NULL REFERENCES users(id) ON DELETE SET NULL,
    action     NVARCHAR(50)  NOT NULL,
    module     NVARCHAR(60)  NULL,
    record_id  INT           NULL,
    old_value  NVARCHAR(MAX) NULL,
    new_value  NVARCHAR(MAX) NULL,
    ip_address NVARCHAR(45)  NULL,
    timestamp  DATETIME2     NOT NULL DEFAULT GETDATE()
);
GO

-- ─── ACTIVITY LOGS ────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'activity_logs')
CREATE TABLE activity_logs (
    id        INT IDENTITY(1,1) PRIMARY KEY,
    user_id   INT           NULL REFERENCES users(id) ON DELETE SET NULL,
    activity  NVARCHAR(150) NOT NULL,
    timestamp DATETIME2     NOT NULL DEFAULT GETDATE(),
    details   NVARCHAR(MAX) NULL
);
GO

-- ─── NOTIFICATION SETTINGS ────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'notification_settings')
CREATE TABLE notification_settings (
    id                   INT IDENTITY(1,1) PRIMARY KEY,
    user_id              INT          NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    email_notifications  BIT          NOT NULL DEFAULT 1,
    whatsapp_notifications BIT        NOT NULL DEFAULT 1,
    phone_number         NVARCHAR(20) NULL,
    email                NVARCHAR(150) NULL
);
GO

-- ─── SYSTEM SETTINGS ──────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'system_settings')
CREATE TABLE system_settings (
    id            INT IDENTITY(1,1) PRIMARY KEY,
    setting_key   NVARCHAR(100) NOT NULL UNIQUE,
    setting_value NVARCHAR(MAX) NULL,
    description   NVARCHAR(300) NULL
);
GO

-- ─── TRAINER SCHEDULE (Phase 5) ───────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'trainer_schedule')
CREATE TABLE trainer_schedule (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    branch_id   INT          NOT NULL REFERENCES branches(id),
    trainer_id  INT          NOT NULL REFERENCES trainers(id),
    member_id   INT          NULL REFERENCES members(id) ON DELETE SET NULL,
    slot_date   DATE         NOT NULL,
    start_time  TIME         NOT NULL,
    end_time    TIME         NOT NULL,
    class_type  NVARCHAR(60) NOT NULL DEFAULT 'Personal Training',
    status      NVARCHAR(20) NOT NULL DEFAULT 'Available'
                    CHECK (status IN ('Available','Booked','Cancelled','Completed')),
    notes       NVARCHAR(300) NULL,
    created_by  INT          NULL REFERENCES users(id),
    created_at  DATETIME2    NOT NULL DEFAULT GETDATE(),
    updated_at  DATETIME2    NOT NULL DEFAULT GETDATE()
);
GO

-- ─── WORKOUT PLAN EXERCISES (aliases workout_exercises → workout_plan_exercises) ──
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'workout_plan_exercises')
CREATE TABLE workout_plan_exercises (
    id            INT IDENTITY(1,1) PRIMARY KEY,
    plan_id       INT           NOT NULL REFERENCES workout_plans(id) ON DELETE CASCADE,
    exercise_name NVARCHAR(150) NOT NULL,
    sets          INT           NOT NULL DEFAULT 3,
    reps          INT           NULL DEFAULT 10,
    rest_seconds  INT           NULL DEFAULT 60,
    day_of_week   NVARCHAR(15)  NOT NULL DEFAULT 'Monday',
    notes         NVARCHAR(300) NULL,
    order_index   INT           NOT NULL DEFAULT 0
);
GO

-- Add missing columns to workout_plans if they don't exist
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('workout_plans') AND name='trainer_id')
    ALTER TABLE workout_plans ADD trainer_id INT NULL REFERENCES trainers(id);
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('workout_plans') AND name='weeks')
    ALTER TABLE workout_plans ADD weeks INT NOT NULL DEFAULT 4;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('workout_plans') AND name='notes')
    ALTER TABLE workout_plans ADD notes NVARCHAR(MAX) NULL;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('workout_plans') AND name='goal')
    ALTER TABLE workout_plans ADD goal NVARCHAR(60) NOT NULL DEFAULT 'General Fitness';
GO

-- ─── DIET PLAN MEALS (aliases diet_meals → diet_plan_meals) ──────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'diet_plan_meals')
CREATE TABLE diet_plan_meals (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    plan_id     INT           NOT NULL REFERENCES diet_plans(id) ON DELETE CASCADE,
    meal_type   NVARCHAR(40)  NOT NULL,
    food_item   NVARCHAR(200) NOT NULL,
    quantity_g  INT           NULL DEFAULT 100,
    calories    INT           NULL DEFAULT 0,
    protein_g   DECIMAL(6,1)  NULL DEFAULT 0,
    carbs_g     DECIMAL(6,1)  NULL DEFAULT 0,
    fat_g       DECIMAL(6,1)  NULL DEFAULT 0,
    notes       NVARCHAR(300) NULL
);
GO

-- Add missing columns to diet_plans
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('diet_plans') AND name='trainer_id')
    ALTER TABLE diet_plans ADD trainer_id INT NULL REFERENCES trainers(id);
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('diet_plans') AND name='daily_calories')
    ALTER TABLE diet_plans ADD daily_calories INT NOT NULL DEFAULT 2000;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('diet_plans') AND name='protein_g')
    ALTER TABLE diet_plans ADD protein_g INT NULL DEFAULT 150;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('diet_plans') AND name='carbs_g')
    ALTER TABLE diet_plans ADD carbs_g INT NULL DEFAULT 200;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('diet_plans') AND name='fat_g')
    ALTER TABLE diet_plans ADD fat_g INT NULL DEFAULT 65;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('diet_plans') AND name='notes')
    ALTER TABLE diet_plans ADD notes NVARCHAR(MAX) NULL;
GO

-- ─── PROGRESS LOGS ────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'progress_logs')
CREATE TABLE progress_logs (
    id           INT IDENTITY(1,1) PRIMARY KEY,
    member_id    INT          NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    log_date     DATE         NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    weight_kg    DECIMAL(5,1) NULL,
    body_fat_pct DECIMAL(4,1) NULL,
    chest_cm     DECIMAL(5,1) NULL,
    waist_cm     DECIMAL(5,1) NULL,
    hips_cm      DECIMAL(5,1) NULL,
    arms_cm      DECIMAL(5,1) NULL,
    legs_cm      DECIMAL(5,1) NULL,
    notes        NVARCHAR(500) NULL,
    logged_by    INT          NULL REFERENCES users(id),
    created_at   DATETIME2    NOT NULL DEFAULT GETDATE()
);
GO

-- ─── EQUIPMENT — add missing columns used by service ────────────────────────
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('equipment') AND name='equipment_name')
    ALTER TABLE equipment ADD equipment_name NVARCHAR(150) NOT NULL DEFAULT '';
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('equipment') AND name='brand')
    ALTER TABLE equipment ADD brand NVARCHAR(100) NULL;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('equipment') AND name='model')
    ALTER TABLE equipment ADD model NVARCHAR(100) NULL;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('equipment') AND name='serial_number')
    ALTER TABLE equipment ADD serial_number NVARCHAR(100) NULL;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('equipment') AND name='condition_status')
    ALTER TABLE equipment ADD condition_status NVARCHAR(20) NOT NULL DEFAULT 'Good';
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('equipment') AND name='last_maintenance_date')
    ALTER TABLE equipment ADD last_maintenance_date DATE NULL;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('equipment') AND name='notes')
    ALTER TABLE equipment ADD notes NVARCHAR(MAX) NULL;
GO

-- ─── SALARY RECORDS — add missing columns ────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('salary_records') AND name='bonus')
    ALTER TABLE salary_records ADD bonus DECIMAL(10,2) NULL DEFAULT 0;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('salary_records') AND name='deduction')
    ALTER TABLE salary_records ADD deduction DECIMAL(10,2) NULL DEFAULT 0;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('salary_records') AND name='net_salary')
    ALTER TABLE salary_records ADD net_salary AS (amount + ISNULL(bonus,0) - ISNULL(deduction,0)) PERSISTED;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('salary_records') AND name='notes')
    ALTER TABLE salary_records ADD notes NVARCHAR(500) NULL;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('salary_records') AND name='updated_at')
    ALTER TABLE salary_records ADD updated_at DATETIME2 NULL DEFAULT GETDATE();
GO

-- ─── INDEXES ──────────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_members_branch')
    CREATE INDEX idx_members_branch    ON members(branch_id);
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_members_status')
    CREATE INDEX idx_members_status    ON members(status);
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_attendance_member')
    CREATE INDEX idx_attendance_member ON attendance(member_id);
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_attendance_date')
    CREATE INDEX idx_attendance_date   ON attendance(date);
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_payments_member')
    CREATE INDEX idx_payments_member   ON payments(member_id);
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_audit_timestamp')
    CREATE INDEX idx_audit_timestamp   ON audit_logs(timestamp);
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_sched_date')
    CREATE INDEX idx_sched_date        ON trainer_schedule(slot_date);
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_progress_member')
    CREATE INDEX idx_progress_member   ON progress_logs(member_id);
GO

PRINT 'FitLifeDB schema Phase 5 additions complete.';
GO
