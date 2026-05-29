"""
FitLife — Expense Service
Track custom branch expenses like Rent, Electricity, etc.
"""
import logging
from typing import Optional
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)

def get_expenses_by_branch(branch_id: Optional[int] = None, month: Optional[int] = None, year: Optional[int] = None) -> list:
    try:
        sql = """
            SELECT e.id, b.branch_name, e.category, e.amount, e.expense_date, e.description, u.full_name
            FROM expenses e
            JOIN branches b ON e.branch_id = b.id
            LEFT JOIN users u ON e.recorded_by = u.id
            WHERE 1=1
        """
        params = []
        if branch_id:
            sql += " AND e.branch_id=?"
            params.append(branch_id)
        if month:
            sql += " AND MONTH(e.expense_date)=?"
            params.append(month)
        if year:
            sql += " AND YEAR(e.expense_date)=?"
            params.append(year)
        sql += " ORDER BY e.expense_date DESC, e.id DESC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_expenses_by_branch error: {e}")
        return []

def add_expense(branch_id: int, category: str, amount: float, expense_date: str, description: str, recorded_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO expenses (branch_id, category, amount, expense_date, description, recorded_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, GETDATE())
            """, (branch_id, category, amount, expense_date, description, recorded_by))
        return {"success": True, "message": "Expense recorded successfully."}
    except Exception as e:
        logger.error(f"add_expense error: {e}")
        return {"success": False, "message": str(e)}

def delete_expense(expense_id: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        return {"success": True, "message": "Expense deleted."}
    except Exception as e:
        logger.error(f"delete_expense error: {e}")
        return {"success": False, "message": str(e)}
