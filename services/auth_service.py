"""
FitLife — Authentication Service
Handles login, password hashing, session management, lockout logic.
"""

import bcrypt
import logging
import json
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field
from database.connection import DatabaseConnection
from config.constants import (
    MAX_LOGIN_ATTEMPTS, LOCKOUT_DURATION_MINUTES,
    SESSION_TIMEOUT_MINUTES, SESSION_WARNING_MINUTES,
    ACTION_LOGIN, ACTION_LOGOUT, ACTION_LOGIN_FAILED, ACTION_LOGIN_LOCKED,
    ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER
)

logger = logging.getLogger(__name__)


# ─── Session Data Class ───────────────────────────────────────────────────────
@dataclass
class UserSession:
    user_id:    int
    username:   str
    full_name:  str
    role:       str
    role_id:    int
    branch_id:  Optional[int]
    email:      str
    phone:      str
    theme_pref: str
    login_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def refresh(self):
        self.last_activity = datetime.now()

    def is_expired(self) -> bool:
        delta = (datetime.now() - self.last_activity).total_seconds() / 60
        return delta >= SESSION_TIMEOUT_MINUTES

    def warn_expiry(self) -> bool:
        delta = (datetime.now() - self.last_activity).total_seconds() / 60
        return delta >= SESSION_WARNING_MINUTES

    def minutes_until_timeout(self) -> int:
        elapsed = (datetime.now() - self.last_activity).total_seconds() / 60
        return max(0, int(SESSION_TIMEOUT_MINUTES - elapsed))

    def to_dict(self) -> dict:
        return {
            "user_id":   self.user_id,
            "username":  self.username,
            "full_name": self.full_name,
            "role":      self.role,
            "branch_id": self.branch_id,
        }


# ─── Global Session ───────────────────────────────────────────────────────────
_current_session: Optional[UserSession] = None


def get_current_session() -> Optional[UserSession]:
    return _current_session


def get_current_user() -> Optional[UserSession]:
    return _current_session


def require_session() -> UserSession:
    if _current_session is None:
        raise RuntimeError("No active session.")
    return _current_session


def clear_session():
    global _current_session
    _current_session = None


# ─── Password Utilities ───────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


# ─── Lockout Helpers ─────────────────────────────────────────────────────────
def _is_locked(locked_until: Optional[datetime]) -> tuple[bool, int]:
    """Returns (is_locked, seconds_remaining)."""
    if locked_until is None:
        return False, 0
    now = datetime.now()
    if now < locked_until:
        remaining = int((locked_until - now).total_seconds())
        return True, remaining
    return False, 0


def _increment_failed_attempts(user_id: int, current_attempts: int):
    new_attempts = current_attempts + 1
    locked_until = None
    if new_attempts >= MAX_LOGIN_ATTEMPTS:
        locked_until = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        logger.warning(f"Account locked for user_id={user_id} until {locked_until}")
    with DatabaseConnection() as (conn, cursor):
        cursor.execute(
            "UPDATE users SET failed_attempts=?, locked_until=?, updated_at=GETDATE() WHERE id=?",
            (new_attempts, locked_until, user_id)
        )
    return new_attempts, locked_until


def _reset_failed_attempts(user_id: int):
    with DatabaseConnection() as (conn, cursor):
        cursor.execute(
            "UPDATE users SET failed_attempts=0, locked_until=NULL, last_login=GETDATE(), updated_at=GETDATE() WHERE id=?",
            (user_id,)
        )


# ─── Audit Log Helper ─────────────────────────────────────────────────────────
def _log_audit(user_id: Optional[int], action: str, details: str = ""):
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "INSERT INTO audit_logs (user_id, action, module, new_value, timestamp) VALUES (?,?,?,?,GETDATE())",
                (user_id, action, "Auth", details)
            )
    except Exception as e:
        logger.error(f"Audit log failed: {e}")


