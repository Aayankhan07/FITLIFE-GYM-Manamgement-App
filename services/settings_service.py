"""FitLife — Settings Service (Phase 7)"""
import logging
from typing import Optional, Any
from database.connection import DatabaseConnection
import services.auth_service as auth_svc

logger = logging.getLogger(__name__)


# ── System Settings (key/value store) ─────────────────────────────────────────
def get_setting(key: str, default: str = "") -> str:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key=?", (key,))
            row = cursor.fetchone()
            return row[0] if row and row[0] is not None else default
    except Exception as e:
        logger.error(f"get_setting({key}): {e}"); return default


def set_setting(key: str, value: str, description: str = "", updated_by: int = 0) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("SELECT id FROM system_settings WHERE setting_key=?", (key,))
            if cursor.fetchone():
                cursor.execute("UPDATE system_settings SET setting_value=? WHERE setting_key=?", (value, key))
            else:
                cursor.execute(
                    "INSERT INTO system_settings(setting_key,setting_value,description) VALUES(?,?,?)",
                    (key, value, description)
                )
        return {"success": True, "message": f"Setting '{key}' saved."}
    except Exception as e:
        logger.error(f"set_setting({key}): {e}")
        return {"success": False, "message": str(e)}


def get_all_settings() -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("SELECT setting_key, setting_value FROM system_settings")
            return {row[0]: row[1] for row in cursor.fetchall()}
    except Exception as e:
        logger.error(f"get_all_settings: {e}"); return {}


def bulk_save_settings(settings: dict, updated_by: int) -> dict:
    errors = []
    for key, value in settings.items():
        r = set_setting(key, str(value))
        if not r["success"]: errors.append(key)
    if errors:
        return {"success": False, "message": f"Failed to save: {', '.join(errors)}"}
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "INSERT INTO audit_logs(user_id,action,module,new_value,timestamp) VALUES(?,?,?,?,GETDATE())",
                (updated_by, "UPDATE", "Settings", f"Saved {len(settings)} settings")
            )
    except Exception: pass
    return {"success": True, "message": f"{len(settings)} settings saved."}


# ── Notification Settings ──────────────────────────────────────────────────────
def get_notification_settings(user_id: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT email_notifications, whatsapp_notifications, phone_number, email
                FROM notification_settings WHERE user_id=?
            """, (user_id,))
            row = cursor.fetchone()
            if row:
                return {"email_notif": bool(row[0]), "whatsapp_notif": bool(row[1]),
                        "phone": row[2] or "", "email": row[3] or ""}
            return {"email_notif": True, "whatsapp_notif": True, "phone": "", "email": ""}
    except Exception as e:
        logger.error(f"get_notification_settings: {e}")
        return {"email_notif": True, "whatsapp_notif": True, "phone": "", "email": ""}


def save_notification_settings(user_id: int, data: dict) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("SELECT id FROM notification_settings WHERE user_id=?", (user_id,))
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE notification_settings
                    SET email_notifications=?, whatsapp_notifications=?, phone_number=?, email=?
                    WHERE user_id=?
                """, (data["email_notif"], data["whatsapp_notif"],
                      data.get("phone",""), data.get("email",""), user_id))
            else:
                cursor.execute("""
                    INSERT INTO notification_settings(user_id,email_notifications,whatsapp_notifications,phone_number,email)
                    VALUES(?,?,?,?,?)
                """, (user_id, data["email_notif"], data["whatsapp_notif"],
                      data.get("phone",""), data.get("email","")))
        return {"success": True, "message": "Notification settings saved."}
    except Exception as e:
        logger.error(f"save_notification_settings: {e}")
        return {"success": False, "message": str(e)}


def change_own_password(user_id: int, current_pw: str, new_pw: str) -> dict:
    return auth_svc.change_password(user_id, current_pw, new_pw)


def get_expiring_memberships(days_ahead: int = 7, branch_id: Optional[int] = None) -> list:
    """Used by reminder system."""
    try:
        sql = """
            SELECT m.full_name, m.phone, m.email, m.expiry_date,
                   b.branch_name, mp.plan_name
            FROM   members m
            JOIN   branches b ON m.branch_id=b.id
            LEFT JOIN membership_plans mp ON m.membership_plan_id=mp.id
            WHERE  m.status='Active'
            AND    m.expiry_date BETWEEN CAST(GETDATE() AS DATE)
                   AND DATEADD(day,?,CAST(GETDATE() AS DATE))
        """
        params = [days_ahead]
        if branch_id:
            sql += " AND m.branch_id=?"; params.append(branch_id)
        sql += " ORDER BY m.expiry_date"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_expiring_memberships: {e}"); return []


def get_overdue_payments(branch_id: Optional[int] = None) -> list:
    try:
        sql = """
            SELECT m.full_name, m.phone, py.invoice_number, py.amount, py.payment_date
            FROM payments py JOIN members m ON py.member_id=m.id
            WHERE py.status IN ('Unpaid','Overdue')
        """
        params = []
        if branch_id:
            sql += " AND m.branch_id=?"; params.append(branch_id)
        sql += " ORDER BY py.payment_date"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_overdue_payments: {e}"); return []


def get_ai_settings() -> dict:
    import json
    try:
        with open("config/settings.json", "r", encoding="utf-8") as f:
            return json.load(f).get("ai", {})
    except Exception:
        return {}

def save_ai_settings(provider: str, api_key: str, model: str) -> dict:
    import json, os
    try:
        data = {}
        if os.path.exists("config/settings.json"):
            with open("config/settings.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        
        if "ai" not in data:
            data["ai"] = {}
        
        data["ai"]["provider"] = provider
        data["ai"]["api_key"] = api_key
        data["ai"]["model"] = model
        
        with open("config/settings.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        return {"success": True, "message": "AI settings saved successfully."}
    except Exception as e:
        logger.error(f"save_ai_settings error: {e}")
        return {"success": False, "message": str(e)}
