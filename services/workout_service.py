"""
FitLife — Workout Plan Service
AI-assisted + manual plan creation, trainer verification workflow,
exercise management, member plan assignment.
"""
import logging
from datetime import date
from typing import Optional
from database.connection import DatabaseConnection
from config.constants import (
    PLAN_STATUS_DRAFT, PLAN_STATUS_PENDING, PLAN_STATUS_APPROVED,
    PLAN_STATUS_ACTIVE, PLAN_STATUS_REJECTED, ACTION_CREATE, ACTION_UPDATE
)

logger = logging.getLogger(__name__)


def _log_audit(user_id, action, record_id, detail=""):
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "INSERT INTO audit_logs(user_id,action,module,record_id,new_value,timestamp)"
                " VALUES(?,?,?,?,?,GETDATE())",
                (user_id, action, "Workout Plans", record_id, detail)
            )
    except Exception as e:
        logger.error(f"Audit error: {e}")


# ── Plan CRUD ──────────────────────────────────────────────────────────────────
def get_all_plans(branch_id: Optional[int] = None,
                  member_id: Optional[int] = None,
                  status: Optional[str] = None,
                  trainer_id: Optional[int] = None) -> list:
    try:
        sql = """
            SELECT wp.id, m.full_name, t.full_name AS trainer,
                   wp.plan_name, wp.goal, wp.weeks, wp.status,
                   wp.created_at, wp.updated_at, wp.member_id, wp.trainer_id,
                   wp.notes
            FROM   workout_plans wp
            JOIN   members  m ON wp.member_id  = m.id
            LEFT JOIN trainers t ON wp.trainer_id = t.id
            WHERE  1=1
        """
        params = []
        if branch_id:
            sql += " AND m.branch_id=?"
            params.append(branch_id)
        if member_id:
            sql += " AND wp.member_id=?"
            params.append(member_id)
        if status:
            sql += " AND wp.status=?"
            params.append(status)
        if trainer_id:
            sql += " AND (wp.trainer_id=? OR m.trainer_id=?)"
            params.extend([trainer_id, trainer_id])
        sql += " ORDER BY wp.created_at DESC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_all_plans error: {e}")
        return []


def get_plan_by_id(plan_id: int) -> Optional[object]:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT wp.id, wp.member_id, wp.trainer_id, wp.plan_name,
                       wp.goal, wp.weeks, wp.status, wp.notes,
                       wp.created_at, wp.updated_at,
                       m.full_name, t.full_name AS trainer_name
                FROM   workout_plans wp
                JOIN   members  m ON wp.member_id  = m.id
                LEFT JOIN trainers t ON wp.trainer_id = t.id
                WHERE  wp.id=?
            """, (plan_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"get_plan_by_id error: {e}")
        return None


def create_plan(data: dict, created_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO workout_plans
                    (member_id, trainer_id, plan_name, goal, weeks,
                     status, notes, created_by, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,GETDATE(),GETDATE())
            """, (
                data["member_id"], data.get("trainer_id"),
                data["plan_name"], data.get("goal", "General Fitness"),
                data.get("weeks", 4), data.get("status", PLAN_STATUS_DRAFT),
                data.get("notes", ""), created_by
            ))
            cursor.execute("SELECT @@IDENTITY")
            new_id = int(cursor.fetchone()[0])
        _log_audit(created_by, ACTION_CREATE, new_id, data["plan_name"])
        return {"success": True, "plan_id": new_id, "message": "Workout plan created."}
    except Exception as e:
        logger.error(f"create_plan error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to create plan: {e}"}


