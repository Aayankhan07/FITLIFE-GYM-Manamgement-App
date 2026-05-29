"""
FitLife — Billing Service
Payment recording, invoice number generation, fee status, branch financials.
"""
import logging
import uuid
from datetime import date, datetime
from typing import Optional
from database.connection import DatabaseConnection
from config.constants import (
    PAYMENT_PAID, PAYMENT_UNPAID, PAYMENT_OVERDUE, ACTION_PAYMENT
)

logger = logging.getLogger(__name__)


def _log_audit(user_id, action, record_id, detail=""):
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "INSERT INTO audit_logs(user_id,action,module,record_id,new_value,timestamp)"
                " VALUES(?,?,?,?,?,GETDATE())",
                (user_id, action, "Billing", record_id, detail)
            )
    except Exception as e:
        logger.error(f"Audit error: {e}")


def generate_invoice_number() -> str:
    """Generate a unique invoice number: INV-YYYY-XXXXXXXX"""
    year = datetime.now().year
    unique = uuid.uuid4().hex[:8].upper()
    return f"INV-{year}-{unique}"


# ── Payment Recording ──────────────────────────────────────────────────────────
def record_payment(member_id: int, amount: float, payment_method: str,
                   payment_date: date, membership_id: Optional[int],
                   recorded_by: int, notes: str = "") -> dict:
    """Record a payment and mark it as PAID."""
    try:
        inv_num = generate_invoice_number()
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO payments
                    (member_id, membership_id, amount, payment_date, payment_method,
                     status, invoice_number, recorded_by, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,GETDATE())
            """, (
                member_id, membership_id, amount, payment_date,
                payment_method, PAYMENT_PAID, inv_num, recorded_by, notes
            ))
            cursor.execute("SELECT @@IDENTITY")
            pay_id = int(cursor.fetchone()[0])

        # Create invoice record
        _create_invoice_record(pay_id, member_id, inv_num, amount, payment_date)
        _log_audit(recorded_by, ACTION_PAYMENT, pay_id,
                   f"Rs.{amount} from member_id={member_id} via {payment_method}")
        logger.info(f"Payment recorded: {inv_num} Rs.{amount}")
        return {
            "success": True,
            "payment_id": pay_id,
            "invoice_number": inv_num,
            "message": f"Payment of Rs.{amount:,.0f} recorded. Invoice: {inv_num}"
        }
    except Exception as e:
        logger.error(f"record_payment error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to record payment: {e}"}


def _create_invoice_record(payment_id: int, member_id: int, inv_num: str,
                            amount: float, due_date: date):
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO invoices
                    (payment_id, member_id, invoice_number, amount_due, due_date, created_at)
                VALUES (?,?,?,?,?,GETDATE())
            """, (payment_id, member_id, inv_num, amount, due_date))
    except Exception as e:
        logger.error(f"_create_invoice_record error: {e}")


def update_payment_status(payment_id: int, new_status: str, updated_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE payments SET status=? WHERE id=?", (new_status, payment_id)
            )
        _log_audit(updated_by, "PAYMENT_STATUS_UPDATE", payment_id, new_status)
        return {"success": True, "message": f"Status updated to {new_status}."}
    except Exception as e:
        logger.error(f"update_payment_status error: {e}")
        return {"success": False, "message": str(e)}


# ── Fetch Records ─────────────────────────────────────────────────────────────
def get_payments_by_branch(branch_id: Optional[int],
                            status: Optional[str] = None,
                            month: Optional[int] = None,
                            year: Optional[int] = None) -> list:
    try:
        sql = """
            SELECT p.id, m.full_name, m.cnic, b.branch_name,
                   p.amount, p.payment_date, p.payment_method,
                   p.status, p.invoice_number, p.notes, p.created_at,
                   p.member_id, p.membership_id
            FROM   payments p
            JOIN   members  m ON p.member_id = m.id
            JOIN   branches b ON m.branch_id = b.id
            WHERE  1=1
        """
        params = []
        if branch_id:
            sql += " AND m.branch_id=?"
            params.append(branch_id)
        if status:
            sql += " AND p.status=?"
            params.append(status)
        if month:
            sql += " AND MONTH(p.payment_date)=?"
            params.append(month)
        if year:
            sql += " AND YEAR(p.payment_date)=?"
            params.append(year)
        sql += " ORDER BY p.created_at DESC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_payments_by_branch error: {e}")
        return []


