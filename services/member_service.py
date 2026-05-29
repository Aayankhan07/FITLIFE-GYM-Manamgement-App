"""
FitLife — Member Service
Full CRUD + search/filter + BMI calculation + profile data.
"""
import logging
from datetime import date, timedelta
from typing import Optional
from database.connection import DatabaseConnection
from config.constants import (
    MEMBER_STATUS_ACTIVE, MEMBER_STATUS_EXPIRED,
    ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE
)

logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _calc_bmi(weight_kg: float, height_cm: float) -> Optional[float]:
    try:
        if weight_kg and height_cm and height_cm > 0:
            h_m = height_cm / 100
            return round(weight_kg / (h_m * h_m), 1)
    except Exception:
        pass
    return None


def _log_audit(user_id, action, module, record_id, old_val="", new_val=""):
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "INSERT INTO audit_logs (user_id,action,module,record_id,old_value,new_value,timestamp)"
                " VALUES (?,?,?,?,?,?,GETDATE())",
                (user_id, action, module, record_id, str(old_val), str(new_val))
            )
    except Exception as e:
        logger.error(f"Audit log error: {e}")


# ─── GET ALL MEMBERS ──────────────────────────────────────────────────────────
def get_all_members(branch_id: Optional[int] = None,
                    status: Optional[str] = None,
                    search: Optional[str] = None) -> list:
    """
    Returns list of member rows for display.
    branch_id=None → all branches (admin view).
    """
    try:
        sql = """
            SELECT m.id, m.full_name, m.cnic, m.phone, m.email,
                   b.branch_name, t.full_name AS trainer_name,
                   mp.plan_name, m.expiry_date, m.status,
                   m.fitness_goal, m.weight_kg, m.height_cm, m.bmi,
                   m.join_date, m.branch_id, m.trainer_id, m.membership_plan_id
            FROM   members m
            LEFT JOIN branches b  ON m.branch_id = b.id
            LEFT JOIN trainers t  ON m.trainer_id = t.id
            LEFT JOIN membership_plans mp ON m.membership_plan_id = mp.id
            WHERE  1=1
        """
        params = []
        if branch_id:
            sql += " AND m.branch_id = ?"
            params.append(branch_id)
        if status:
            sql += " AND m.status = ?"
            params.append(status)
        if search:
            sql += " AND (m.full_name LIKE ? OR m.cnic LIKE ? OR m.phone LIKE ? OR m.email LIKE ?)"
            s = f"%{search}%"
            params += [s, s, s, s]
        sql += " ORDER BY m.created_at DESC"

        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_all_members error: {e}", exc_info=True)
        return []


def get_member_by_id(member_id: int) -> Optional[object]:
    """Returns a single member row by ID."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT m.id, m.full_name, m.cnic, m.date_of_birth, m.phone, m.email,
                       m.emergency_contact, m.address, m.photo_path,
                       m.fitness_goal, m.health_conditions,
                       m.weight_kg, m.height_cm, m.bmi,
                       m.join_date, m.expiry_date, m.status,
                       m.branch_id, m.trainer_id, m.membership_plan_id,
                       m.user_id, m.created_at, m.updated_at,
                       b.branch_name, t.full_name AS trainer_name,
                       mp.plan_name
                FROM   members m
                LEFT JOIN branches b  ON m.branch_id = b.id
                LEFT JOIN trainers t  ON m.trainer_id = t.id
                LEFT JOIN membership_plans mp ON m.membership_plan_id = mp.id
                WHERE  m.id = ?
            """, (member_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"get_member_by_id error: {e}")
        return None


