"""FitLife — Reports Service + CSV Export (Phase 6)"""
import csv, io, logging
from typing import Optional
from datetime import date
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


def get_member_report(branch_id: Optional[int] = None,
                      status: Optional[str] = None) -> list:
    try:
        sql = """
            SELECT m.full_name, m.cnic, m.phone, m.email,
                   b.branch_name, t.full_name AS trainer,
                   mp.plan_name, m.join_date, m.expiry_date,
                   m.status, m.fitness_goal, m.weight_kg, m.bmi
            FROM   members m
            LEFT JOIN branches b ON m.branch_id=b.id
            LEFT JOIN trainers t ON m.trainer_id=t.id
            LEFT JOIN membership_plans mp ON m.membership_plan_id=mp.id
            WHERE  1=1
        """
        params = []
        if branch_id: sql += " AND m.branch_id=?"; params.append(branch_id)
        if status:    sql += " AND m.status=?";    params.append(status)
        sql += " ORDER BY m.full_name"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_member_report: {e}"); return []


def get_payment_report(branch_id: Optional[int] = None,
                       date_from: Optional[date] = None,
                       date_to:   Optional[date] = None) -> list:
    try:
        sql = """
            SELECT m.full_name, m.phone, b.branch_name,
                   py.invoice_number, py.amount, py.payment_date,
                   py.payment_method, py.status, py.notes
            FROM   payments py
            JOIN   members m ON py.member_id=m.id
            JOIN   branches b ON m.branch_id=b.id
            WHERE  1=1
        """
        params = []
        if branch_id: sql += " AND m.branch_id=?"; params.append(branch_id)
        if date_from: sql += " AND py.payment_date>=?"; params.append(date_from)
        if date_to:   sql += " AND py.payment_date<=?"; params.append(date_to)
        sql += " ORDER BY py.payment_date DESC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_payment_report: {e}"); return []


def get_attendance_report(branch_id: Optional[int] = None,
                          date_from: Optional[date] = None,
                          date_to:   Optional[date] = None) -> list:
    try:
        sql = """
            SELECT m.full_name, b.branch_name,
                   a.date, a.check_in_time, a.check_out_time, a.status
            FROM   attendance a
            JOIN   members m ON a.member_id=m.id
            JOIN   branches b ON m.branch_id=b.id
            WHERE  1=1
        """
        params = []
        if branch_id: sql += " AND m.branch_id=?"; params.append(branch_id)
        if date_from: sql += " AND a.date>=?"; params.append(date_from)
        if date_to:   sql += " AND a.date<=?"; params.append(date_to)
        sql += " ORDER BY a.date DESC, m.full_name"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_attendance_report: {e}"); return []


def get_trainer_performance_report(branch_id: Optional[int] = None) -> list:
    try:
        sql = """
            SELECT t.full_name, b.branch_name, t.specialization,
                   COUNT(m.id) AS members,
                   ISNULL(t.performance_rating, 0) AS rating,
                   t.monthly_salary, t.hire_date, t.status
            FROM   trainers t
            JOIN   branches b ON t.branch_id=b.id
            LEFT JOIN members m ON m.trainer_id=t.id AND m.status='Active'
            WHERE  1=1
        """
        params = []
        if branch_id: sql += " AND t.branch_id=?"; params.append(branch_id)
        sql += " GROUP BY t.id, t.full_name, b.branch_name, t.specialization, t.performance_rating, t.monthly_salary, t.hire_date, t.status ORDER BY members DESC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_trainer_performance_report: {e}"); return []


def get_equipment_report(branch_id: Optional[int] = None) -> list:
    try:
        sql = """
            SELECT e.equipment_name, e.category, e.brand, e.model,
                   e.serial_number, e.condition_status, e.quantity,
                   e.purchase_price, e.purchase_date,
                   e.last_maintenance_date, b.branch_name
            FROM   equipment e
            JOIN   branches b ON e.branch_id=b.id
            WHERE  1=1
        """
        params = []
        if branch_id: sql += " AND e.branch_id=?"; params.append(branch_id)
        sql += " ORDER BY e.category, e.equipment_name"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_equipment_report: {e}"); return []


def export_to_csv(headers: list, rows: list, file_path: str) -> dict:
    try:
        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows([[str(v) if v is not None else "" for v in row] for row in rows])
        return {"success": True, "message": f"Exported {len(rows)} rows to {file_path}"}
    except Exception as e:
        logger.error(f"export_to_csv: {e}")
        return {"success": False, "message": str(e)}