def get_payment_by_id(payment_id: int) -> Optional[object]:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT p.id, m.full_name, m.cnic, m.email, m.phone,
                       b.branch_name, b.address, mp.plan_name,
                       p.amount, p.payment_date, p.payment_method,
                       p.status, p.invoice_number, p.notes,
                       p.member_id, p.membership_id
                FROM   payments p
                JOIN   members       m  ON p.member_id = m.id
                JOIN   branches      b  ON m.branch_id = b.id
                LEFT JOIN membership_plans mp ON m.membership_plan_id = mp.id
                WHERE  p.id=?
            """, (payment_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"get_payment_by_id error: {e}")
        return None


def get_unpaid_members(branch_id: Optional[int]) -> list:
    """Members with no Paid payment this month."""
    try:
        sql = """
            SELECT m.id, m.full_name, m.phone, m.email, m.expiry_date,
                   mp.plan_name, mp.price, b.branch_name
            FROM   members m
            JOIN   branches b ON m.branch_id = b.id
            LEFT JOIN membership_plans mp ON m.membership_plan_id = mp.id
            WHERE  m.status='Active'
            AND    m.id NOT IN (
                SELECT DISTINCT member_id FROM payments
                WHERE  status='Paid'
                AND    MONTH(payment_date)=MONTH(GETDATE())
                AND    YEAR(payment_date)=YEAR(GETDATE())
            )
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
        logger.error(f"get_unpaid_members error: {e}")
        return []


def mark_overdue_payments() -> int:
    """Auto-flag Unpaid payments past due date as Overdue."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                UPDATE payments SET status='Overdue'
                WHERE  status='Unpaid'
                AND    payment_date < CAST(GETDATE() AS DATE)
            """)
            return cursor.rowcount
    except Exception as e:
        logger.error(f"mark_overdue_payments error: {e}")
        return 0


# ── Branch Financials ──────────────────────────────────────────────────────────
def get_branch_financials(branch_id: Optional[int],
                           month: int, year: int) -> dict:
    """Revenue, salary expenses, net profit for a branch in a given month."""
    try:
        with DatabaseConnection() as (conn, cursor):
            # Revenue collected
            sql_rev = """
                SELECT ISNULL(SUM(p.amount), 0)
                FROM   payments p
                JOIN   members m ON p.member_id = m.id
                WHERE  p.status='Paid'
                AND    MONTH(p.payment_date)=? AND YEAR(p.payment_date)=?
            """
            rev_params = [month, year]
            if branch_id:
                sql_rev += " AND m.branch_id=?"
                rev_params.append(branch_id)
            cursor.execute(sql_rev, rev_params)
            revenue = float(cursor.fetchone()[0])

            # Salary expenses
            sql_sal = """
                SELECT ISNULL(SUM(sr.amount), 0)
                FROM   salary_records sr
                JOIN   trainers t ON sr.trainer_id = t.id
                WHERE  sr.status='Paid' AND sr.month=? AND sr.year=?
            """
            sal_params = [month, year]
            if branch_id:
                sql_sal += " AND t.branch_id=?"
                sal_params.append(branch_id)
            cursor.execute(sql_sal, sal_params)
            salaries = float(cursor.fetchone()[0])

            # Equipment purchases
            sql_equip = """
                SELECT ISNULL(SUM(purchase_price * quantity), 0)
                FROM equipment
                WHERE purchase_date IS NOT NULL AND MONTH(purchase_date)=? AND YEAR(purchase_date)=?
            """
            equip_params = [month, year]
            if branch_id:
                sql_equip += " AND branch_id=?"
                equip_params.append(branch_id)
            cursor.execute(sql_equip, equip_params)
            equipment_costs = float(cursor.fetchone()[0])

            # Extra expenses
            sql_exp = """
                SELECT ISNULL(SUM(amount), 0)
                FROM expenses
                WHERE MONTH(expense_date)=? AND YEAR(expense_date)=?
            """
            exp_params = [month, year]
            if branch_id:
                sql_exp += " AND branch_id=?"
                exp_params.append(branch_id)
            cursor.execute(sql_exp, exp_params)
            extra_expenses = float(cursor.fetchone()[0])

            # Pending revenue (Unpaid/Overdue)
            sql_pend = """
                SELECT ISNULL(SUM(p.amount), 0)
                FROM   payments p
                JOIN   members m ON p.member_id = m.id
                WHERE  p.status IN ('Unpaid','Overdue')
                AND    MONTH(p.payment_date)=? AND YEAR(p.payment_date)=?
            """
            pend_params = [month, year]
            if branch_id:
                sql_pend += " AND m.branch_id=?"
                pend_params.append(branch_id)
            cursor.execute(sql_pend, pend_params)
            pending = float(cursor.fetchone()[0])

        net_profit = revenue - salaries - equipment_costs - extra_expenses
        return {
            "revenue":    revenue,
            "salaries":   salaries,
            "equipment":  equipment_costs,
            "expenses":   extra_expenses,
            "pending":    pending,
            "net_profit": net_profit,
            "month": month, "year": year,
        }
    except Exception as e:
        logger.error(f"get_branch_financials error: {e}")
        return {"revenue": 0, "salaries": 0, "pending": 0, "net_profit": 0}


