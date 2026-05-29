"""
FitLife — Diet Plan Service
Full CRUD for diet plans + meal items, macros calculation, trainer verification.
"""
import logging
from typing import Optional
from database.connection import DatabaseConnection
from config.constants import PLAN_STATUS_DRAFT, PLAN_STATUS_PENDING, PLAN_STATUS_APPROVED

logger = logging.getLogger(__name__)


def _log_audit(user_id, action, record_id, detail=""):
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "INSERT INTO audit_logs(user_id,action,module,record_id,new_value,timestamp)"
                " VALUES(?,?,?,?,?,GETDATE())",
                (user_id, action, "Diet Plans", record_id, detail)
            )
    except Exception as e:
        logger.error(f"Audit error: {e}")


def get_all_diet_plans(branch_id: Optional[int] = None,
                       member_id: Optional[int] = None,
                       status: Optional[str] = None,
                       trainer_id: Optional[int] = None) -> list:
    try:
        sql = """
            SELECT dp.id, m.full_name, t.full_name AS trainer,
                   dp.plan_name, dp.goal, dp.daily_calories, dp.status,
                   dp.created_at, dp.member_id, dp.trainer_id, dp.notes
            FROM   diet_plans dp
            JOIN   members  m ON dp.member_id  = m.id
            LEFT JOIN trainers t ON dp.trainer_id = t.id
            WHERE  1=1
        """
        params = []
        if branch_id:
            sql += " AND m.branch_id=?"
            params.append(branch_id)
        if member_id:
            sql += " AND dp.member_id=?"
            params.append(member_id)
        if status:
            sql += " AND dp.status=?"
            params.append(status)
        if trainer_id:
            sql += " AND (dp.trainer_id=? OR m.trainer_id=?)"
            params.extend([trainer_id, trainer_id])
        sql += " ORDER BY dp.created_at DESC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_all_diet_plans error: {e}")
        return []


def get_diet_plan_by_id(plan_id: int) -> Optional[object]:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT dp.id, dp.member_id, dp.trainer_id, dp.plan_name,
                       dp.goal, dp.daily_calories, dp.protein_g, dp.carbs_g, dp.fat_g,
                       dp.status, dp.notes, dp.created_at,
                       m.full_name, t.full_name AS trainer_name
                FROM   diet_plans dp
                JOIN   members  m ON dp.member_id  = m.id
                LEFT JOIN trainers t ON dp.trainer_id = t.id
                WHERE  dp.id=?
            """, (plan_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"get_diet_plan_by_id error: {e}")
        return None


def create_diet_plan(data: dict, created_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO diet_plans
                    (member_id, trainer_id, plan_name, goal, daily_calories,
                     protein_g, carbs_g, fat_g, status, notes, created_by,
                     created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,GETDATE(),GETDATE())
            """, (
                data["member_id"], data.get("trainer_id"),
                data["plan_name"], data.get("goal", "Balanced Nutrition"),
                data.get("daily_calories", 2000),
                data.get("protein_g", 150), data.get("carbs_g", 200), data.get("fat_g", 65),
                data.get("status", PLAN_STATUS_DRAFT),
                data.get("notes", ""), created_by
            ))
            cursor.execute("SELECT @@IDENTITY")
            new_id = int(cursor.fetchone()[0])
        _log_audit(created_by, "CREATE", new_id, data["plan_name"])
        return {"success": True, "plan_id": new_id, "message": "Diet plan created."}
    except Exception as e:
        logger.error(f"create_diet_plan error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to create diet plan: {e}"}


