"""
FitLife — Progress Service
Body measurement logs, weight tracking, goal milestone records.
"""
import logging
from typing import Optional
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


def log_progress(member_id: int, data: dict, logged_by: int) -> dict:
    """Log a body measurement entry."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO progress_logs
                    (member_id, log_date, weight_kg, body_fat_pct,
                     chest_cm, waist_cm, hips_cm, arms_cm, legs_cm,
                     notes, logged_by, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,GETDATE())
            """, (
                member_id,
                data.get("log_date"),
                data.get("weight_kg"),
                data.get("body_fat_pct"),
                data.get("chest_cm"),
                data.get("waist_cm"),
                data.get("hips_cm"),
                data.get("arms_cm"),
                data.get("legs_cm"),
                data.get("notes", ""),
                logged_by,
            ))
            cursor.execute("SELECT @@IDENTITY")
            log_id = int(cursor.fetchone()[0])
            # Keep member record weight synced
            if data.get("weight_kg"):
                cursor.execute(
                    "UPDATE members SET weight_kg=?, updated_at=GETDATE() WHERE id=?",
                    (data["weight_kg"], member_id)
                )
        return {"success": True, "log_id": log_id, "message": "Progress logged."}
    except Exception as e:
        logger.error(f"log_progress error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to log progress: {e}"}


def get_progress_logs(member_id: int, limit: int = 30) -> list:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT pl.id, pl.member_id, pl.log_date, pl.weight_kg, pl.body_fat_pct,
                       pl.chest_cm, pl.waist_cm, pl.hips_cm,
                       pl.arms_cm, pl.legs_cm, pl.notes, pl.created_at
                FROM   progress_logs pl
                WHERE  pl.member_id=?
                ORDER  BY pl.log_date DESC
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
            """, (member_id, limit))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_progress_logs error: {e}")
        return []


def delete_progress_log(log_id: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("DELETE FROM progress_logs WHERE id=?", (log_id,))
        return {"success": True, "message": "Log entry deleted."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_weight_trend(member_id: int, last_n: int = 12) -> list:
    """Returns [(date, weight_kg)] for charting."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT TOP (?) log_date, weight_kg
                FROM   progress_logs
                WHERE  member_id=? AND weight_kg IS NOT NULL
                ORDER  BY log_date ASC
            """, (last_n, member_id))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_weight_trend error: {e}")
        return []


def get_member_progress_summary(member_id: int) -> dict:
    """First log vs latest log comparison."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT TOP 1 log_date, weight_kg, body_fat_pct
                FROM progress_logs WHERE member_id=? ORDER BY log_date ASC
            """, (member_id,))
            first = cursor.fetchone()
            cursor.execute("""
                SELECT TOP 1 log_date, weight_kg, body_fat_pct
                FROM progress_logs WHERE member_id=? ORDER BY log_date DESC
            """, (member_id,))
            latest = cursor.fetchone()
            cursor.execute(
                "SELECT COUNT(*) FROM progress_logs WHERE member_id=?", (member_id,)
            )
            total_logs = cursor.fetchone()[0]
        if not first or not latest:
            return {"first": None, "latest": None, "total_logs": 0, "weight_change": 0}
        weight_change = 0
        if first[1] and latest[1]:
            weight_change = round(float(latest[1]) - float(first[1]), 1)
        return {
            "first":  {"date": first[0],  "weight": first[1],  "fat": first[2]},
            "latest": {"date": latest[0], "weight": latest[1], "fat": latest[2]},
            "total_logs":    total_logs,
            "weight_change": weight_change,
        }
    except Exception as e:
        logger.error(f"get_member_progress_summary error: {e}")
        return {"first": None, "latest": None, "total_logs": 0, "weight_change": 0}


def get_branch_progress_overview(branch_id: int) -> list:
    """All members with their latest weight for branch overview."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT m.id, m.full_name, m.weight_kg, m.fitness_goal,
                       (SELECT TOP 1 pl.log_date FROM progress_logs pl
                        WHERE pl.member_id=m.id ORDER BY pl.log_date DESC) AS last_log_date,
                       (SELECT COUNT(*) FROM progress_logs pl WHERE pl.member_id=m.id) AS total_logs
                FROM   members m
                WHERE  m.branch_id=? AND m.status='Active'
                ORDER BY m.full_name
            """, (branch_id,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_branch_progress_overview error: {e}")
        return []


def get_all_progress_overview(branch_id: Optional[int] = None, member_id: Optional[int] = None, trainer_id: Optional[int] = None) -> list:
    """All active members with their latest progress — works for Admin (branch_id=None), Manager, Trainer."""
    try:
        with DatabaseConnection() as (conn, cursor):
            sql = """
                SELECT m.id, m.full_name, m.weight_kg, m.fitness_goal,
                       (SELECT TOP 1 pl.log_date FROM progress_logs pl
                        WHERE pl.member_id=m.id ORDER BY pl.log_date DESC) AS last_log_date,
                       (SELECT COUNT(*) FROM progress_logs pl WHERE pl.member_id=m.id) AS total_logs
                FROM   members m
                WHERE  m.status='Active'
            """
            params = []
            if branch_id:
                sql += " AND m.branch_id=?"
                params.append(branch_id)
            if member_id:
                sql += " AND m.id=?"
                params.append(member_id)
            if trainer_id:
                sql += " AND m.trainer_id=?"
                params.append(trainer_id)
            sql += " ORDER BY m.full_name"
            
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_all_progress_overview error: {e}")
        return []
