"""
FitLife — Application Constants
Central repository for all constant values used across the application.
"""

# ─── Application Info ─────────────────────────────────────────────────────────
APP_NAME = "FitLife"
APP_VERSION = "1.0.0"
APP_SUBTITLE = "Male Fitness Chain Management System"
APP_TAGLINE = "Elevate Every Rep"

# ─── User Roles ───────────────────────────────────────────────────────────────
ROLE_ADMIN = "Admin"
ROLE_MANAGER = "Manager"
ROLE_TRAINER = "Trainer"
ROLE_MEMBER = "Member"

ALL_ROLES = [ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER]

# ─── Security ─────────────────────────────────────────────────────────────────
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
SESSION_TIMEOUT_MINUTES = 30
SESSION_WARNING_MINUTES = 25
BCRYPT_ROUNDS = 12

# ─── Member Status ────────────────────────────────────────────────────────────
MEMBER_STATUS_ACTIVE = "Active"
MEMBER_STATUS_INACTIVE = "Inactive"
MEMBER_STATUS_SUSPENDED = "Suspended"
MEMBER_STATUS_EXPIRED = "Expired"

MEMBER_STATUSES = [
    MEMBER_STATUS_ACTIVE,
    MEMBER_STATUS_INACTIVE,
    MEMBER_STATUS_SUSPENDED,
    MEMBER_STATUS_EXPIRED,
]

# ─── Fitness Goals ────────────────────────────────────────────────────────────
GOAL_BULKING = "Bulking"
GOAL_CUTTING = "Cutting"
GOAL_MAINTENANCE = "Maintenance"
GOAL_WEIGHT_LOSS = "Weight Loss"
GOAL_ENDURANCE = "Endurance"

FITNESS_GOALS = [GOAL_BULKING, GOAL_CUTTING, GOAL_MAINTENANCE, GOAL_WEIGHT_LOSS, GOAL_ENDURANCE]

# ─── Trainer Specializations ──────────────────────────────────────────────────
SPEC_STRENGTH = "Strength"
SPEC_CARDIO = "Cardio"
SPEC_HIIT = "HIIT"
SPEC_YOGA = "Yoga"
SPEC_BOXING = "Boxing"
SPEC_GENERAL = "General Fitness"
SPEC_NUTRITION = "Nutrition"

SPECIALIZATIONS = [SPEC_STRENGTH, SPEC_CARDIO, SPEC_HIIT, SPEC_YOGA, SPEC_BOXING, SPEC_GENERAL, SPEC_NUTRITION]

# ─── Branch Status ────────────────────────────────────────────────────────────
BRANCH_STATUS_ACTIVE = "Active"
BRANCH_STATUS_CLOSED = "Closed"
BRANCH_STATUS_RENOVATION = "Under Renovation"

BRANCH_STATUSES = [BRANCH_STATUS_ACTIVE, BRANCH_STATUS_CLOSED, BRANCH_STATUS_RENOVATION]

# ─── Payment Status ───────────────────────────────────────────────────────────
PAYMENT_PAID = "Paid"
PAYMENT_UNPAID = "Unpaid"
PAYMENT_PARTIAL = "Partial"
PAYMENT_OVERDUE = "Overdue"

PAYMENT_STATUSES = [PAYMENT_PAID, PAYMENT_UNPAID, PAYMENT_PARTIAL, PAYMENT_OVERDUE]

# ─── Payment Methods ──────────────────────────────────────────────────────────
METHOD_CASH = "Cash"
METHOD_CARD = "Card"
METHOD_ONLINE = "Online Transfer"
METHOD_BANK = "Bank Deposit"

PAYMENT_METHODS = [METHOD_CASH, METHOD_CARD, METHOD_ONLINE, METHOD_BANK]