def get_monthly_revenue_trend(branch_id: Optional[int], months: int = 6) -> list:
    """Revenue per month for last N months — for charts."""
    try:
        sql = """
            SELECT YEAR(p.payment_date)  AS yr,
                   MONTH(p.payment_date) AS mo,
                   SUM(p.amount)         AS total
            FROM   payments p
            JOIN   members m ON p.member_id = m.id
            WHERE  p.status='Paid'
            AND    p.payment_date >= DATEADD(month, ?, CAST(GETDATE() AS DATE))
        """
        params = [-months]
        if branch_id:
            sql += " AND m.branch_id=?"
            params.append(branch_id)
        sql += " GROUP BY YEAR(p.payment_date), MONTH(p.payment_date) ORDER BY yr,mo"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_monthly_revenue_trend error: {e}")
        return []


# ── Fee Status Summary ─────────────────────────────────────────────────────────
def get_fee_status_summary(branch_id: Optional[int]) -> dict:
    try:
        sql = """
            SELECT
                SUM(CASE WHEN p.status='Paid'    THEN 1 ELSE 0 END),
                SUM(CASE WHEN p.status='Unpaid'  THEN 1 ELSE 0 END),
                SUM(CASE WHEN p.status='Partial' THEN 1 ELSE 0 END),
                SUM(CASE WHEN p.status='Overdue' THEN 1 ELSE 0 END),
                SUM(CASE WHEN p.status='Paid'    THEN p.amount ELSE 0 END),
                SUM(CASE WHEN p.status<>'Paid'   THEN p.amount ELSE 0 END)
            FROM payments p
            JOIN members m ON p.member_id=m.id
            WHERE MONTH(p.payment_date)=MONTH(GETDATE())
            AND   YEAR(p.payment_date)=YEAR(GETDATE())
        """
        params = []
        if branch_id:
            sql += " AND m.branch_id=?"
            params.append(branch_id)
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return {
                "paid_count":     row[0] or 0,
                "unpaid_count":   row[1] or 0,
                "partial_count":  row[2] or 0,
                "overdue_count":  row[3] or 0,
                "collected":      float(row[4] or 0),
                "outstanding":    float(row[5] or 0),
            }
    except Exception as e:
        logger.error(f"get_fee_status_summary error: {e}")
        return {"paid_count":0,"unpaid_count":0,"partial_count":0,"overdue_count":0,"collected":0,"outstanding":0}
