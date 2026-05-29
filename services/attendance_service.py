"""
FitLife — Attendance Service
Check-in/out, daily log, calendar data, reports.
Supports both Members and Trainers.
"""
import logging
from datetime import date, datetime
from typing import Optional
from database.connection import DatabaseConnection
from config.constants import ACTION_CREATE, ATTEND_PRESENT, ATTEND_LATE

logger = logging.getLogger(__name__)


def _log_audit(user_id, action, record_id, detail=""):
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "INSERT INTO audit_logs(user_id,action,module,record_id,new_value,timestamp)"
                " VALUES(?,?,?,?,?,GETDATE())",
                (user_id, action, "Attendance", record_id, detail)
            )
    except Exception as e:
        logger.error(f"Audit error: {e}")


# ── Check-in / Check-out ──────────────────────────────────────────────────────
def check_in(entity_id: int, branch_id: int, recorded_by: int,
             notes: str = "", is_trainer: bool = False) -> dict:
    try:
        today = date.today()
        # Check if already checked in today
        col = "trainer_id" if is_trainer else "member_id"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                f"SELECT id, check_out_time FROM attendance WHERE {col}=? AND date=?",
                (entity_id, today)
            )
            row = cursor.fetchone()

        if row:
            if row[1] is None:
                return {"success": False, "message": "Already checked in today."}
            # Re-check-in after checkout
        now = datetime.now()
        # Late if after 9:00 AM
        status = ATTEND_LATE if now.hour >= 9 else ATTEND_PRESENT
        with DatabaseConnection() as (conn, cursor):
            if not branch_id:
                if is_trainer:
                    cursor.execute("SELECT branch_id FROM trainers WHERE id=?", (entity_id,))
                else:
                    cursor.execute("SELECT branch_id FROM members WHERE id=?", (entity_id,))
                b_row = cursor.fetchone()
                if b_row:
                    branch_id = b_row[0]
                else:
                    return {"success": False, "message": "Branch not found."}

            if row:
                cursor.execute(
                    "UPDATE attendance SET check_in_time=?, check_out_time=NULL, status=? WHERE id=?",
                    (now, status, row[0])
                )
                att_id = row[0]
            else:
                if is_trainer:
                    cursor.execute("""
                        INSERT INTO attendance
                            (trainer_id, branch_id, check_in_time, date, status, recorded_by, notes)
                        VALUES (?,?,?,?,?,?,?)
                    """, (entity_id, branch_id, now, today, status, recorded_by, notes))
                else:
                    cursor.execute("""
                        INSERT INTO attendance
                            (member_id, branch_id, check_in_time, date, status, recorded_by, notes)
                        VALUES (?,?,?,?,?,?,?)
                    """, (entity_id, branch_id, now, today, status, recorded_by, notes))
                cursor.execute("SELECT @@IDENTITY")
                att_id = int(cursor.fetchone()[0])

        _log_audit(recorded_by, ACTION_CREATE, att_id, f"Check-in {col}={entity_id}")
        return {"success": True, "message": f"Checked in at {now.strftime('%H:%M')}. Status: {status}"}
    except Exception as e:
        logger.error(f"check_in error: {e}", exc_info=True)
        return {"success": False, "message": f"Check-in failed: {e}"}


def check_out(entity_id: int, recorded_by: int, is_trainer: bool = False) -> dict:
    try:
        today = date.today()
        col = "trainer_id" if is_trainer else "member_id"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                f"SELECT id FROM attendance WHERE {col}=? AND date=? AND check_in_time IS NOT NULL AND check_out_time IS NULL",
                (entity_id, today)
            )
            row = cursor.fetchone()
        if not row:
            return {"success": False, "message": "No active check-in found for today."}
        now = datetime.now()
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE attendance SET check_out_time=? WHERE id=?", (now, row[0])
            )
        return {"success": True, "message": f"Checked out at {now.strftime('%H:%M')}."}
    except Exception as e:
        logger.error(f"check_out error: {e}", exc_info=True)
        return {"success": False, "message": f"Check-out failed: {e}"}


# ── Fetch Records ─────────────────────────────────────────────────────────────
def get_daily_log(branch_id: Optional[int], log_date: date, entity_id: Optional[int] = None, is_trainer: bool = False) -> list:
    try:
        sql = """
            SELECT a.id, COALESCE(m.full_name, t.full_name), COALESCE(m.cnic, t.cnic), 
                   a.check_in_time, a.check_out_time,
                   a.status, a.notes, a.date, b.branch_name, COALESCE(a.member_id, a.trainer_id)
            FROM   attendance a
            LEFT JOIN members  m ON a.member_id  = m.id
            LEFT JOIN trainers t ON a.trainer_id = t.id
            JOIN   branches b ON a.branch_id  = b.id
            WHERE  a.date = ?
        """
        params = [log_date]
        if branch_id:
            sql += " AND a.branch_id=?"
            params.append(branch_id)
        if entity_id:
            col = "a.trainer_id" if is_trainer else "a.member_id"
            sql += f" AND {col}=?"
            params.append(entity_id)
                
        sql += " ORDER BY a.check_in_time DESC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_daily_log error: {e}")
        return []