# ─── Membership Plans ─────────────────────────────────────────────────────────
PLAN_MONTHLY = "Monthly"
PLAN_QUARTERLY = "Quarterly"
PLAN_HALF_YEARLY = "Half-Yearly"
PLAN_ANNUAL = "Annual"
PLAN_CUSTOM = "Custom"

PLAN_TYPES = [PLAN_MONTHLY, PLAN_QUARTERLY, PLAN_HALF_YEARLY, PLAN_ANNUAL, PLAN_CUSTOM]

PLAN_DURATIONS = {
    PLAN_MONTHLY: 30,
    PLAN_QUARTERLY: 90,
    PLAN_HALF_YEARLY: 180,
    PLAN_ANNUAL: 365,
    PLAN_CUSTOM: 0,
}

# ─── Workout Plan Status ──────────────────────────────────────────────────────
PLAN_STATUS_DRAFT = "Draft"
PLAN_STATUS_PENDING = "Pending Verification"
PLAN_STATUS_APPROVED = "Trainer Approved"
PLAN_STATUS_ACTIVE = "Active"
PLAN_STATUS_COMPLETED = "Completed"
PLAN_STATUS_REJECTED = "Rejected"

PLAN_STATUSES = [
    PLAN_STATUS_DRAFT, PLAN_STATUS_PENDING, PLAN_STATUS_APPROVED,
    PLAN_STATUS_ACTIVE, PLAN_STATUS_COMPLETED, PLAN_STATUS_REJECTED,
]

# ─── Equipment Categories ─────────────────────────────────────────────────────
EQUIP_CARDIO = "Cardio"
EQUIP_STRENGTH = "Strength"
EQUIP_FREE_WEIGHTS = "Free Weights"
EQUIP_MACHINES = "Machines"
EQUIP_ACCESSORIES = "Accessories"

EQUIPMENT_CATEGORIES = [EQUIP_CARDIO, EQUIP_STRENGTH, EQUIP_FREE_WEIGHTS, EQUIP_MACHINES, EQUIP_ACCESSORIES]

# ─── Equipment Condition ──────────────────────────────────────────────────────
COND_NEW = "New"
COND_GOOD = "Good"
COND_FAIR = "Fair"
COND_DAMAGED = "Damaged"
COND_RETIRED = "Retired"

EQUIPMENT_CONDITIONS = [COND_NEW, COND_GOOD, COND_FAIR, COND_DAMAGED, COND_RETIRED]

# ─── Attendance Status ────────────────────────────────────────────────────────
ATTEND_PRESENT = "Present"
ATTEND_ABSENT = "Absent"
ATTEND_LATE = "Late"

ATTENDANCE_STATUSES = [ATTEND_PRESENT, ATTEND_ABSENT, ATTEND_LATE]
ATTEND_STATUSES = ATTENDANCE_STATUSES   # alias used by UI screens

# ─── Diet Meal Types ──────────────────────────────────────────────────────────
MEAL_BREAKFAST = "Breakfast"
MEAL_MORNING_SNACK = "Morning Snack"
MEAL_LUNCH = "Lunch"
MEAL_EVENING_SNACK = "Evening Snack"
MEAL_DINNER = "Dinner"
MEAL_PRE_WORKOUT = "Pre-Workout"
MEAL_POST_WORKOUT = "Post-Workout"

MEAL_TYPES = [
    MEAL_BREAKFAST, MEAL_MORNING_SNACK, MEAL_LUNCH,
    MEAL_EVENING_SNACK, MEAL_DINNER, MEAL_PRE_WORKOUT, MEAL_POST_WORKOUT,
]

# ─── Days of Week ─────────────────────────────────────────────────────────────
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYS_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ─── Diary Tags ───────────────────────────────────────────────────────────────
TAG_WORK = "Work"
TAG_PERSONAL = "Personal"
TAG_REMINDER = "Reminder"
TAG_IMPORTANT = "Important"

DIARY_TAGS = [TAG_WORK, TAG_PERSONAL, TAG_REMINDER, TAG_IMPORTANT]

