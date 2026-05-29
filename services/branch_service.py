"""
FitLife — Branch Service
Full CRUD + stats + manager assignment.
"""
import logging
from typing import Optional
from database.connection import DatabaseConnection
from config.constants import ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE

logger = logging.getLogger(__name__)


def _log_audit(user_id, action, record_id, detail=""):
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "INSERT INTO audit_logs (user_id,action,module,record_id,new_value,timestamp)"
                " VALUES (?,?,?,?,?,GETDATE())",
                (user_id, action, "Branches", record_id, detail)
            )
    except Exception as e:
        logger.error(f"Audit log error: {e}")


def get_all_branches(search: Optional[str] = None) -> list:
    try:
        sql = """
            SELECT b.id, b.branch_name, b.city, b.address, b.phone, b.email,
                   b.capacity, b.opening_date, b.status,
                   u.full_name AS manager_name,
                   (SELECT COUNT(*) FROM members m WHERE m.branch_id=b.id AND m.status='Active') AS member_count,
                   (SELECT COUNT(*) FROM trainers t WHERE t.branch_id=b.id AND t.status='Active') AS trainer_count,
                   b.manager_id
            FROM   branches b
            LEFT JOIN users u ON b.manager_id = u.id
            WHERE  1=1
        """
        params = []
        if search:
            sql += " AND (b.branch_name LIKE ? OR b.city LIKE ? OR b.phone LIKE ?)"
            s = f"%{search}%"
            params += [s, s, s]
        sql += " ORDER BY b.branch_name"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_all_branches error: {e}")
        return []


def get_branch_by_id(branch_id: int) -> Optional[object]:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT b.id, b.branch_name, b.city, b.address, b.phone,
                       b.email, b.capacity, b.opening_date, b.status,
                       b.manager_id, u.full_name AS manager_name,
                       b.created_at, b.updated_at
                FROM   branches b
                LEFT JOIN users u ON b.manager_id = u.id
                WHERE  b.id=?
            """, (branch_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"get_branch_by_id error: {e}")
        return None


def get_all_branches_dropdown() -> list:
    """Lightweight list for dropdowns: [(id, branch_name), ...]"""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "SELECT id, branch_name FROM branches WHERE status='Active' ORDER BY branch_name"
            )
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_all_branches_dropdown error: {e}")
        return []


def get_managers_dropdown() -> list:
    """Users with Manager role for assignment dropdown."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT u.id, u.full_name
                FROM   users u
                JOIN   roles r ON u.role_id = r.id
                WHERE  r.role_name='Manager' AND u.is_active=1
                ORDER BY u.full_name
            """)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_managers_dropdown error: {e}")
        return []


def create_branch(data: dict, created_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO branches
                    (branch_name, city, address, phone, email, capacity,
                     opening_date, status, manager_id, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,GETDATE(),GETDATE())
            """, (
                data["branch_name"], data["city"], data["address"],
                data["phone"], data.get("email"),
                data.get("capacity", 100),
                data["opening_date"],
                data.get("status", "Active"),
                data.get("manager_id"),
            ))
            cursor.execute("SELECT @@IDENTITY")
            new_id = int(cursor.fetchone()[0])
        # Update manager's branch_id
        if data.get("manager_id"):
            with DatabaseConnection() as (conn, cursor):
                cursor.execute(
                    "UPDATE users SET branch_id=? WHERE id=?",
                    (new_id, data["manager_id"])
                )
        _log_audit(created_by, ACTION_CREATE, new_id, data["branch_name"])
        return {"success": True, "branch_id": new_id, "message": "Branch created successfully."}
    except Exception as e:
        logger.error(f"create_branch error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to create branch: {e}"}


def update_branch(branch_id: int, data: dict, updated_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                UPDATE branches SET
                    branch_name=?, city=?, address=?, phone=?, email=?,
                    capacity=?, opening_date=?, status=?, manager_id=?,
                    updated_at=GETDATE()
                WHERE id=?
            """, (
                data["branch_name"], data["city"], data["address"],
                data["phone"], data.get("email"),
                data.get("capacity", 100),
                data["opening_date"],
                data.get("status", "Active"),
                data.get("manager_id"),
                branch_id,
            ))
        if data.get("manager_id"):
            with DatabaseConnection() as (conn, cursor):
                cursor.execute(
                    "UPDATE users SET branch_id=? WHERE id=?",
                    (branch_id, data["manager_id"])
                )
        _log_audit(updated_by, ACTION_UPDATE, branch_id, data["branch_name"])
        return {"success": True, "message": "Branch updated successfully."}
    except Exception as e:
        logger.error(f"update_branch error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to update branch: {e}"}


def delete_branch(branch_id: int, deleted_by: int) -> dict:
    try:
        row = get_branch_by_id(branch_id)
        name = row[1] if row else str(branch_id)
        with DatabaseConnection() as (conn, cursor):
            # Check no active members
            cursor.execute(
                "SELECT COUNT(*) FROM members WHERE branch_id=? AND status='Active'",
                (branch_id,)
            )
            count = cursor.fetchone()[0]
            if count > 0:
                return {
                    "success": False,
                    "message": f"Cannot delete branch — {count} active member(s) assigned to it. "
                               "Reassign or deactivate members first."
                }
            cursor.execute("DELETE FROM branches WHERE id=?", (branch_id,))
        _log_audit(deleted_by, ACTION_DELETE, branch_id, name)
        return {"success": True, "message": f"Branch '{name}' deleted successfully."}
    except Exception as e:
        logger.error(f"delete_branch error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to delete branch: {e}"}


def get_branch_stats(branch_id: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM members  WHERE branch_id=? AND status='Active') AS members,
                    (SELECT COUNT(*) FROM trainers WHERE branch_id=? AND status='Active') AS trainers,
                    (SELECT COUNT(*) FROM equipment WHERE branch_id=?)                    AS equipment,
                    (SELECT ISNULL(SUM(amount),0) FROM payments p
                     JOIN   members m ON p.member_id=m.id
                     WHERE  m.branch_id=? AND p.status='Paid'
                     AND    MONTH(p.payment_date)=MONTH(GETDATE())
                     AND    YEAR(p.payment_date)=YEAR(GETDATE()))                         AS revenue_this_month
            """, (branch_id, branch_id, branch_id, branch_id))
            row = cursor.fetchone()
            return {
                "members":  row[0], "trainers": row[1],
                "equipment": row[2], "revenue_this_month": float(row[3]),
            }
    except Exception as e:
        logger.error(f"get_branch_stats error: {e}")
        return {"members": 0, "trainers": 0, "equipment": 0, "revenue_this_month": 0}