def get_attendance_by_range(branch_id: Optional[int],
                             start_date: date, end_date: date,
                             entity_id: Optional[int] = None, is_trainer: bool = False) -> list:
    try:
        sql = """
            SELECT a.date, COALESCE(m.full_name, t.full_name), a.check_in_time, a.check_out_time,
                   a.status, b.branch_name
            FROM   attendance a
            LEFT JOIN members  m ON a.member_id  = m.id
            LEFT JOIN trainers t ON a.trainer_id = t.id
            JOIN   branches b ON a.branch_id  = b.id
            WHERE  a.date BETWEEN ? AND ?
        """
        params = [start_date, end_date]
        if branch_id:
            sql += " AND a.branch_id=?"
            params.append(branch_id)
        if entity_id:
            col = "a.trainer_id" if is_trainer else "a.member_id"
            sql += f" AND {col}=?"
            params.append(entity_id)
        sql += " ORDER BY a.date DESC, a.check_in_time DESC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_attendance_by_range error: {e}")
        return []


def get_calendar_data(branch_id: Optional[int], year: int, month: int, entity_id: Optional[int] = None, is_trainer: bool = False) -> dict:
    """Returns {day: count} for calendar view."""
    try:
        sql = """
            SELECT DAY(a.date), COUNT(*)
            FROM   attendance a
            WHERE  YEAR(a.date)=? AND MONTH(a.date)=? AND a.status='Present'
        """
        params = [year, month]
        if branch_id:
            sql += " AND a.branch_id=?"
            params.append(branch_id)
        if entity_id:
            col = "a.trainer_id" if is_trainer else "a.member_id"
            sql += f" AND {col}=?"
            params.append(entity_id)
        sql += " GROUP BY DAY(a.date)"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return {row[0]: row[1] for row in cursor.fetchall()}
    except Exception as e:
        logger.error(f"get_calendar_data error: {e}")
        return {}


def get_attendance_stats(branch_id: Optional[int], for_date: date, entity_id: Optional[int] = None, is_trainer: bool = False) -> dict:
    try:
        sql = """
            SELECT
                SUM(CASE WHEN status IN ('Present', 'Late') THEN 1 ELSE 0 END),
                SUM(CASE WHEN status='Late'    THEN 1 ELSE 0 END),
                SUM(CASE WHEN status='Absent'  THEN 1 ELSE 0 END),
                COUNT(*)
            FROM attendance WHERE date=?
        """
        params = [for_date]
        if branch_id:
            sql += " AND branch_id=?"
            params.append(branch_id)
        if entity_id:
            col = "trainer_id" if is_trainer else "member_id"
            sql += f" AND {col}=?"
            params.append(entity_id)
                
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return {
                "present": row[0] or 0,
                "late":    row[1] or 0,
                "absent":  row[2] or 0,
                "total":   row[3] or 0,
            }
    except Exception as e:
        logger.error(f"get_attendance_stats error: {e}")
        return {"present": 0, "late": 0, "absent": 0, "total": 0}


def record_manual_attendance(entity_id: int, branch_id: int,
                               att_date: date, status: str,
                               check_in: Optional[str], check_out: Optional[str],
                               notes: str, recorded_by: int, is_trainer: bool = False) -> dict:
    """Manual attendance entry for past dates."""
    try:
        col = "trainer_id" if is_trainer else "member_id"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                f"SELECT id FROM attendance WHERE {col}=? AND date=?",
                (entity_id, att_date)
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute("""
                    UPDATE attendance
                    SET status=?, check_in_time=?, check_out_time=?, notes=?, recorded_by=?
                    WHERE id=?
                """, (status, check_in, check_out, notes, recorded_by, existing[0]))
                aid = existing[0]
            else:
                if is_trainer:
                    cursor.execute("""
                        INSERT INTO attendance
                            (trainer_id, branch_id, date, status, check_in_time, check_out_time, notes, recorded_by)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, (entity_id, branch_id, att_date, status, check_in, check_out, notes, recorded_by))
                else:
                    cursor.execute("""
                        INSERT INTO attendance
                            (member_id, branch_id, date, status, check_in_time, check_out_time, notes, recorded_by)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, (entity_id, branch_id, att_date, status, check_in, check_out, notes, recorded_by))
                cursor.execute("SELECT @@IDENTITY")
                aid = int(cursor.fetchone()[0])
        _log_audit(recorded_by, "MANUAL_ATTENDANCE", aid, f"{col}={entity_id} date={att_date}")
        return {"success": True, "message": "Attendance recorded."}
    except Exception as e:
        logger.error(f"record_manual_attendance error: {e}")
        return {"success": False, "message": str(e)}


def get_members_for_checkin(branch_id: Optional[int]) -> list:
    """Active members for check-in dropdown."""
    try:
        sql = """
            SELECT m.id, m.full_name, m.cnic,
                   CASE WHEN a.id IS NOT NULL AND a.check_out_time IS NULL THEN 1 ELSE 0 END AS is_checked_in
            FROM   members m
            LEFT JOIN attendance a ON a.member_id=m.id AND a.date=CAST(GETDATE() AS DATE)
            WHERE  m.status='Active'
        """
        params = []
        if branch_id:
            sql += " AND m.branch_id=?"
            params.append(branch_id)
        sql += " ORDER BY m.full_name"
        
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_members_for_checkin error: {e}")
        return []

def get_trainers_for_checkin(branch_id: Optional[int]) -> list:
    """Active trainers for check-in dropdown."""
    try:
        sql = """
            SELECT t.id, t.full_name, t.cnic,
                   CASE WHEN a.id IS NOT NULL AND a.check_out_time IS NULL THEN 1 ELSE 0 END AS is_checked_in
            FROM   trainers t
            LEFT JOIN attendance a ON a.trainer_id=t.id AND a.date=CAST(GETDATE() AS DATE)
            WHERE  t.status='Active'
        """
        params = []
        if branch_id:
            sql += " AND t.branch_id=?"
            params.append(branch_id)
        sql += " ORDER BY t.full_name"
        
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_trainers_for_checkin error: {e}")
        return []
