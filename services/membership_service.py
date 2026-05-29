"""
FitLife — Membership Plan Service + Membership Assignment
Full CRUD for plans + assign/renew membership with auto-expiry calculation.
"""
import logging
from datetime import date, timedelta
from typing import Optional
from database.connection import DatabaseConnection
from config.constants import ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE, PLAN_DURATIONS

logger = logging.getLogger(__name__)


def _log_audit(user_id, action, record_id, detail=""):
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "INSERT INTO audit_logs (user_id,action,module,record_id,new_value,timestamp)"
                " VALUES (?,?,?,?,?,GETDATE())",
                (user_id, action, "Membership Plans", record_id, detail)
            )
    except Exception as e:
        logger.error(f"Audit log error: {e}")


# ─── PLAN CRUD ────────────────────────────────────────────────────────────────
def get_all_plans(active_only: bool = False) -> list:
    try:
        sql = """
            SELECT id, plan_name, duration_days, price, description, is_active, created_at
            FROM   membership_plans
            WHERE  1=1
        """
        params = []
        if active_only:
            sql += " AND is_active=1"
        sql += " ORDER BY duration_days"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_all_plans error: {e}")
        return []


def get_plan_by_id(plan_id: int) -> Optional[object]:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "SELECT id, plan_name, duration_days, price, description, is_active FROM membership_plans WHERE id=?",
                (plan_id,)
            )
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"get_plan_by_id error: {e}")
        return None


def get_plans_dropdown() -> list:
    """Lightweight for ComboBox: [(id, plan_name, duration_days, price), ...]"""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "SELECT id, plan_name, duration_days, price FROM membership_plans WHERE is_active=1 ORDER BY duration_days"
            )
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_plans_dropdown error: {e}")
        return []


def create_plan(data: dict, created_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO membership_plans
                    (plan_name, duration_days, price, description, is_active, created_at)
                VALUES (?,?,?,?,?,GETDATE())
            """, (
                data["plan_name"],
                int(data["duration_days"]),
                float(data["price"]),
                data.get("description", ""),
                1 if data.get("is_active", True) else 0,
            ))
            cursor.execute("SELECT @@IDENTITY")
            new_id = int(cursor.fetchone()[0])
        _log_audit(created_by, ACTION_CREATE, new_id, data["plan_name"])
        return {"success": True, "plan_id": new_id, "message": "Membership plan created successfully."}
    except Exception as e:
        logger.error(f"create_plan error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to create plan: {e}"}


def update_plan(plan_id: int, data: dict, updated_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                UPDATE membership_plans SET
                    plan_name=?, duration_days=?, price=?, description=?, is_active=?
                WHERE id=?
            """, (
                data["plan_name"],
                int(data["duration_days"]),
                float(data["price"]),
                data.get("description", ""),
                1 if data.get("is_active", True) else 0,
                plan_id,
            ))
        _log_audit(updated_by, ACTION_UPDATE, plan_id, data["plan_name"])
        return {"success": True, "message": "Plan updated successfully."}
    except Exception as e:
        logger.error(f"update_plan error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to update plan: {e}"}


def delete_plan(plan_id: int, deleted_by: int) -> dict:
    try:
        row = get_plan_by_id(plan_id)
        name = row[1] if row else str(plan_id)
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "SELECT COUNT(*) FROM members WHERE membership_plan_id=? AND status='Active'",
                (plan_id,)
            )
            count = cursor.fetchone()[0]
            if count > 0:
                return {
                    "success": False,
                    "message": f"Cannot delete plan — {count} active member(s) using it."
                }
            cursor.execute("DELETE FROM membership_plans WHERE id=?", (plan_id,))
        _log_audit(deleted_by, ACTION_DELETE, plan_id, name)
        return {"success": True, "message": f"Plan '{name}' deleted."}
    except Exception as e:
        logger.error(f"delete_plan error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to delete plan: {e}"}


def toggle_plan_active(plan_id: int, updated_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE membership_plans SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id=?",
                (plan_id,)
            )
        return {"success": True, "message": "Plan status toggled."}
    except Exception as e:
        logger.error(f"toggle_plan_active error: {e}")
        return {"success": False, "message": str(e)}


# ─── MEMBERSHIP ASSIGNMENT ────────────────────────────────────────────────────
def calculate_expiry(start_date: date, duration_days: int) -> date:
    """Auto-calculate expiry = start_date + duration_days - 1."""
    return start_date + timedelta(days=duration_days - 1)


def assign_membership(member_id: int, plan_id: int,
                      start_date: date, assigned_by: int) -> dict:
    """
    Assign (or renew) a membership to a member.
    - Calculates expiry from plan duration.
    - Creates memberships record.
    - Updates members.membership_plan_id, expiry_date, status=Active.
    """
    try:
        plan = get_plan_by_id(plan_id)
        if not plan:
            return {"success": False, "message": "Membership plan not found."}

        duration_days = plan[2]
        expiry_date = calculate_expiry(start_date, duration_days)

        with DatabaseConnection() as (conn, cursor):
            # Expire any old active memberships
            cursor.execute(
                "UPDATE memberships SET status='Expired' WHERE member_id=? AND status='Active'",
                (member_id,)
            )
            # Create new membership record
            cursor.execute("""
                INSERT INTO memberships (member_id, plan_id, start_date, end_date, status, created_at)
                VALUES (?,?,?,?,?,GETDATE())
            """, (member_id, plan_id, start_date, expiry_date, "Active"))
            cursor.execute("SELECT @@IDENTITY")
            mem_id = int(cursor.fetchone()[0])

            # Update the member record
            cursor.execute("""
                UPDATE members SET
                    membership_plan_id=?, expiry_date=?, status='Active', updated_at=GETDATE()
                WHERE id=?
            """, (plan_id, expiry_date, member_id))

        _log_audit(
            assigned_by, ACTION_CREATE, mem_id,
            f"Assigned plan_id={plan_id} to member_id={member_id}, expires {expiry_date}"
        )
        return {
            "success": True,
            "membership_id": mem_id,
            "expiry_date": expiry_date,
            "message": f"Membership assigned. Expires on {expiry_date.strftime('%d %b %Y')}."
        }
    except Exception as e:
        logger.error(f"assign_membership error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to assign membership: {e}"}


def get_membership_history(member_id: int) -> list:
    """Full membership history for a member."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT ms.id, mp.plan_name, mp.price, ms.start_date, ms.end_date, ms.status, ms.created_at
                FROM   memberships ms
                JOIN   membership_plans mp ON ms.plan_id = mp.id
                WHERE  ms.member_id=?
                ORDER BY ms.created_at DESC
            """, (member_id,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_membership_history error: {e}")
        return []


def get_plan_usage_stats() -> list:
    """How many active members are on each plan."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT mp.plan_name, COUNT(m.id) AS member_count,
                       mp.price, mp.duration_days
                FROM   membership_plans mp
                LEFT JOIN members m ON m.membership_plan_id=mp.id AND m.status='Active'
                GROUP BY mp.plan_name, mp.price, mp.duration_days
                ORDER BY member_count DESC
            """)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_plan_usage_stats error: {e}")
        return []
