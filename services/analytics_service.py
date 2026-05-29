"""FitLife — Analytics Service (Phase 6)"""
import logging
from typing import Optional
from datetime import date, timedelta
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


def get_dashboard_kpis(branch_id: Optional[int] = None) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            b = "AND m.branch_id=?" if branch_id else ""
            p = [branch_id] if branch_id else []

            # Members
            cursor.execute(f"SELECT COUNT(*), SUM(CASE WHEN status='Active' THEN 1 ELSE 0 END) FROM members m WHERE 1=1 {b}", p)
            r = cursor.fetchone(); total_mem, active_mem = r[0] or 0, r[1] or 0

            # Revenue this month
            cursor.execute(f"""
                SELECT ISNULL(SUM(py.amount),0)
                FROM payments py
                JOIN members m ON py.member_id=m.id
                WHERE py.status='Paid'
                AND MONTH(py.payment_date)=MONTH(GETDATE())
                AND YEAR(py.payment_date)=YEAR(GETDATE()) {b.replace('m.branch_id','m.branch_id')}
            """, p)
            monthly_rev = float(cursor.fetchone()[0] or 0)

            # Calculate Monthly Profit Deductions
            # Salaries
            sal_sql = """
                SELECT ISNULL(SUM(sr.amount + ISNULL(sr.bonus,0) - ISNULL(sr.deduction,0)),0)
                FROM salary_records sr
                JOIN trainers t ON sr.trainer_id=t.id
                WHERE sr.status='Paid'
                AND MONTH(sr.payment_date)=MONTH(GETDATE())
                AND YEAR(sr.payment_date)=YEAR(GETDATE())
            """
            if branch_id:
                sal_sql += " AND t.branch_id=?"
            cursor.execute(sal_sql, p)
            monthly_sal = float(cursor.fetchone()[0] or 0)

            # Equipment
            equip_sql = """
                SELECT ISNULL(SUM(purchase_price * quantity), 0)
                FROM equipment
                WHERE purchase_date IS NOT NULL
                AND MONTH(purchase_date)=MONTH(GETDATE())
                AND YEAR(purchase_date)=YEAR(GETDATE())
            """
            if branch_id:
                equip_sql += " AND branch_id=?"
            cursor.execute(equip_sql, p)
            monthly_equip = float(cursor.fetchone()[0] or 0)

            # Expenses
            exp_sql = """
                SELECT ISNULL(SUM(amount), 0)
                FROM expenses
                WHERE MONTH(expense_date)=MONTH(GETDATE())
                AND YEAR(expense_date)=YEAR(GETDATE())
            """
            if branch_id:
                exp_sql += " AND branch_id=?"
            cursor.execute(exp_sql, p)
            monthly_exp = float(cursor.fetchone()[0] or 0)

            monthly_profit = monthly_rev - monthly_sal - monthly_equip - monthly_exp

            # Attendance today
            cursor.execute(f"""
                SELECT COUNT(*) FROM attendance a
                JOIN members m ON a.member_id=m.id
                WHERE a.date=CAST(GETDATE() AS DATE) {b}
            """, p)
            today_att = cursor.fetchone()[0] or 0

            # Active trainers
            cursor.execute(f"SELECT COUNT(*) FROM trainers t WHERE t.status='Active' {'AND t.branch_id=?' if branch_id else ''}", p)
            trainers = cursor.fetchone()[0] or 0

            # Expiring soon (7 days)
            cursor.execute(f"""
                SELECT COUNT(*) FROM members m WHERE status='Active'
                AND expiry_date BETWEEN CAST(GETDATE() AS DATE) AND DATEADD(day,7,CAST(GETDATE() AS DATE)) {b}
            """, p)
            expiring = cursor.fetchone()[0] or 0

            # Pending payments
            cursor.execute(f"""
                SELECT COUNT(*), ISNULL(SUM(py.amount),0)
                FROM payments py JOIN members m ON py.member_id=m.id
                WHERE py.status IN ('Unpaid','Overdue') {b}
            """, p)
            r2 = cursor.fetchone(); pending_cnt, pending_amt = r2[0] or 0, float(r2[1] or 0)

            # Total revenue
            cursor.execute(f"SELECT ISNULL(SUM(py.amount),0) FROM payments py JOIN members m ON py.member_id=m.id WHERE py.status='Paid' {b}", p)
            total_rev = float(cursor.fetchone()[0] or 0)

            # Calculate Total Profit Deductions
            t_sal_sql = "SELECT ISNULL(SUM(sr.amount + ISNULL(sr.bonus,0) - ISNULL(sr.deduction,0)),0) FROM salary_records sr JOIN trainers t ON sr.trainer_id=t.id WHERE sr.status='Paid'"
            if branch_id:
                t_sal_sql += " AND t.branch_id=?"
            cursor.execute(t_sal_sql, p)
            total_sal = float(cursor.fetchone()[0] or 0)

            t_equip_sql = "SELECT ISNULL(SUM(purchase_price * quantity), 0) FROM equipment WHERE purchase_date IS NOT NULL"
            if branch_id:
                t_equip_sql += " AND branch_id=?"
            cursor.execute(t_equip_sql, p)
            total_equip = float(cursor.fetchone()[0] or 0)

            t_exp_sql = "SELECT ISNULL(SUM(amount), 0) FROM expenses WHERE 1=1"
            if branch_id:
                t_exp_sql += " AND branch_id=?"
            cursor.execute(t_exp_sql, p)
            total_exp = float(cursor.fetchone()[0] or 0)

            total_profit = total_rev - total_sal - total_equip - total_exp

            return {
                "total_members": total_mem, "active_members": active_mem,
                "monthly_revenue": monthly_rev, "total_revenue": total_rev,
                "monthly_profit": monthly_profit, "total_profit": total_profit,
                "today_attendance": today_att,
                "active_trainers": trainers, "expiring_soon": expiring,
                "pending_payments": pending_cnt, "pending_amount": pending_amt,
            }
    except Exception as e:
        logger.error(f"get_dashboard_kpis error: {e}")
        return {"total_members":0,"active_members":0,"monthly_revenue":0,"today_attendance":0,
                "active_trainers":0,"expiring_soon":0,"pending_payments":0,"pending_amount":0}