def get_member_by_user_id(user_id: int) -> Optional[object]:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT m.id, m.full_name, m.cnic, m.date_of_birth, m.phone, m.email,
                       m.emergency_contact, m.address, m.photo_path,
                       m.fitness_goal, m.health_conditions,
                       m.weight_kg, m.height_cm, m.bmi,
                       m.join_date, m.expiry_date, m.status,
                       m.branch_id, m.trainer_id, m.membership_plan_id,
                       m.user_id, m.created_at, m.updated_at,
                       b.branch_name, t.full_name AS trainer_name,
                       mp.plan_name
                FROM   members m
                LEFT JOIN branches b  ON m.branch_id = b.id
                LEFT JOIN trainers t  ON m.trainer_id = t.id
                LEFT JOIN membership_plans mp ON m.membership_plan_id = mp.id
                WHERE  m.user_id = ?
            """, (user_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"get_member_by_user_id error: {e}")
        return None


# ─── CREATE ───────────────────────────────────────────────────────────────────
def create_member(data: dict, created_by_user_id: int) -> dict:
    """
    Create a new member record.
    data keys: full_name, cnic, date_of_birth, phone, email, emergency_contact,
               address, photo_path, fitness_goal, health_conditions,
               weight_kg, height_cm, branch_id, trainer_id, membership_plan_id,
               join_date, expiry_date, status, user_id(optional)
    """
    try:
        bmi = _calc_bmi(data.get("weight_kg"), data.get("height_cm"))

        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO members
                    (user_id, branch_id, trainer_id, full_name, cnic,
                     date_of_birth, phone, email, emergency_contact, address,
                     photo_path, fitness_goal, health_conditions,
                     weight_kg, height_cm, bmi,
                     join_date, membership_plan_id, expiry_date, status,
                     created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,GETDATE(),GETDATE())
            """, (
                data.get("user_id"),
                data["branch_id"],
                data.get("trainer_id"),
                data["full_name"],
                data["cnic"],
                data["date_of_birth"],
                data["phone"],
                data.get("email"),
                data.get("emergency_contact"),
                data.get("address"),
                data.get("photo_path"),
                data.get("fitness_goal", "Maintenance"),
                data.get("health_conditions"),
                data.get("weight_kg"),
                data.get("height_cm"),
                bmi,
                data.get("join_date", date.today()),
                data.get("membership_plan_id"),
                data.get("expiry_date"),
                data.get("status", MEMBER_STATUS_ACTIVE),
            ))
            cursor.execute("SELECT @@IDENTITY")
            new_id = int(cursor.fetchone()[0])

        _log_audit(created_by_user_id, ACTION_CREATE, "Members", new_id,
                   new_val=data["full_name"])
        logger.info(f"Member created: {data['full_name']} (id={new_id})")
        return {"success": True, "member_id": new_id, "message": "Member added successfully."}
    except Exception as e:
        logger.error(f"create_member error: {e}", exc_info=True)
        if "UNIQUE" in str(e) or "unique" in str(e).lower():
            return {"success": False, "message": "A member with this CNIC already exists."}
        return {"success": False, "message": f"Failed to create member: {e}"}


# ─── UPDATE ───────────────────────────────────────────────────────────────────
def update_member(member_id: int, data: dict, updated_by_user_id: int) -> dict:
    try:
        bmi = _calc_bmi(data.get("weight_kg"), data.get("height_cm"))
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                UPDATE members SET
                    branch_id=?, trainer_id=?, full_name=?, cnic=?,
                    date_of_birth=?, phone=?, email=?, emergency_contact=?,
                    address=?, photo_path=?, fitness_goal=?, health_conditions=?,
                    weight_kg=?, height_cm=?, bmi=?,
                    membership_plan_id=?, expiry_date=?, status=?,
                    updated_at=GETDATE()
                WHERE id=?
            """, (
                data["branch_id"], data.get("trainer_id"), data["full_name"],
                data["cnic"], data["date_of_birth"], data["phone"],
                data.get("email"), data.get("emergency_contact"),
                data.get("address"), data.get("photo_path"),
                data.get("fitness_goal", "Maintenance"),
                data.get("health_conditions"),
                data.get("weight_kg"), data.get("height_cm"), bmi,
                data.get("membership_plan_id"), data.get("expiry_date"),
                data.get("status", MEMBER_STATUS_ACTIVE),
                member_id,
            ))
        _log_audit(updated_by_user_id, ACTION_UPDATE, "Members", member_id,
                   new_val=data["full_name"])
        return {"success": True, "message": "Member updated successfully."}
    except Exception as e:
        logger.error(f"update_member error: {e}", exc_info=True)
        if "UNIQUE" in str(e) or "unique" in str(e).lower():
            return {"success": False, "message": "CNIC already in use by another member."}
        return {"success": False, "message": f"Failed to update member: {e}"}


# ─── DELETE ───────────────────────────────────────────────────────────────────
def delete_member(member_id: int, deleted_by_user_id: int) -> dict:
    try:
        row = get_member_by_id(member_id)
        name = row[1] if row else str(member_id)
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("DELETE FROM members WHERE id=?", (member_id,))
        _log_audit(deleted_by_user_id, ACTION_DELETE, "Members", member_id,
                   old_val=name)
        return {"success": True, "message": f"Member '{name}' deleted successfully."}
    except Exception as e:
        logger.error(f"delete_member error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to delete member: {e}"}


# ─── MEMBER STATS ─────────────────────────────────────────────────────────────
def get_unlinked_members() -> list:
    """Return list of members without an associated user account.
    Returns list of tuples (member_id, full_name).
    """
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT id, full_name FROM members WHERE user_id IS NULL
            """)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_unlinked_members error: {e}")
        return []


