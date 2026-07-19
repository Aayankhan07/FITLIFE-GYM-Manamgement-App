"""
FitLife — Staff Service
User/staff management: list users, create, update, toggle status.
Trainers are managed via trainer_service; this handles other staff roles.
"""
import logging
from typing import Optional
from database.connection import DatabaseConnection
import services.auth_service as auth_svc
from config.constants import ALL_ROLES, ROLE_TRAINER

logger = logging.getLogger(__name__)


def _log_audit(user_id, action, record_id, detail=""):
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "INSERT INTO audit_logs(user_id,action,module,record_id,new_value,timestamp)"
                " VALUES(?,?,?,?,?,GETDATE())",
                (user_id, action, "Staff", record_id, detail)
            )
    except Exception as e:
        logger.error(f"Audit error: {e}")


def get_all_staff(branch_id: Optional[int] = None,
                  role: Optional[str] = None,
                  status: Optional[str] = None,
                  search: Optional[str] = None) -> list:
    """Returns all system users with their role and branch info."""
    try:
        sql = """
            SELECT u.id, u.username, u.full_name, u.email, u.phone,
                   r.role_name, b.branch_name, u.is_active,
                   u.last_login, u.created_at, u.branch_id
            FROM   users u
            JOIN   roles r ON u.role_id = r.id
            LEFT JOIN branches b ON u.branch_id = b.id
            WHERE  1=1
        """
        params = []
        if branch_id:
            sql += " AND u.branch_id=?"
            params.append(branch_id)
        if role:
            sql += " AND r.role_name=?"
            params.append(role)
        if status == "Active":
            sql += " AND u.is_active=1"
        elif status == "Inactive":
            sql += " AND u.is_active=0"
        if search:
            sql += " AND (u.full_name LIKE ? OR u.username LIKE ? OR u.email LIKE ?)"
            s = f"%{search}%"
            params += [s, s, s]
        sql += " ORDER BY r.role_name, u.full_name"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_all_staff error: {e}")
        return []


def get_staff_by_id(user_id: int) -> Optional[object]:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT u.id, u.username, u.full_name, u.email, u.phone,
                       r.role_name, r.id AS role_id, u.branch_id,
                       b.branch_name, u.is_active, u.created_at, u.last_login
                FROM   users u
                JOIN   roles r ON u.role_id = r.id
                LEFT JOIN branches b ON u.branch_id = b.id
                WHERE  u.id=?
            """, (user_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"get_staff_by_id error: {e}")
        return None


def create_staff(data: dict, created_by: int) -> dict:
    """Create a new system user account."""
    try:
        # Validate required
        for f in ["username", "full_name", "password", "role_id"]:
            if not data.get(f):
                return {"success": False, "message": f"Field '{f}' is required."}
        is_strong, err_msg = auth_svc.validate_password_strength(data["password"])
        if not is_strong:
            return {"success": False, "message": err_msg}
        pw_hash = auth_svc.hash_password(data["password"])
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO users
                    (username, password_hash, full_name, email, phone,
                     role_id, branch_id, is_active, theme_pref,
                     created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,1,'dark',GETDATE(),GETDATE())
            """, (
                data["username"].strip(), pw_hash, data["full_name"].strip(),
                data.get("email", ""), data.get("phone", ""),
                data["role_id"], data.get("branch_id")
            ))
            cursor.execute("SELECT @@IDENTITY")
            new_id = int(cursor.fetchone()[0])
        _log_audit(created_by, "CREATE", new_id, data["username"])
        return {"success": True, "user_id": new_id, "message": f"Account '{data['username']}' created."}
    except Exception as e:
        logger.error(f"create_staff error: {e}", exc_info=True)
        if "UNIQUE" in str(e).upper():
            return {"success": False, "message": "Username or email already exists."}
        return {"success": False, "message": f"Failed to create account: {e}"}


def update_staff(user_id: int, data: dict, updated_by: int) -> dict:
    """Update staff profile (not password)."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                UPDATE users SET
                    full_name=?, email=?, phone=?,
                    role_id=?, branch_id=?, updated_at=GETDATE()
                WHERE id=?
            """, (
                data["full_name"], data.get("email", ""), data.get("phone", ""),
                data["role_id"], data.get("branch_id"), user_id
            ))
        _log_audit(updated_by, "UPDATE", user_id, data["full_name"])
        return {"success": True, "message": "Staff updated."}
    except Exception as e:
        logger.error(f"update_staff error: {e}")
        return {"success": False, "message": str(e)}


def toggle_staff_status(user_id: int, admin_id: int) -> dict:
    """Activate or deactivate a user account."""
    try:
        row = get_staff_by_id(user_id)
        if not row:
            return {"success": False, "message": "User not found."}
        new_state = 0 if row[9] else 1
        label = "Activated" if new_state else "Deactivated"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE users SET is_active=?, updated_at=GETDATE() WHERE id=?",
                (new_state, user_id)
            )
        _log_audit(admin_id, f"TOGGLE_{label.upper()}", user_id, row[2])
        return {"success": True, "message": f"Account {label}."}
    except Exception as e:
        logger.error(f"toggle_staff_status error: {e}")
        return {"success": False, "message": str(e)}


def reset_staff_password(user_id: int, new_password: str, admin_id: int) -> dict:
    return auth_svc.admin_reset_password(admin_id, user_id, new_password)


def get_roles_dropdown() -> list:
    """Returns [(role_id, role_name)] for form dropdowns."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("SELECT id, role_name FROM roles ORDER BY id")
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_roles_dropdown error: {e}")
        return []


def get_staff_stats(branch_id: Optional[int] = None) -> dict:
    try:
        sql = """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN u.is_active=1 THEN 1 ELSE 0 END) AS active,
                   SUM(CASE WHEN u.is_active=0 THEN 1 ELSE 0 END) AS inactive
            FROM users u WHERE 1=1
        """
        params = []
        if branch_id:
            sql += " AND u.branch_id=?"; params.append(branch_id)
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return {"total": row[0], "active": row[1], "inactive": row[2]}
    except Exception as e:
        logger.error(f"get_staff_stats error: {e}")
        return {"total":0,"active":0,"inactive":0}