# ─── Notification Types ───────────────────────────────────────────────────────
NOTIF_INFO = "info"
NOTIF_SUCCESS = "success"
NOTIF_WARNING = "warning"
NOTIF_ERROR = "error"
NOTIF_ALERT = "alert"

# ─── Salary Status ────────────────────────────────────────────────────────────
SALARY_PAID = "Paid"
SALARY_PENDING = "Pending"

SALARY_STATUSES = [SALARY_PAID, SALARY_PENDING]

# ─── Audit Actions ────────────────────────────────────────────────────────────
ACTION_LOGIN = "LOGIN"
ACTION_LOGOUT = "LOGOUT"
ACTION_LOGIN_FAILED = "LOGIN_FAILED"
ACTION_LOGIN_LOCKED = "LOGIN_LOCKED"
ACTION_CREATE = "CREATE"
ACTION_UPDATE = "UPDATE"
ACTION_DELETE = "DELETE"
ACTION_VIEW = "VIEW"
ACTION_EXPORT = "EXPORT"
ACTION_PAYMENT = "PAYMENT"
ACTION_SALARY = "SALARY"
ACTION_PLAN_APPROVE = "PLAN_APPROVE"
ACTION_PLAN_REJECT = "PLAN_REJECT"
ACTION_INVOICE_SENT = "INVOICE_SENT"

# ─── Modules ──────────────────────────────────────────────────────────────────
MODULE_MEMBERS = "Members"
MODULE_TRAINERS = "Trainers"
MODULE_BRANCHES = "Branches"
MODULE_BILLING = "Billing"
MODULE_ATTENDANCE = "Attendance"
MODULE_WORKOUT_PLANS = "Workout Plans"
MODULE_DIET_PLANS = "Diet Plans"
MODULE_EQUIPMENT = "Equipment"
MODULE_PROGRESS = "Progress"
MODULE_ANALYTICS = "Analytics"
MODULE_STAFF = "Staff"
MODULE_DIARY = "Diary"
MODULE_SMART_ASK = "Smart Ask"
MODULE_REPORTS = "Reports"
MODULE_SETTINGS = "Settings"
MODULE_SALARY = "Salary"
MODULE_AUDIT = "Audit Logs"

# ─── UI Constants ─────────────────────────────────────────────────────────────
SIDEBAR_WIDTH_EXPANDED = 260
SIDEBAR_WIDTH_COLLAPSED = 72
TOPBAR_HEIGHT = 64
PAGE_SIZE = 25
SEARCH_DEBOUNCE_MS = 300
ANIMATION_DURATION_MS = 200
TOAST_DURATION_MS = 4000

# ─── File Size Limits ─────────────────────────────────────────────────────────
MAX_PHOTO_SIZE_MB = 5
MAX_PHOTO_SIZE_BYTES = MAX_PHOTO_SIZE_MB * 1024 * 1024
ALLOWED_PHOTO_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]

# ─── Validation Ranges ────────────────────────────────────────────────────────
MIN_WEIGHT_KG = 30
MAX_WEIGHT_KG = 300
MIN_HEIGHT_CM = 100
MAX_HEIGHT_CM = 250
MIN_PHONE_DIGITS = 10
MAX_PHONE_DIGITS = 15
CNIC_LENGTH = 13

# ─── Report Types ─────────────────────────────────────────────────────────────
REPORT_MEMBER_LIST = "member_list"
REPORT_PAYMENT = "payment"
REPORT_ATTENDANCE = "attendance"
REPORT_TRAINER_PERFORMANCE = "trainer_performance"
REPORT_BRANCH_SUMMARY = "branch_summary"
REPORT_EQUIPMENT = "equipment"

# ─── Scheduler ────────────────────────────────────────────────────────────────
INVOICE_SEND_DAY = 27
OVERDUE_CHECK_DAY = 10
RENEWAL_WARNING_DAYS = 7
MAX_SEND_RETRIES = 3
