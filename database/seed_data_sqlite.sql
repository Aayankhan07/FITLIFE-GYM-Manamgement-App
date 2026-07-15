-- ============================================================
-- FitLife — Seed Data
-- Run AFTER schema.sql
-- Passwords are bcrypt hashes of: Admin@123, Manager@123, Trainer@123, Member@123
-- ============================================================



-- ─── ROLES ────────────────────────────────────────────────────────────────────
INSERT INTO roles (role_name, description) VALUES
('Admin',   'Full system access and control'),
('Manager', 'Branch-level management access'),
('Trainer', 'Training and plan verification access'),
('Member',  'Personal data and plan view access');


-- ─── BRANCHES (insert without manager_id first) ───────────────────────────────
INSERT INTO branches (branch_name, city, address, phone, email, capacity, opening_date, status) VALUES
('FitLife Downtown', 'Karachi', '24-B Main Shahrah-e-Faisal, Karachi', '02134567890', 'downtown@fitlife.pk', 200, '2022-01-15', 'Active'),
('FitLife North',   'Lahore',  '17 Gulberg III, Main Boulevard, Lahore', '04234567890', 'north@fitlife.pk',    150, '2023-03-01', 'Active');


-- ─── USERS ────────────────────────────────────────────────────────────────────
-- Admin@123  => $2b$12$Wv2QNtvXvul3tIFdr22t8edVKNPO5NSXmYmLweTjJcp/tBfokK3Ba
-- Manager@123=> $2b$12$9M6HykgoHPNpTQmRbcvxje4QcAaPCGbAlKJpuV7atDsS2xkqw337S
-- Trainer@123=> $2b$12$A6qpNjj29IO9gDdTMDGxh.1lIBbDUEr0uMK79Rfms6c3gNz65YSfm
-- Member@123 => $2b$12$6vaZsPYA3k4sx4eVcLEgeOCWMEtMUAoPeKF47xTREG/hxJEH3g86u






INSERT INTO users (username, password_hash, role_id, full_name, email, phone, branch_id, is_active) VALUES
('admin',    '$2b$12$Wv2QNtvXvul3tIFdr22t8edVKNPO5NSXmYmLweTjJcp/tBfokK3Ba',   1, 'System Administrator', 'admin@fitlife.pk',    '03001234567', NULL, 1),
('manager1', '$2b$12$9M6HykgoHPNpTQmRbcvxje4QcAaPCGbAlKJpuV7atDsS2xkqw337S',     2, 'Ali Hassan',           'manager1@fitlife.pk', '03011234567', 1,    1),
('manager2', '$2b$12$9M6HykgoHPNpTQmRbcvxje4QcAaPCGbAlKJpuV7atDsS2xkqw337S',     2, 'Bilal Raza',           'manager2@fitlife.pk', '03021234567', 2,    1),
('trainer1', '$2b$12$A6qpNjj29IO9gDdTMDGxh.1lIBbDUEr0uMK79Rfms6c3gNz65YSfm', 3, 'Usman Farooq',         'trainer1@fitlife.pk', '03031234567', 1,    1),
('trainer2', '$2b$12$A6qpNjj29IO9gDdTMDGxh.1lIBbDUEr0uMK79Rfms6c3gNz65YSfm', 3, 'Kamran Malik',         'trainer2@fitlife.pk', '03041234567', 1,    1),
('trainer3', '$2b$12$A6qpNjj29IO9gDdTMDGxh.1lIBbDUEr0uMK79Rfms6c3gNz65YSfm', 3, 'Zeeshan Ahmad',        'trainer3@fitlife.pk', '03051234567', 2,    1),
('trainer4', '$2b$12$A6qpNjj29IO9gDdTMDGxh.1lIBbDUEr0uMK79Rfms6c3gNz65YSfm', 3, 'Faisal Qureshi',       'trainer4@fitlife.pk', '03061234567', 2,    1),
('member1',  '$2b$12$6vaZsPYA3k4sx4eVcLEgeOCWMEtMUAoPeKF47xTREG/hxJEH3g86u',  4, 'Ahmed Siddiqui',       'member1@gmail.com',   '03071234567', 1,    1),
('member2',  '$2b$12$6vaZsPYA3k4sx4eVcLEgeOCWMEtMUAoPeKF47xTREG/hxJEH3g86u',  4, 'Hamza Khan',           'member2@gmail.com',   '03081234567', 1,    1),
('member3',  '$2b$12$6vaZsPYA3k4sx4eVcLEgeOCWMEtMUAoPeKF47xTREG/hxJEH3g86u',  4, 'Tariq Mahmood',        'member3@gmail.com',   '03091234567', 1,    1),
('member4',  '$2b$12$6vaZsPYA3k4sx4eVcLEgeOCWMEtMUAoPeKF47xTREG/hxJEH3g86u',  4, 'Shahid Iqbal',         'member4@gmail.com',   '03101234567', 2,    1),
('member5',  '$2b$12$6vaZsPYA3k4sx4eVcLEgeOCWMEtMUAoPeKF47xTREG/hxJEH3g86u',  4, 'Rehan Zafar',          'member5@gmail.com',   '03111234567', 2,    1);


