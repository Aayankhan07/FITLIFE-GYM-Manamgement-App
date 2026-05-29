"""
FitLife — Notification Service
In-app notifications: create, fetch, mark read, clear.
No external services needed (email/WhatsApp are optional).
"""
import logging
from typing import Optional
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)

# ── In-Memory notification store (per session) ────────────────────────────────
_notifications: list[dict] = []


def push_notification(user_id: int, title: str, message: str,
                      notif_type: str = "info") -> None:
    """
    Push an in-app notification to the in-memory store.
    Types: info | success | warning | error | alert
    """
    _notifications.append({
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": notif_type,
        "is_read": False,
    })
    logger.debug(f"Notification pushed: [{notif_type}] {title} for user={user_id}")


def get_notifications(user_id: int) -> list[dict]:
    """Get all unread notifications for a user."""
    return [n for n in _notifications if n["user_id"] == user_id and not n["is_read"]]


def get_unread_count(user_id: int) -> int:
    """Count of unread notifications for a user."""
    return sum(1 for n in _notifications if n["user_id"] == user_id and not n["is_read"])


def mark_all_read(user_id: int) -> None:
    """Mark all notifications as read for a user."""
    for n in _notifications:
        if n["user_id"] == user_id:
            n["is_read"] = True


def clear_all(user_id: int) -> None:
    """Remove all notifications for a user."""
    global _notifications
    _notifications = [n for n in _notifications if n["user_id"] != user_id]


# ── Notification Settings (DB) ─────────────────────────────────────────────────
def get_notification_settings(user_id: int) -> Optional[object]:
    """Fetch user notification preferences from DB."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "SELECT * FROM notification_settings WHERE user_id=?", (user_id,)
            )
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"get_notification_settings error: {e}")
        return None


def save_notification_settings(user_id: int, email_notif: bool,
                                whatsapp_notif: bool,
                                phone: str = "", email: str = "") -> dict:
    """Upsert notification settings."""
    try:
        existing = get_notification_settings(user_id)
        with DatabaseConnection() as (conn, cursor):
            if existing:
                cursor.execute("""
                    UPDATE notification_settings
                    SET email_notifications=?, whatsapp_notifications=?,
                        phone_number=?, email=?
                    WHERE user_id=?
                """, (1 if email_notif else 0, 1 if whatsapp_notif else 0,
                      phone or None, email or None, user_id))
            else:
                cursor.execute("""
                    INSERT INTO notification_settings
                        (user_id, email_notifications, whatsapp_notifications, phone_number, email)
                    VALUES (?,?,?,?,?)
                """, (user_id, 1 if email_notif else 0, 1 if whatsapp_notif else 0,
                      phone or None, email or None))
        return {"success": True, "message": "Notification settings saved."}
    except Exception as e:
        logger.error(f"save_notification_settings error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to save settings: {e}"}


# ── Auto-notification triggers ─────────────────────────────────────────────────
def notify_expiring_memberships(days: int = 7) -> int:
    """Push notifications for members whose memberships expire within `days` days."""
    try:
        from services.member_service import get_expiring_soon
        expiring = get_expiring_soon(days=days)
        count = 0
        for row in expiring:
            member_id, full_name, phone, email, expiry_date, branch_name = row
            push_notification(
                user_id=1,  # notify admin
                title="Membership Expiring Soon",
                message=f"{full_name} ({branch_name}) expires on {expiry_date}.",
                notif_type="warning"
            )
            count += 1
        logger.info(f"Notified {count} expiring memberships.")
        return count
    except Exception as e:
        logger.error(f"notify_expiring_memberships error: {e}")
        return 0


def notify_overdue_payments() -> int:
    """Push notifications for overdue payments."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT m.full_name, p.amount, p.invoice_number
                FROM payments p
                JOIN members m ON p.member_id = m.id
                WHERE p.status = 'Overdue'
            """)
            rows = cursor.fetchall()
        count = 0
        for row in rows:
            push_notification(
                user_id=1,
                title="Overdue Payment",
                message=f"{row[0]}: Rs.{row[1]:,.0f} overdue (Invoice: {row[2]}).",
                notif_type="error"
            )
            count += 1
        logger.info(f"Notified {count} overdue payments.")
        return count
    except Exception as e:
        logger.error(f"notify_overdue_payments error: {e}")
        return 0