def _get_last_n_months(n: int) -> list:
    today = date.today()
    y, m = today.year, today.month
    res = []
    for _ in range(n):
        res.insert(0, (y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return res

def get_monthly_revenue(branch_id: Optional[int] = None, months: int = 6) -> list:
    """Returns [(month_label, revenue)] for the last N months."""
    try:
        rows = []
        months_list = _get_last_n_months(months)
        with DatabaseConnection() as (conn, cursor):
            for y, m in months_list:
                sql = """
                    SELECT ISNULL(SUM(py.amount),0)
                    FROM payments py JOIN members mem ON py.member_id=mem.id
                    WHERE py.status='Paid' AND MONTH(py.payment_date)=? AND YEAR(py.payment_date)=?
                """
                params = [m, y]
                if branch_id:
                    sql += " AND mem.branch_id=?"; params.append(branch_id)
                cursor.execute(sql, params)
                rev = float(cursor.fetchone()[0] or 0)
                d = date(y, m, 1)
                label = d.strftime("%b %Y")
                rows.append((label, rev))
        return rows
    except Exception as e:
        logger.error(f"get_monthly_revenue error: {e}")
        return []


def get_member_growth(branch_id: Optional[int] = None, months: int = 6) -> list:
    """Returns [(month_label, new_members)] for last N months."""
    try:
        rows = []
        months_list = _get_last_n_months(months)
        with DatabaseConnection() as (conn, cursor):
            for y, m in months_list:
                sql = "SELECT COUNT(*) FROM members WHERE MONTH(join_date)=? AND YEAR(join_date)=?"
                params = [m, y]
                if branch_id:
                    sql += " AND branch_id=?"; params.append(branch_id)
                cursor.execute(sql, params)
                cnt = cursor.fetchone()[0] or 0
                d = date(y, m, 1)
                rows.append((d.strftime("%b %Y"), cnt))
        return rows
    except Exception as e:
        logger.error(f"get_member_growth error: {e}")
        return []


def get_attendance_by_day(branch_id: Optional[int] = None, days: int = 7) -> list:
    """Returns [(date_str, count)] for last N days."""
    try:
        rows = []
        today = date.today()
        with DatabaseConnection() as (conn, cursor):
            for i in range(days - 1, -1, -1):
                d = today - timedelta(days=i)
                sql = """
                    SELECT COUNT(*) FROM attendance a
                    JOIN members m ON a.member_id=m.id
                    WHERE a.date=?
                """
                params = [d]
                if branch_id:
                    sql += " AND m.branch_id=?"; params.append(branch_id)
                cursor.execute(sql, params)
                cnt = cursor.fetchone()[0] or 0
                rows.append((d.strftime("%d %b"), cnt))
        return rows
    except Exception as e:
        logger.error(f"get_attendance_by_day error: {e}")
        return []


def get_goal_distribution(branch_id: Optional[int] = None) -> list:
    """Returns [(goal, count)] for member fitness goals."""
    try:
        sql = """
            SELECT fitness_goal, COUNT(*) AS cnt
            FROM members WHERE status='Active'
        """
        params = []
        if branch_id:
            sql += " AND branch_id=?"; params.append(branch_id)
        sql += " GROUP BY fitness_goal ORDER BY cnt DESC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_goal_distribution error: {e}")
        return []


def get_top_trainers(branch_id: Optional[int] = None, limit: int = 5) -> list:
    try:
        sql = """
            SELECT TOP (?) t.full_name, t.specialization,
                   COUNT(m.id) AS members,
                   ISNULL(t.performance_rating, 0) AS rating
            FROM trainers t
            LEFT JOIN members m ON m.trainer_id=t.id AND m.status='Active'
            WHERE t.status='Active'
        """
        params = [limit]
        if branch_id:
            sql += " AND t.branch_id=?"; params.append(branch_id)
        sql += " GROUP BY t.id, t.full_name, t.specialization, t.performance_rating ORDER BY members DESC, rating DESC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_top_trainers error: {e}")
        return []