-- Update branch managers
UPDATE branches SET manager_id = 2 WHERE id = 1;
UPDATE branches SET manager_id = 3 WHERE id = 2;


-- ─── TRAINERS ─────────────────────────────────────────────────────────────────
INSERT INTO trainers (user_id, branch_id, full_name, cnic, phone, email, specialization, monthly_salary, hire_date, qualification, status) VALUES
(4, 1, 'Usman Farooq',   '4210112345671', '03031234567', 'trainer1@fitlife.pk', 'Strength',       55000, '2022-02-01', 'BSc Sports Science', 'Active'),
(5, 1, 'Kamran Malik',   '4210112345672', '03041234567', 'trainer2@fitlife.pk', 'Cardio',         48000, '2022-06-15', 'Diploma in Fitness', 'Active'),
(6, 2, 'Zeeshan Ahmad',  '4210112345673', '03051234567', 'trainer3@fitlife.pk', 'HIIT',           52000, '2023-04-01', 'Certified PT',       'Active'),
(7, 2, 'Faisal Qureshi', '4210112345674', '03061234567', 'trainer4@fitlife.pk', 'General Fitness',45000, '2023-05-10', 'BSc Physical Ed',    'Active');


-- ─── MEMBERSHIP PLANS ─────────────────────────────────────────────────────────
INSERT INTO membership_plans (plan_name, duration_days, price, description, is_active) VALUES
('Monthly Basic',    30,  3500,  'Access to gym floor and basic equipment. Valid 30 days.',         1),
('Monthly Premium',  30,  5500,  'Full access + trainer session twice a week. Valid 30 days.',      1),
('Quarterly Basic',  90,  9500,  'Three months access to gym floor and equipment.',                 1),
('Quarterly Premium',90,  15000, 'Three months full access + weekly trainer sessions.',             1),
('Half-Yearly',      180, 28000, 'Six months full access with bi-weekly trainer check-ins.',        1),
('Annual Elite',     365, 50000, 'Full year access, unlimited trainer sessions, priority booking.', 1);


