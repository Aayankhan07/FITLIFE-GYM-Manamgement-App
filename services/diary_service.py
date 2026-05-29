"""
FitLife — Diary Service
CRUD for personal diary entries. Private per user (no cross-user access).
"""
import logging
from datetime import date
from typing import Optional
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


def get_entries(user_id: int, search: Optional[str] = None,
                tag: Optional[str] = None, pinned_only: bool = False) -> list:
    """Fetch diary entries for a user. No cross-user access."""
    try:
        sql = """
            SELECT id, user_id, title, body, entry_date, tags, is_pinned, is_deleted,
                   created_at, updated_at
            FROM   diary_entries
            WHERE  user_id=? AND is_deleted=0
        """
        params = [user_id]
        if search:
            sql += " AND (title LIKE ? OR body LIKE ?)"
            s = f"%{search}%"
            params += [s, s]
        if tag:
            sql += " AND tags LIKE ?"
            params.append(f"%{tag}%")
        if pinned_only:
            sql += " AND is_pinned=1"
        sql += " ORDER BY is_pinned DESC, entry_date DESC, created_at DESC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_entries error: {e}")
        return []


def get_entry_by_id(entry_id: int, user_id: int) -> Optional[object]:
    """Returns single entry if it belongs to the user (security check)."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "SELECT * FROM diary_entries WHERE id=? AND user_id=? AND is_deleted=0",
                (entry_id, user_id)
            )
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"get_entry_by_id error: {e}")
        return None


def create_entry(user_id: int, title: str, body: str,
                 entry_date: Optional[date] = None,
                 tags: Optional[str] = None,
                 is_pinned: bool = False) -> dict:
    """Create a new diary entry."""
    try:
        d = entry_date or date.today()
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO diary_entries
                    (user_id, title, body, entry_date, tags, is_pinned, is_deleted,
                     created_at, updated_at)
                VALUES (?,?,?,?,?,?,0,GETDATE(),GETDATE())
            """, (user_id, title, body, d, tags, 1 if is_pinned else 0))
            cursor.execute("SELECT @@IDENTITY")
            new_id = int(cursor.fetchone()[0])
        logger.info(f"Diary entry created: id={new_id} for user={user_id}")
        return {"success": True, "entry_id": new_id, "message": "Entry saved."}
    except Exception as e:
        logger.error(f"create_entry error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to save entry: {e}"}


def update_entry(entry_id: int, user_id: int, title: str, body: str,
                 entry_date: Optional[date] = None,
                 tags: Optional[str] = None,
                 is_pinned: bool = False) -> dict:
    """Update diary entry — security check: user must own entry."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                UPDATE diary_entries
                SET title=?, body=?, entry_date=?, tags=?, is_pinned=?,
                    updated_at=GETDATE()
                WHERE id=? AND user_id=?
            """, (title, body, entry_date or date.today(), tags,
                  1 if is_pinned else 0, entry_id, user_id))
            if cursor.rowcount == 0:
                return {"success": False, "message": "Entry not found or not authorized."}
        return {"success": True, "message": "Entry updated."}
    except Exception as e:
        logger.error(f"update_entry error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to update entry: {e}"}


def delete_entry(entry_id: int, user_id: int) -> dict:
    """Soft-delete a diary entry (user must own it)."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE diary_entries SET is_deleted=1, updated_at=GETDATE() WHERE id=? AND user_id=?",
                (entry_id, user_id)
            )
            if cursor.rowcount == 0:
                return {"success": False, "message": "Entry not found or not authorized."}
        return {"success": True, "message": "Entry deleted."}
    except Exception as e:
        logger.error(f"delete_entry error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to delete entry: {e}"}


def toggle_pin(entry_id: int, user_id: int) -> dict:
    """Toggle the pinned state of an entry."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE diary_entries SET is_pinned = CASE WHEN is_pinned=1 THEN 0 ELSE 1 END, "
                "updated_at=GETDATE() WHERE id=? AND user_id=?",
                (entry_id, user_id)
            )
        return {"success": True, "message": "Pin status toggled."}
    except Exception as e:
        logger.error(f"toggle_pin error: {e}")
        return {"success": False, "message": str(e)}


def get_entry_count(user_id: int) -> int:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "SELECT COUNT(*) FROM diary_entries WHERE user_id=? AND is_deleted=0",
                (user_id,)
            )
            return cursor.fetchone()[0] or 0
    except Exception as e:
        logger.error(f"get_entry_count error: {e}")
        return 0