def update_diet_plan(plan_id: int, data: dict, updated_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                UPDATE diet_plans SET
                    plan_name=?, goal=?, daily_calories=?,
                    protein_g=?, carbs_g=?, fat_g=?,
                    status=?, notes=?, trainer_id=?, updated_at=GETDATE()
                WHERE id=?
            """, (
                data["plan_name"], data.get("goal"),
                data.get("daily_calories", 2000),
                data.get("protein_g", 150), data.get("carbs_g", 200),
                data.get("fat_g", 65), data.get("status", PLAN_STATUS_DRAFT),
                data.get("notes", ""), data.get("trainer_id"), plan_id
            ))
        _log_audit(updated_by, "UPDATE", plan_id, data["plan_name"])
        return {"success": True, "message": "Diet plan updated."}
    except Exception as e:
        logger.error(f"update_diet_plan error: {e}")
        return {"success": False, "message": str(e)}


def delete_diet_plan(plan_id: int, deleted_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("DELETE FROM diet_plan_meals WHERE plan_id=?", (plan_id,))
            cursor.execute("DELETE FROM diet_plans WHERE id=?", (plan_id,))
        _log_audit(deleted_by, "DELETE", plan_id)
        return {"success": True, "message": "Diet plan deleted."}
    except Exception as e:
        logger.error(f"delete_diet_plan error: {e}")
        return {"success": False, "message": str(e)}


def approve_diet_plan(plan_id: int, trainer_id: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE diet_plans SET status=?, trainer_id=?, updated_at=GETDATE() WHERE id=?",
                (PLAN_STATUS_APPROVED, trainer_id, plan_id)
            )
        _log_audit(trainer_id, "PLAN_APPROVE", plan_id)
        return {"success": True, "message": "Diet plan approved."}
    except Exception as e:
        logger.error(f"approve_diet_plan error: {e}")
        return {"success": False, "message": str(e)}


def submit_diet_plan_for_review(plan_id: int, submitted_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE diet_plans SET status=?, updated_at=GETDATE() WHERE id=?",
                (PLAN_STATUS_PENDING, plan_id)
            )
        return {"success": True, "message": "Diet plan submitted for review."}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ── Meal Items ─────────────────────────────────────────────────────────────────
def get_meals(plan_id: int) -> list:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT id, meal_type, food_item, quantity_g, calories,
                       protein_g, carbs_g, fat_g, notes
                FROM   diet_plan_meals
                WHERE  plan_id=?
                ORDER BY meal_type, id
            """, (plan_id,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_meals error: {e}")
        return []


def add_meal(plan_id: int, data: dict) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO diet_plan_meals
                    (plan_id, meal_type, food_item, quantity_g,
                     calories, protein_g, carbs_g, fat_g, notes)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                plan_id, data["meal_type"], data["food_item"],
                data.get("quantity_g", 100),
                data.get("calories", 0), data.get("protein_g", 0),
                data.get("carbs_g", 0), data.get("fat_g", 0),
                data.get("notes", "")
            ))
            cursor.execute("SELECT @@IDENTITY")
            mid = int(cursor.fetchone()[0])
        return {"success": True, "meal_id": mid, "message": "Meal added."}
    except Exception as e:
        logger.error(f"add_meal error: {e}")
        return {"success": False, "message": str(e)}


def delete_meal(meal_id: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("DELETE FROM diet_plan_meals WHERE id=?", (meal_id,))
        return {"success": True, "message": "Meal removed."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_diet_plan_stats(branch_id: Optional[int] = None, member_id: Optional[int] = None) -> dict:
    try:
        sql = """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN dp.status='Active'  THEN 1 ELSE 0 END) AS active,
                   SUM(CASE WHEN dp.status='Pending Verification' THEN 1 ELSE 0 END) AS pending
            FROM diet_plans dp
            JOIN members m ON dp.member_id=m.id WHERE 1=1
        """
        params = []
        if branch_id:
            sql += " AND m.branch_id=?"
            params.append(branch_id)
        if member_id:
            sql += " AND dp.member_id=?"
            params.append(member_id)
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return {"total": row[0], "active": row[1], "pending": row[2]}
    except Exception as e:
        logger.error(f"get_diet_plan_stats error: {e}")
        return {"total": 0, "active": 0, "pending": 0}