-- ─── MEMBERS ──────────────────────────────────────────────────────────────────
INSERT INTO members (user_id, branch_id, trainer_id, full_name, cnic, date_of_birth, phone, email, fitness_goal, weight_kg, height_cm, bmi, join_date, membership_plan_id, expiry_date, status) VALUES
(8,  1, 1, 'Ahmed Siddiqui', '4210112345601', '1995-03-15', '03071234567', 'member1@gmail.com', 'Bulking',      78.5, 175.0, 25.6, '2026-01-01', 2, '2026-01-31', 'Active'),
(9,  1, 1, 'Hamza Khan',     '4210112345602', '1998-07-22', '03081234567', 'member2@gmail.com', 'Weight Loss',  92.0, 178.0, 29.0, '2026-01-05', 1, '2026-02-04', 'Active'),
(10, 1, 2, 'Tariq Mahmood',  '4210112345603', '1990-11-10', '03091234567', 'member3@gmail.com', 'Maintenance',  70.0, 170.0, 24.2, '2025-12-01', 3, '2026-02-28', 'Active'),
(11, 2, 3, 'Shahid Iqbal',   '4210112345604', '2000-05-18', '03101234567', 'member4@gmail.com', 'Cutting',      85.0, 180.0, 26.2, '2026-01-10', 2, '2026-02-09', 'Active'),
(12, 2, 4, 'Rehan Zafar',    '4210112345605', '1993-09-25', '03111234567', 'member5@gmail.com', 'Endurance',    68.0, 172.0, 23.0, '2026-02-01', 4, '2026-04-30', 'Active'),
(NULL, 1, 1, 'Junaid Aslam', '4210112345606', '1997-01-30', '03121234567', 'junaid@gmail.com',  'Bulking',      82.0, 176.0, 26.5, '2025-11-01', 6, '2026-10-31', 'Active'),
(NULL, 1, 2, 'Saad Mehmood', '4210112345607', '2001-04-12', '03131234567', 'saad@gmail.com',    'Weight Loss',  95.0, 177.0, 30.4, '2026-01-15', 1, '2026-02-14', 'Expired'),
(NULL, 2, 3, 'Owais Rana',   '4210112345608', '1996-08-05', '03141234567', 'owais@gmail.com',   'Maintenance',  73.0, 173.0, 24.4, '2026-02-10', 3, '2026-05-10', 'Active'),
(NULL, 2, 4, 'Nabeel Javed', '4210112345609', '1994-12-20', '03151234567', 'nabeel@gmail.com',  'Bulking',      77.0, 174.0, 25.4, '2026-01-20', 5, '2026-07-19', 'Active'),
(NULL, 1, 2, 'Adnan Malik',  '4210112345610', '1992-06-08', '03161234567', 'adnan@gmail.com',   'Cutting',      88.0, 179.0, 27.5, '2025-10-01', 6, '2026-09-30', 'Active');


-- ─── MEMBERSHIPS ──────────────────────────────────────────────────────────────
INSERT INTO memberships (member_id, plan_id, start_date, end_date, status) VALUES
(1, 2, '2026-01-01', '2026-01-31', 'Active'),
(2, 1, '2026-01-05', '2026-02-04', 'Active'),
(3, 3, '2025-12-01', '2026-02-28', 'Active'),
(4, 2, '2026-01-10', '2026-02-09', 'Active'),
(5, 4, '2026-02-01', '2026-04-30', 'Active');


-- ─── PAYMENTS ─────────────────────────────────────────────────────────────────
INSERT INTO payments (member_id, membership_id, amount, payment_date, payment_method, status, invoice_number, recorded_by) VALUES
(1, 1, 5500, '2026-01-01', 'Cash',            'Paid',   'INV-2026-0001', 2),
(2, 2, 3500, '2026-01-05', 'Card',            'Paid',   'INV-2026-0002', 2),
(3, 3, 9500, '2025-12-01', 'Online Transfer', 'Paid',   'INV-2025-0010', 2),
(4, 4, 5500, '2026-01-10', 'Cash',            'Paid',   'INV-2026-0003', 3),
(5, 5,15000, '2026-02-01', 'Bank Deposit',    'Paid',   'INV-2026-0004', 3),
(6, NULL,50000,'2025-11-01','Card',            'Paid',   'INV-2025-0005', 2),
(7, NULL, 3500,'2026-01-15','Cash',            'Overdue','INV-2026-0007', 2);


-- ─── ATTENDANCE (sample — last 7 days) ───────────────────────────────────────
INSERT INTO attendance (member_id, branch_id, check_in_time, check_out_time, date, status, recorded_by) VALUES
(1, 1, '2026-05-13 07:30:00', '2026-05-13 09:15:00', '2026-05-13', 'Present', 2),
(2, 1, '2026-05-13 08:00:00', '2026-05-13 09:30:00', '2026-05-13', 'Present', 2),
(3, 1, '2026-05-13 07:45:00', '2026-05-13 09:00:00', '2026-05-13', 'Late',    2),
(1, 1, '2026-05-14 07:30:00', '2026-05-14 09:10:00', '2026-05-14', 'Present', 2),
(2, 1, '2026-05-14 08:05:00', '2026-05-14 09:45:00', '2026-05-14', 'Present', 2),
(4, 2, '2026-05-13 09:00:00', '2026-05-13 10:30:00', '2026-05-13', 'Present', 3),
(5, 2, '2026-05-13 09:15:00', '2026-05-13 11:00:00', '2026-05-13', 'Present', 3);


