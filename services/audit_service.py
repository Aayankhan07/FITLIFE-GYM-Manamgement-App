"""FitLife — Audit Service (read-only log viewer for admins)."""
import logging
from typing import Optional
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


def get_audit_logs(limit: int = 200, module: Optional[str] = None,
                   action: Optional[str] = None,
                   user_id: Optional[int] = None) -> list:
    try:
        sql = """
            SELECT al.id, u.username, al.action, al.module, al.record_id,
                   al.old_value, al.new_value, al.timestamp
            FROM   audit_logs al
            LEFT JOIN users u ON al.user_id = u.id
            WHERE 1=1
        """
        params = []
        if module:
            sql += " AND al.module=?"; params.append(module)
        if action:
            sql += " AND al.action=?"; params.append(action)
        if user_id:
            sql += " AND al.user_id=?"; params.append(user_id)
        sql += " ORDER BY al.timestamp DESC"
        sql = f"SELECT TOP ({limit}) * FROM ({sql}) t ORDER BY timestamp DESC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_audit_logs error: {e}")
        return []


def get_audit_modules() -> list:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "SELECT DISTINCT module FROM audit_logs WHERE module IS NOT NULL ORDER BY module"
            )
            return [r[0] for r in cursor.fetchall()]
    except Exception as e:
        logger.error(f"get_audit_modules error: {e}")
        return []


def get_audit_actions() -> list:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("SELECT DISTINCT action FROM audit_logs ORDER BY action")
            return [r[0] for r in cursor.fetchall()]
    except Exception as e:
        logger.error(f"get_audit_actions error: {e}")
        return []