def link_member_user(member_id: int, user_id: int) -> dict:
    """Link a member record to a user account.
    Updates the members.user_id field.
    """
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE members SET user_id=?, updated_at=GETDATE() WHERE id=?",
                (user_id, member_id)
            )
        _log_audit(user_id, ACTION_UPDATE, "Members", member_id, new_val="Linked to user")
        return {"success": True, "message": "Member linked to user successfully."}
    except Exception as e:
        logger.error(f"link_member_user error: {e}")
        return {"success": False, "message": f"Failed to link member: {e}"}

def get_member_stats(branch_id: Optional[int] = None) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            b_filter = "AND branch_id=?" if branch_id else ""
            params = (branch_id,) if branch_id else ()
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status='Active'    THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN status='Inactive'  THEN 1 ELSE 0 END) as inactive,
                    SUM(CASE WHEN status='Expired'   THEN 1 ELSE 0 END) as expired,
                    SUM(CASE WHEN status='Suspended' THEN 1 ELSE 0 END) as suspended
                FROM members WHERE 1=1 {b_filter}
            """, params)
            row = cursor.fetchone()
            return {
                "total": row[0], "active": row[1],
                "inactive": row[2], "expired": row[3], "suspended": row[4]
            }
    except Exception as e:
        logger.error(f"get_member_stats error: {e}")
        return {"total": 0, "active": 0, "inactive": 0, "expired": 0, "suspended": 0}


def get_expiring_soon(branch_id: Optional[int] = None, days: int = 7) -> list:
    """Members whose membership expires within `days` days."""
    try:
        sql = """
            SELECT m.id, m.full_name, m.phone, m.email, m.expiry_date, b.branch_name
            FROM   members m
            JOIN   branches b ON m.branch_id = b.id
            WHERE  m.status='Active'
            AND    m.expiry_date BETWEEN CAST(GETDATE() AS DATE)
                   AND DATEADD(day, ?, CAST(GETDATE() AS DATE))
        """
        params = [days]
        if branch_id:
            sql += " AND m.branch_id=?"
            params.append(branch_id)
        sql += " ORDER BY m.expiry_date ASC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_expiring_soon error: {e}")
        return []


def get_member_attendance_history(member_id: int, limit: int = 30) -> list:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT date, check_in_time, check_out_time, status, notes
                FROM   attendance
                WHERE  member_id=?
                ORDER BY date DESC
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
            """, (member_id, limit))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_member_attendance_history error: {e}")
        return []


def get_member_payment_history(member_id: int) -> list:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT payment_date, amount, payment_method, status, invoice_number, notes
                FROM   payments
                WHERE  member_id=?
                ORDER BY payment_date DESC
            """, (member_id,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_member_payment_history error: {e}")
        return []


def update_expired_memberships() -> int:
    """Auto-mark expired memberships — call on startup/daily."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                UPDATE members
                SET    status='Expired', updated_at=GETDATE()
                WHERE  expiry_date < CAST(GETDATE() AS DATE)
                AND    status='Active'
            """)
            return cursor.rowcount
    except Exception as e:
        logger.error(f"update_expired_memberships error: {e}")
        return 0
