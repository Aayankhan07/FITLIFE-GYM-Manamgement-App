"""
FitLife — Salary Service
Salary records, payment, slip generation, reports.
Actual DB schema for salary_records:
  id, trainer_id, month, year, amount, payment_date, payment_method,
  status, paid_by, slip_sent, created_at, bonus, deduction, notes, updated_at
NOTE: No base_salary or net_salary columns — use amount + bonus - deduction.
"""
import logging
from datetime import date
from typing import Optional
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)

MONTHS = ["", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def _log_audit(user_id, action, record_id, detail=""):
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "INSERT INTO audit_logs(user_id,action,module,record_id,new_value,timestamp)"
                " VALUES(?,?,?,?,?,GETDATE())",
                (user_id, action, "Salary", record_id, detail)
            )
    except Exception as e:
        logger.error(f"Audit error: {e}")


def get_salary_records(branch_id: Optional[int] = None,
                        month: Optional[int] = None,
                        year: Optional[int] = None) -> list:
    """
    Returns list of salary records.
    Columns: id, trainer_name, branch_name, month, year,
             base_amount (=amount), bonus, deduction, net (computed),
             status, payment_date, notes, trainer_id
    """
    try:
        sql = """
            SELECT sr.id,
                   t.full_name,
                   ISNULL(b.branch_name, 'N/A'),
                   sr.month,
                   sr.year,
                   ISNULL(sr.amount, 0)           AS base_amount,
                   ISNULL(sr.bonus, 0)            AS bonus,
                   ISNULL(sr.deduction, 0)        AS deduction,
                   (ISNULL(sr.amount,0) + ISNULL(sr.bonus,0) - ISNULL(sr.deduction,0)) AS net_salary,
                   sr.status,
                   sr.payment_date,
                   ISNULL(sr.notes, '')           AS notes,
                   sr.trainer_id
            FROM   salary_records sr
            JOIN   trainers t ON sr.trainer_id = t.id
            LEFT JOIN branches b ON t.branch_id = b.id
            WHERE  1=1
        """
        params = []
        if branch_id:
            sql += " AND t.branch_id=?"
            params.append(branch_id)
        if month:
            sql += " AND sr.month=?"
            params.append(month)
        if year:
            sql += " AND sr.year=?"
            params.append(year)
        sql += " ORDER BY sr.year DESC, sr.month DESC, t.full_name"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_salary_records error: {e}")
        return []


def get_salary_stats(branch_id: Optional[int], month: int, year: int) -> dict:
    try:
        sql = """
            SELECT
                COUNT(*)                 AS total,
                SUM(CASE WHEN sr.status='Paid'    THEN 1 ELSE 0 END) AS paid,
                SUM(CASE WHEN sr.status='Pending' THEN 1 ELSE 0 END) AS pending,
                ISNULL(SUM(ISNULL(sr.amount,0) + ISNULL(sr.bonus,0) - ISNULL(sr.deduction,0)), 0) AS total_payout,
                ISNULL(SUM(CASE WHEN sr.status='Paid'
                           THEN ISNULL(sr.amount,0) + ISNULL(sr.bonus,0) - ISNULL(sr.deduction,0)
                           ELSE 0 END), 0) AS paid_amount
            FROM salary_records sr
            JOIN trainers t ON sr.trainer_id = t.id
            WHERE sr.month=? AND sr.year=?
        """
        params = [month, year]
        if branch_id:
            sql += " AND t.branch_id=?"
            params.append(branch_id)
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            row = cursor.fetchone()
            if row:
                return {
                    "total": row[0] or 0, "paid": row[1] or 0, "pending": row[2] or 0,
                    "total_payout": float(row[3] or 0), "paid_amount": float(row[4] or 0)
                }
        return {"total": 0, "paid": 0, "pending": 0, "total_payout": 0, "paid_amount": 0}
    except Exception as e:
        logger.error(f"get_salary_stats error: {e}")
        return {"total": 0, "paid": 0, "pending": 0, "total_payout": 0, "paid_amount": 0}