# ─── Main Login Function ──────────────────────────────────────────────────────
def login(username: str, password: str) -> dict:
    """
    Attempt login. Returns dict with:
      success (bool), message (str), session (UserSession or None),
      locked (bool), lock_seconds (int)
    """
    global _current_session

    if not username or not password:
        return {"success": False, "message": "Username and password are required.", "locked": False, "lock_seconds": 0}

    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT u.id, u.username, u.password_hash, u.full_name, u.email, u.phone,
                       u.branch_id, u.is_active, u.failed_attempts, u.locked_until,
                       u.theme_pref, r.role_name, r.id AS role_id
                FROM   users u
                JOIN   roles r ON u.role_id = r.id
                WHERE  u.username = ?
            """, (username,))
            row = cursor.fetchone()

        if row is None:
            logger.warning(f"Login attempt for unknown username: {username}")
            return {"success": False, "message": "Invalid credentials. Please try again.", "locked": False, "lock_seconds": 0}

        (uid, uname, pw_hash, full_name, email, phone,
         branch_id, is_active, failed_attempts, locked_until,
         theme_pref, role_name, role_id) = row

        # Check active
        if not is_active:
            return {"success": False, "message": "Your account has been deactivated. Contact admin.", "locked": False, "lock_seconds": 0}

        # Check lockout
        locked, secs = _is_locked(locked_until)
        if locked:
            mins = secs // 60
            secs_rem = secs % 60
            _log_audit(uid, ACTION_LOGIN_LOCKED, f"Account locked, {secs}s remaining")
            return {
                "success": False,
                "message": f"Account locked due to too many failed attempts.\nTry again in {mins}m {secs_rem}s.",
                "locked": True,
                "lock_seconds": secs
            }

        # Verify password
        if not verify_password(password, pw_hash):
            attempts, locked_until_new = _increment_failed_attempts(uid, failed_attempts)
            remaining = MAX_LOGIN_ATTEMPTS - attempts
            _log_audit(uid, ACTION_LOGIN_FAILED, f"Attempt {attempts}")
            if attempts >= MAX_LOGIN_ATTEMPTS:
                return {
                    "success": False,
                    "message": f"Too many failed attempts. Account locked for {LOCKOUT_DURATION_MINUTES} minutes.",
                    "locked": True,
                    "lock_seconds": LOCKOUT_DURATION_MINUTES * 60
                }
            return {
                "success": False,
                "message": f"Invalid credentials. {remaining} attempt(s) remaining.",
                "locked": False,
                "lock_seconds": 0
            }

        # Success
        _reset_failed_attempts(uid)
        session = UserSession(
            user_id=uid, username=uname, full_name=full_name,
            role=role_name, role_id=role_id, branch_id=branch_id,
            email=email or "", phone=phone or "",
            theme_pref=theme_pref or "dark"
        )
        _current_session = session
        _log_audit(uid, ACTION_LOGIN, f"Role: {role_name}")
        logger.info(f"User '{uname}' logged in as {role_name}")
        return {"success": True, "message": f"Welcome, {full_name}!", "session": session, "locked": False, "lock_seconds": 0}

    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return {"success": False, "message": "A system error occurred. Please try again.", "locked": False, "lock_seconds": 0}


def logout():
    """Log out the current user."""
    global _current_session
    if _current_session:
        _log_audit(_current_session.user_id, ACTION_LOGOUT, "")
        logger.info(f"User '{_current_session.username}' logged out.")
    _current_session = None


def change_password(user_id: int, old_password: str, new_password: str) -> dict:
    """Change password for a user, verifying the old one first."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("SELECT password_hash FROM users WHERE id=?", (user_id,))
            row = cursor.fetchone()
        if not row:
            return {"success": False, "message": "User not found."}
        if not verify_password(old_password, row[0]):
            return {"success": False, "message": "Current password is incorrect."}
        if len(new_password) < 8:
            return {"success": False, "message": "New password must be at least 8 characters."}
        new_hash = hash_password(new_password)
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("UPDATE users SET password_hash=?, updated_at=GETDATE() WHERE id=?", (new_hash, user_id))
        _log_audit(user_id, "PASSWORD_CHANGE", "Password changed successfully")
        return {"success": True, "message": "Password changed successfully."}
    except Exception as e:
        logger.error(f"Change password error: {e}")
        return {"success": False, "message": "Failed to change password. Please try again."}


def admin_reset_password(admin_user_id: int, target_user_id: int, new_password: str) -> dict:
    """Admin resets another user's password."""
    try:
        if len(new_password) < 8:
            return {"success": False, "message": "Password must be at least 8 characters."}
        new_hash = hash_password(new_password)
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE users SET password_hash=?, failed_attempts=0, locked_until=NULL, updated_at=GETDATE() WHERE id=?",
                (new_hash, target_user_id)
            )
        _log_audit(admin_user_id, "ADMIN_RESET_PASSWORD", f"Reset password for user_id={target_user_id}")
        return {"success": True, "message": "Password reset successfully."}
    except Exception as e:
        logger.error(f"Admin reset password error: {e}")
        return {"success": False, "message": "Failed to reset password."}


def unlock_account(admin_user_id: int, target_user_id: int) -> dict:
    """Admin unlocks a locked account."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE users SET failed_attempts=0, locked_until=NULL, updated_at=GETDATE() WHERE id=?",
                (target_user_id,)
            )
        _log_audit(admin_user_id, "ACCOUNT_UNLOCK", f"Unlocked user_id={target_user_id}")
        return {"success": True, "message": "Account unlocked successfully."}
    except Exception as e:
        logger.error(f"Unlock account error: {e}")
        return {"success": False, "message": "Failed to unlock account."}


def save_theme_preference(user_id: int, theme: str):
    """Save user's theme preference."""
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("UPDATE users SET theme_pref=? WHERE id=?", (theme, user_id))
        if _current_session and _current_session.user_id == user_id:
            _current_session.theme_pref = theme
    except Exception as e:
        logger.error(f"Save theme pref error: {e}")