-- ─── SALARY RECORDS ───────────────────────────────────────────────────────────
INSERT INTO salary_records (trainer_id, month, year, amount, payment_date, payment_method, status, paid_by) VALUES
(1, 4, 2026, 55000, '2026-04-30', 'Bank Deposit', 'Paid',    2),
(2, 4, 2026, 48000, '2026-04-30', 'Bank Deposit', 'Paid',    2),
(3, 4, 2026, 52000, '2026-04-30', 'Bank Deposit', 'Paid',    3),
(4, 4, 2026, 45000, '2026-04-30', 'Bank Deposit', 'Paid',    3),
(1, 5, 2026, 55000, NULL,          NULL,           'Pending', NULL),
(2, 5, 2026, 48000, NULL,          NULL,           'Pending', NULL),
(3, 5, 2026, 52000, NULL,          NULL,           'Pending', NULL),
(4, 5, 2026, 45000, NULL,          NULL,           'Pending', NULL);


-- ─── EQUIPMENT ────────────────────────────────────────────────────────────────
INSERT INTO equipment (branch_id, name, category, quantity, purchase_date, purchase_price, condition, next_maintenance_date) VALUES
(1, 'Treadmill Pro X5',     'Cardio',       5, '2022-01-15', 185000, 'Good',   '2026-06-01'),
(1, 'Stationary Bike',      'Cardio',       3, '2022-01-15', 95000,  'Good',   '2026-06-01'),
(1, 'Olympic Barbell Set',  'Free Weights', 10,'2022-02-01', 45000,  'Good',   NULL),
(1, 'Dumbbells 5-50kg',     'Free Weights', 20,'2022-02-01', 120000, 'Good',   NULL),
(1, 'Lat Pulldown Machine', 'Machines',     2, '2022-03-01', 220000, 'Fair',   '2026-05-20'),
(1, 'Chest Press Machine',  'Machines',     2, '2022-03-01', 195000, 'Good',   '2026-07-01'),
(2, 'Treadmill Elite',      'Cardio',       4, '2023-03-01', 195000, 'New',    '2026-09-01'),
(2, 'Rowing Machine',       'Cardio',       2, '2023-03-01', 145000, 'Good',   '2026-08-01'),
(2, 'Power Rack',           'Strength',     2, '2023-04-01', 280000, 'Good',   NULL),
(2, 'Dumbbells 5-40kg',     'Free Weights', 15,'2023-04-01', 95000,  'New',    NULL);


-- ─── SYSTEM SETTINGS ──────────────────────────────────────────────────────────
INSERT INTO system_settings (setting_key, setting_value, description) VALUES
('app_name',           'FitLife',      'Application display name'),
('currency_symbol',    'Rs.',          'Currency symbol for billing'),
('invoice_prefix',     'INV',          'Prefix for auto-generated invoice numbers'),
('date_format',        'dd/MM/yyyy',   'Display date format'),
('renewal_alert_days', '7',            'Days before expiry to send renewal alert'),
('overdue_grace_days', '3',            'Grace days before marking payment overdue');


-- ─── PROGRESS RECORDS ─────────────────────────────────────────────────────────
INSERT INTO progress_records (member_id, trainer_id, record_date, weight_kg, bmi, body_fat_pct, chest_cm, waist_cm, arm_cm, bench_press_max_kg, squat_max_kg, notes) VALUES
(1, 1, '2026-01-01', 78.5, 25.6, 18.0, 100.0, 85.0, 35.0, 80.0, 100.0, 'Starting baseline measurements.'),
(1, 1, '2026-02-01', 80.0, 26.1, 17.5, 101.5, 84.0, 36.0, 90.0, 110.0, 'Good progress on bench press. Keep it up.'),
(2, 1, '2026-01-05', 92.0, 29.0, 25.0, 108.0, 98.0, 38.0, 70.0, 90.0,  'Starting weight loss program.'),
(2, 1, '2026-02-05', 89.5, 28.3, 23.5, 106.0, 95.0, 37.5, 72.0, 95.0,  'Lost 2.5kg. Great consistency.');