def generate_monthly_salaries(month: int, year: int,
                               branch_id: Optional[int],
                               generated_by: int) -> dict:
    """Auto-generate salary records for all active trainers for a month."""
    try:
        sql = "SELECT id, monthly_salary FROM trainers WHERE status='Active'"
        params = []
        if branch_id:
            sql += " AND branch_id=?"
            params.append(branch_id)
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            trainers = cursor.fetchall()

        created = 0
        skipped = 0
        with DatabaseConnection() as (conn, cursor):
            for t_id, base_sal in trainers:
                cursor.execute(
                    "SELECT id FROM salary_records WHERE trainer_id=? AND month=? AND year=?",
                    (t_id, month, year)
                )
                if cursor.fetchone():
                    skipped += 1
                    continue
                base = float(base_sal or 0)
                cursor.execute("""
                    INSERT INTO salary_records
                        (trainer_id, month, year, amount, bonus, deduction,
                         status, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,GETDATE(),GETDATE())
                """, (t_id, month, year, base, 0, 0, "Pending"))
                created += 1

        _log_audit(generated_by, "SALARY_GENERATED", 0,
                   f"{created} records for {MONTHS[month]} {year}")
        return {
            "success": True, "created": created, "skipped": skipped,
            "message": f"Generated {created} salary record(s). {skipped} already existed."
        }
    except Exception as e:
        logger.error(f"generate_monthly_salaries error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


def update_salary_record(record_id: int, bonus: float, deduction: float,
                          notes: str, updated_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "SELECT ISNULL(amount, 0) FROM salary_records WHERE id=?", (record_id,)
            )
            row = cursor.fetchone()
            if not row:
                return {"success": False, "message": "Record not found."}
            net = float(row[0]) + bonus - deduction
            cursor.execute("""
                UPDATE salary_records
                SET bonus=?, deduction=?, notes=?, updated_at=GETDATE()
                WHERE id=?
            """, (bonus, deduction, notes, record_id))
        _log_audit(updated_by, "SALARY_UPDATED", record_id, f"Net={net}")
        return {"success": True, "message": f"Salary updated. Net: Rs.{net:,.0f}"}
    except Exception as e:
        logger.error(f"update_salary_record error: {e}")
        return {"success": False, "message": str(e)}


def mark_salary_paid(record_id: int, paid_by: int) -> dict:
    try:
        today = date.today()
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE salary_records SET status='Paid', payment_date=?, "
                "paid_by=?, updated_at=GETDATE() WHERE id=?",
                (today, paid_by, record_id)
            )
        _log_audit(paid_by, "SALARY_PAID", record_id, f"Date={today}")
        return {"success": True, "message": "Salary marked as Paid."}
    except Exception as e:
        logger.error(f"mark_salary_paid error: {e}")
        return {"success": False, "message": str(e)}


def get_salary_slip_data(record_id: int) -> Optional[dict]:
    """All data needed to render salary slip."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT sr.id, sr.month, sr.year,
                       ISNULL(sr.amount, 0),
                       ISNULL(sr.bonus, 0),
                       ISNULL(sr.deduction, 0),
                       (ISNULL(sr.amount,0) + ISNULL(sr.bonus,0) - ISNULL(sr.deduction,0)),
                       sr.status,
                       sr.payment_date,
                       ISNULL(sr.notes, ''),
                       t.full_name,
                       ISNULL(t.cnic, ''),
                       ISNULL(t.specialization, 'Trainer'),
                       ISNULL(b.branch_name, 'N/A'),
                       ISNULL(b.address, ''),
                       ISNULL(b.phone, '')
                FROM   salary_records sr
                JOIN   trainers t ON sr.trainer_id = t.id
                LEFT JOIN branches b ON t.branch_id = b.id
                WHERE  sr.id=?
            """, (record_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": row[0], "month": MONTHS[row[1]], "year": row[2],
                "base_salary": float(row[3]),
                "bonus": float(row[4]),
                "deduction": float(row[5]),
                "net_salary": float(row[6]),
                "status": row[7], "payment_date": row[8], "notes": row[9],
                "trainer_name": row[10], "trainer_cnic": row[11],
                "designation": "Trainer",
                "specialization": row[12],
                "branch_name": row[13], "branch_address": row[14], "branch_phone": row[15],
            }
    except Exception as e:
        logger.error(f"get_salary_slip_data error: {e}")
        return None
