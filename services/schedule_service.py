"""
FitLife — Scheduling Service
Trainer schedule slots, class bookings, conflict detection.
"""
import logging
from typing import Optional
from datetime import date, time
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)

SLOT_STATUSES = ["Available","Booked","Cancelled","Completed"]
CLASS_TYPES   = ["Personal Training","Group Class","Cardio Session",
                 "HIIT Class","Yoga","Boxing","Assessment","Other"]


def _log_audit(user_id, action, record_id, detail=""):
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "INSERT INTO audit_logs(user_id,action,module,record_id,new_value,timestamp)"
                " VALUES(?,?,?,?,?,GETDATE())",
                (user_id, action, "Scheduling", record_id, detail)
            )
    except Exception as e:
        logger.error(f"Audit error: {e}")


# ── Schedule Slots ─────────────────────────────────────────────────────────────
def get_schedule(branch_id: Optional[int] = None,
                 trainer_id: Optional[int] = None,
                 slot_date: Optional[date] = None,
                 status: Optional[str] = None) -> list:
    try:
        sql = """
            SELECT s.id, t.full_name AS trainer, m.full_name AS member,
                   s.slot_date, s.start_time, s.end_time,
                   s.class_type, s.status, s.notes,
                   b.branch_name, s.trainer_id, s.member_id, s.branch_id
            FROM   trainer_schedule s
            JOIN   trainers t ON s.trainer_id = t.id
            LEFT JOIN members  m ON s.member_id  = m.id
            JOIN   branches b ON s.branch_id  = b.id
            WHERE  1=1
        """
        params = []
        if branch_id:
            sql += " AND s.branch_id=?"; params.append(branch_id)
        if trainer_id:
            sql += " AND s.trainer_id=?"; params.append(trainer_id)
        if slot_date:
            sql += " AND s.slot_date=?"; params.append(slot_date)
        if status:
            sql += " AND s.status=?"; params.append(status)
        sql += " ORDER BY s.slot_date, s.start_time"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_schedule error: {e}")
        return []


def get_schedule_range(branch_id: int, date_from: date, date_to: date) -> list:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT s.id, t.full_name, m.full_name, s.slot_date,
                       s.start_time, s.end_time, s.class_type, s.status,
                       s.notes, s.trainer_id, s.member_id
                FROM   trainer_schedule s
                JOIN   trainers t ON s.trainer_id=t.id
                LEFT JOIN members m ON s.member_id=m.id
                WHERE  s.branch_id=? AND s.slot_date BETWEEN ? AND ?
                ORDER  BY s.slot_date, s.start_time
            """, (branch_id, date_from, date_to))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_schedule_range error: {e}")
        return []


def create_slot(data: dict, created_by: int) -> dict:
    try:
        # Conflict check: same trainer, same date, overlapping times
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT COUNT(*) FROM trainer_schedule
                WHERE  trainer_id=? AND slot_date=?
                AND    status NOT IN ('Cancelled')
                AND    NOT (end_time <= ? OR start_time >= ?)
            """, (data["trainer_id"], data["slot_date"],
                  data["start_time"], data["end_time"]))
            conflicts = cursor.fetchone()[0]
        if conflicts > 0:
            return {"success": False, "message": "Trainer has a conflicting slot at this time."}

        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO trainer_schedule
                    (branch_id, trainer_id, member_id, slot_date,
                     start_time, end_time, class_type, status, notes,
                     created_by, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,GETDATE(),GETDATE())
            """, (
                data["branch_id"], data["trainer_id"], data.get("member_id"),
                data["slot_date"], data["start_time"], data["end_time"],
                data.get("class_type", "Personal Training"),
                data.get("status", "Available"),
                data.get("notes", ""), created_by
            ))
            cursor.execute("SELECT @@IDENTITY")
            new_id = int(cursor.fetchone()[0])
        _log_audit(created_by, "CREATE", new_id, str(data["slot_date"]))
        return {"success": True, "slot_id": new_id, "message": "Slot created."}
    except Exception as e:
        logger.error(f"create_slot error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to create slot: {e}"}


def update_slot(slot_id: int, data: dict, updated_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                UPDATE trainer_schedule SET
                    trainer_id=?, member_id=?, slot_date=?,
                    start_time=?, end_time=?, class_type=?,
                    status=?, notes=?, updated_at=GETDATE()
                WHERE id=?
            """, (
                data["trainer_id"], data.get("member_id"),
                data["slot_date"], data["start_time"], data["end_time"],
                data.get("class_type", "Personal Training"),
                data.get("status", "Available"), data.get("notes", ""),
                slot_id
            ))
        _log_audit(updated_by, "UPDATE", slot_id)
        return {"success": True, "message": "Slot updated."}
    except Exception as e:
        logger.error(f"update_slot error: {e}")
        return {"success": False, "message": str(e)}


def cancel_slot(slot_id: int, cancelled_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE trainer_schedule SET status='Cancelled', updated_at=GETDATE() WHERE id=?",
                (slot_id,)
            )
        _log_audit(cancelled_by, "CANCEL", slot_id)
        return {"success": True, "message": "Slot cancelled."}
    except Exception as e:
        logger.error(f"cancel_slot error: {e}")
        return {"success": False, "message": str(e)}


def mark_slot_complete(slot_id: int, updated_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE trainer_schedule SET status='Completed', updated_at=GETDATE() WHERE id=?",
                (slot_id,)
            )
        _log_audit(updated_by, "COMPLETE", slot_id)
        return {"success": True, "message": "Session marked complete."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def delete_slot(slot_id: int, deleted_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("DELETE FROM trainer_schedule WHERE id=?", (slot_id,))
        _log_audit(deleted_by, "DELETE", slot_id)
        return {"success": True, "message": "Slot deleted."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_schedule_stats(branch_id: Optional[int] = None,
                       slot_date: Optional[date] = None) -> dict:
    try:
        sql = """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status='Booked'    THEN 1 ELSE 0 END) AS booked,
                   SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END) AS available,
                   SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) AS completed,
                   SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END) AS cancelled
            FROM trainer_schedule WHERE 1=1
        """
        params = []
        if branch_id:
            sql += " AND branch_id=?"; params.append(branch_id)
        if slot_date:
            sql += " AND slot_date=?"; params.append(slot_date)
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return {
                "total": row[0], "booked": row[1],
                "available": row[2], "completed": row[3], "cancelled": row[4]
            }
    except Exception as e:
        logger.error(f"get_schedule_stats error: {e}")
        return {"total":0,"booked":0,"available":0,"completed":0,"cancelled":0}