def update_plan(plan_id: int, data: dict, updated_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                UPDATE workout_plans SET
                    plan_name=?, goal=?, weeks=?, status=?, notes=?,
                    trainer_id=?, updated_at=GETDATE()
                WHERE id=?
            """, (
                data["plan_name"], data.get("goal"),
                data.get("weeks", 4), data.get("status", PLAN_STATUS_DRAFT),
                data.get("notes", ""), data.get("trainer_id"), plan_id
            ))
        _log_audit(updated_by, ACTION_UPDATE, plan_id, data["plan_name"])
        return {"success": True, "message": "Plan updated."}
    except Exception as e:
        logger.error(f"update_plan error: {e}")
        return {"success": False, "message": str(e)}


def delete_plan(plan_id: int, deleted_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("DELETE FROM workout_plan_exercises WHERE plan_id=?", (plan_id,))
            cursor.execute("DELETE FROM workout_plans WHERE id=?", (plan_id,))
        _log_audit(deleted_by, "DELETE", plan_id)
        return {"success": True, "message": "Plan deleted."}
    except Exception as e:
        logger.error(f"delete_plan error: {e}")
        return {"success": False, "message": str(e)}


def submit_for_review(plan_id: int, submitted_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE workout_plans SET status=?, updated_at=GETDATE() WHERE id=?",
                (PLAN_STATUS_PENDING, plan_id)
            )
        _log_audit(submitted_by, "SUBMIT_REVIEW", plan_id)
        return {"success": True, "message": "Plan submitted for trainer review."}
    except Exception as e:
        logger.error(f"submit_for_review error: {e}")
        return {"success": False, "message": str(e)}


def approve_plan(plan_id: int, trainer_id: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE workout_plans SET status=?, trainer_id=?, updated_at=GETDATE() WHERE id=?",
                (PLAN_STATUS_APPROVED, trainer_id, plan_id)
            )
        _log_audit(trainer_id, "PLAN_APPROVE", plan_id)
        return {"success": True, "message": "Plan approved."}
    except Exception as e:
        logger.error(f"approve_plan error: {e}")
        return {"success": False, "message": str(e)}


def reject_plan(plan_id: int, trainer_id: int, reason: str) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE workout_plans SET status=?, notes=?, updated_at=GETDATE() WHERE id=?",
                (PLAN_STATUS_REJECTED, reason, plan_id)
            )
        _log_audit(trainer_id, "PLAN_REJECT", plan_id, reason)
        return {"success": True, "message": "Plan rejected with feedback."}
    except Exception as e:
        logger.error(f"reject_plan error: {e}")
        return {"success": False, "message": str(e)}


# ── Exercises CRUD ─────────────────────────────────────────────────────────────
def get_exercises(plan_id: int) -> list:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT id, exercise_name, sets, reps, rest_seconds,
                       day_of_week, notes, order_index
                FROM   workout_plan_exercises
                WHERE  plan_id=?
                ORDER BY day_of_week, order_index
            """, (plan_id,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_exercises error: {e}")
        return []


def add_exercise(plan_id: int, data: dict, added_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO workout_plan_exercises
                    (plan_id, exercise_name, sets, reps, rest_seconds,
                     day_of_week, notes, order_index)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                plan_id, data["exercise_name"],
                data.get("sets", 3), data.get("reps", 10),
                data.get("rest_seconds", 60),
                data.get("day_of_week", "Monday"),
                data.get("notes", ""),
                data.get("order_index", 0)
            ))
            cursor.execute("SELECT @@IDENTITY")
            eid = int(cursor.fetchone()[0])
        return {"success": True, "exercise_id": eid, "message": "Exercise added."}
    except Exception as e:
        logger.error(f"add_exercise error: {e}")
        return {"success": False, "message": str(e)}


def delete_exercise(exercise_id: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("DELETE FROM workout_plan_exercises WHERE id=?", (exercise_id,))
        return {"success": True, "message": "Exercise removed."}
    except Exception as e:
        logger.error(f"delete_exercise error: {e}")
        return {"success": False, "message": str(e)}


# ── Stats ──────────────────────────────────────────────────────────────────────
def get_plan_stats(branch_id: Optional[int] = None, member_id: Optional[int] = None) -> dict:
    try:
        sql = """
            SELECT
                COUNT(*)                                                  AS total,
                SUM(CASE WHEN wp.status='Active'           THEN 1 ELSE 0 END) AS active,
                SUM(CASE WHEN wp.status='Pending Verification' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN wp.status='Trainer Approved' THEN 1 ELSE 0 END) AS approved
            FROM workout_plans wp
            JOIN members m ON wp.member_id=m.id WHERE 1=1
        """
        params = []
        if branch_id:
            sql += " AND m.branch_id=?"
            params.append(branch_id)
        if member_id:
            sql += " AND wp.member_id=?"
            params.append(member_id)
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return {
                "total": row[0], "active": row[1],
                "pending": row[2], "approved": row[3]
            }
    except Exception as e:
        logger.error(f"get_plan_stats error: {e}")
        return {"total":0,"active":0,"pending":0,"approved":0}
