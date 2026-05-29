"""
FitLife — Trainer Service
Full CRUD + workload + assigned members.
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
                (user_id, action, "Trainers", record_id, detail)
            )
    except Exception as e:
        logger.error(f"Audit log error: {e}")


def get_all_trainers(branch_id: Optional[int] = None,
                     search: Optional[str] = None) -> list:
    try:
        sql = """
            SELECT t.id, t.full_name, t.cnic, t.phone, t.email,
                   b.branch_name, t.specialization, t.monthly_salary,
                   t.hire_date, t.status, t.performance_rating,
                   t.qualification,
                   (SELECT COUNT(*) FROM members m WHERE m.trainer_id = t.id AND m.status='Active') AS member_count
            FROM   trainers t
            JOIN   branches b ON t.branch_id = b.id
            WHERE  1=1
        """
        params = []
        if branch_id:
            sql += " AND t.branch_id=?"
            params.append(branch_id)
        if search:
            sql += " AND (t.full_name LIKE ? OR t.cnic LIKE ? OR t.email LIKE ?)"
            s = f"%{search}%"
            params += [s, s, s]
        sql += " ORDER BY t.full_name"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_all_trainers error: {e}")
        return []


def get_trainer_by_id(trainer_id: int) -> Optional[object]:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT t.id, t.user_id, t.branch_id, t.full_name, t.cnic,
                       t.phone, t.email, t.address, t.photo_path,
                       t.specialization, t.monthly_salary, t.hire_date,
                       t.qualification, t.certifications, t.status,
                       t.performance_rating, t.created_at,
                       b.branch_name
                FROM   trainers t
                JOIN   branches b ON t.branch_id = b.id
                WHERE  t.id=?
            """, (trainer_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"get_trainer_by_id error: {e}")
        return None


def get_trainer_by_user_id(user_id: int) -> Optional[object]:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT t.id, t.branch_id, t.full_name, t.specialization,
                       t.monthly_salary, b.branch_name
                FROM   trainers t
                JOIN   branches b ON t.branch_id = b.id
                WHERE  t.user_id=?
            """, (user_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"get_trainer_by_user_id error: {e}")
        return None


def get_trainers_for_branch(branch_id: int) -> list:
    """Lightweight list for dropdowns."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "SELECT id, full_name, specialization FROM trainers WHERE branch_id=? AND status='Active' ORDER BY full_name",
                (branch_id,)
            )
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_trainers_for_branch error: {e}")
        return []


def get_assigned_members(trainer_id: int) -> list:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT m.id, m.full_name, m.phone, m.fitness_goal,
                       m.status, m.expiry_date, mp.plan_name
                FROM   members m
                LEFT JOIN membership_plans mp ON m.membership_plan_id = mp.id
                WHERE  m.trainer_id=?
                ORDER BY m.full_name
            """, (trainer_id,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_assigned_members error: {e}")
        return []


def create_trainer(data: dict, created_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO trainers
                    (user_id, branch_id, full_name, cnic, phone, email,
                     address, photo_path, specialization, monthly_salary,
                     hire_date, qualification, certifications, status,
                     created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,GETDATE(),GETDATE())
            """, (
                data.get("user_id"), data["branch_id"], data["full_name"],
                data["cnic"], data["phone"], data.get("email"),
                data.get("address"), data.get("photo_path"),
                data.get("specialization", "General Fitness"),
                data["monthly_salary"], data["hire_date"],
                data.get("qualification"), data.get("certifications"),
                data.get("status", "Active"),
            ))
            cursor.execute("SELECT @@IDENTITY")
            new_id = int(cursor.fetchone()[0])
        _log_audit(created_by, ACTION_CREATE, new_id, data["full_name"])
        return {"success": True, "trainer_id": new_id, "message": "Trainer added successfully."}
    except Exception as e:
        logger.error(f"create_trainer error: {e}", exc_info=True)
        if "UNIQUE" in str(e) or "unique" in str(e).lower():
            return {"success": False, "message": "A trainer with this CNIC already exists."}
        return {"success": False, "message": f"Failed to create trainer: {e}"}


def update_trainer(trainer_id: int, data: dict, updated_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                UPDATE trainers SET
                    branch_id=?, full_name=?, cnic=?, phone=?, email=?,
                    address=?, photo_path=?, specialization=?,
                    monthly_salary=?, hire_date=?, qualification=?,
                    certifications=?, status=?, updated_at=GETDATE()
                WHERE id=?
            """, (
                data["branch_id"], data["full_name"], data["cnic"],
                data["phone"], data.get("email"), data.get("address"),
                data.get("photo_path"),
                data.get("specialization", "General Fitness"),
                data["monthly_salary"], data["hire_date"],
                data.get("qualification"), data.get("certifications"),
                data.get("status", "Active"), trainer_id,
            ))
        _log_audit(updated_by, ACTION_UPDATE, trainer_id, data["full_name"])
        return {"success": True, "message": "Trainer updated successfully."}
    except Exception as e:
        logger.error(f"update_trainer error: {e}", exc_info=True)
        if "UNIQUE" in str(e) or "unique" in str(e).lower():
            return {"success": False, "message": "CNIC already in use by another trainer."}
        return {"success": False, "message": f"Failed to update trainer: {e}"}


def delete_trainer(trainer_id: int, deleted_by: int) -> dict:
    try:
        row = get_trainer_by_id(trainer_id)
        name = row[3] if row else str(trainer_id)
        with DatabaseConnection() as (conn, cursor):
            # Unlink members first
            cursor.execute("UPDATE members SET trainer_id=NULL WHERE trainer_id=?", (trainer_id,))
            cursor.execute("DELETE FROM trainers WHERE id=?", (trainer_id,))
        _log_audit(deleted_by, ACTION_DELETE, trainer_id, name)
        return {"success": True, "message": f"Trainer '{name}' deleted successfully."}
    except Exception as e:
        logger.error(f"delete_trainer error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to delete trainer: {e}"}


def get_trainer_stats(branch_id: Optional[int] = None) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            sql = "SELECT COUNT(*), AVG(monthly_salary), AVG(performance_rating) FROM trainers WHERE 1=1"
            params = []
            if branch_id:
                sql += " AND branch_id=?"
                params.append(branch_id)
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return {
                "total": row[0] or 0,
                "avg_salary": float(row[1] or 0),
                "avg_rating": float(row[2] or 0),
            }
    except Exception as e:
        logger.error(f"get_trainer_stats error: {e}")
        return {"total": 0, "avg_salary": 0, "avg_rating": 0}
