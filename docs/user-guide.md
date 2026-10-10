# FitLife User Guide & Operational Manual

This guide provides end-user documentation and step-by-step feature walkthroughs for all 4 user roles in **FitLife Gym Management System**.

---

## 1. Application Layout & Navigation

Upon logging into FitLife, users are presented with a modern glassmorphic application shell:

```
+-----------------------------------------------------------------------------------+
|  [FitLife Logo]   [Branch Indicator]             [Search]  [Theme]  [User Profile]  | Top Bar
+------------------+----------------------------------------------------------------+
|  📊 Dashboard    |                                                                |
|  👥 Members      |                                                                |
|  🏋️ Trainers     |                                                                |
|  🏢 Branches     |                   ACTIVE FEATURE SCREEN                        | Main View
|  💳 Billing      |                (e.g., Member Directory)                        | Area
|  📋 Attendance   |                                                                |
|  💪 Workout Plans|                                                                |
|  🥗 Diet Plans   |                                                                |
|  📈 Progress     |                                                                |
|  🤖 Smart Ask    |                                                                |
|  ⚙️ Settings     |                                                                |
+------------------+----------------------------------------------------------------+ Sidebar
```

---

## 2. Role-Based Feature Walkthroughs

### 2.1 Admin Role
*The Admin persona has unrestricted access across all branches, financial data, and system settings.*

#### Key Admin Workflows:
1. **Multi-Branch Overview**: Select branches via top-bar dropdown to filter KPIs and operational metrics across the network.
2. **Staff Management & Payroll**:
   - Navigate to `Staff` module to recruit, edit, or deactivate trainers and managers.
   - Access `Salary` to calculate and disburse monthly payrolls.
3. **Audit Log Inspection**:
   - Navigate to `Analytics` -> `Audit Logs` to review timestamped security events, failed logins, and data modifications across all branches.
4. **CSV Export Reports**:
   - Open `Reports` module, select date range and branch, then click **Export CSV** to download financial, attendance, or membership reports.

---

### 2.2 Manager Role
*Branch Managers oversee daily operations, member subscriptions, attendance, and branch billing.*

#### Key Manager Workflows:
1. **Registering a New Member**:
   - Navigate to `Members` -> Click **Add Member**.
   - Fill in full name, CNIC (13 digits), phone, emergency contact, select membership plan (e.g. Monthly, Quarterly, Annual), and assign a Trainer.
   - Click **Save**. The system automatically sets the subscription start and expiry dates.
2. **Recording Payments & Generating Invoices**:
   - Navigate to `Billing` -> Click **New Payment**.
   - Select member name, enter payment amount and method (Cash/Card/Online).
   - Click **Generate Invoice**. An official receipt with a unique invoice number (e.g. `INV-20260729-0042`) is created.
3. **Logging Attendance**:
   - Navigate to `Attendance`. Use manual search or CNIC scanner input to check in members as they enter the facility.

---

### 2.3 Trainer Role
*Trainers manage member workout routines, diet plans, and progress tracking.*

#### Key Trainer Workflows:
1. **Creating Custom Workout Plans**:
   - Navigate to `Workout Plans` -> Click **Create Workout Plan**.
   - Select an assigned member.
   - Add exercises from the catalog, specifying Sets, Reps, Weight (kg), and Rest duration.
   - Click **Assign Plan**.
2. **Building Diet Plans**:
   - Navigate to `Diet Plans` -> Click **New Nutrition Plan**.
   - Input target daily calories, macronutrient split (Protein g, Carbs g, Fats g), and meal schedules (Breakfast, Lunch, Pre-workout, Dinner).
3. **Tracking Body Transformation**:
   - Navigate to `Progress` -> Select member -> Record body weight, height, body fat %, and measurement circumferences (chest, waist, biceps).

---

### 2.4 Member Role
*Members access a simplified, self-service portal.*

#### Key Member Workflows:
1. **Subscription Status**: View active membership tier, start date, expiry date, and remaining days.
2. **Viewing Workout & Diet Schedule**: Access current assigned workout routine and nutrition plan set by their trainer.
3. **Progress Log**: View body weight graph and BMI progress history.

---

## 3. Smart Ask AI Assistant

FitLife features **Smart Ask**, an integrated AI assistant:

1. Click **Smart Ask** in the left sidebar.
2. Type fitness, nutrition, or system operational questions (e.g. *"Suggest a high-protein meal plan for muscle gain"* or *"How do I export monthly financial reports?"*).
3. Click **Send** or press `Enter`. The AI responds instantly with structured, clear recommendations.

---

## 4. Settings & Personalization

1. Click **Settings** in the left sidebar.
2. **Theme Selection**: Toggle between **Dark Glass** and **Light Glass** themes.
3. **Profile Settings**: Update contact information or email address.
4. **Change Password**: Input current password and new password (min. 8 characters).
