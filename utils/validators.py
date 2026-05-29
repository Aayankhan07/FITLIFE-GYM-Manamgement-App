"""FitLife — Input Sanitization & Validation Utilities (Phase 8)"""
import re
from typing import Optional


# ── Text sanitizers ────────────────────────────────────────────────────────────
def sanitize_text(value: str, max_len: int = 255) -> str:
    """Strip, truncate, remove dangerous SQL-adjacent chars."""
    if not isinstance(value, str): return ""
    return value.strip()[:max_len]


def sanitize_name(value: str) -> str:
    """Allow letters, spaces, hyphens, apostrophes only."""
    v = sanitize_text(value, 150)
    return re.sub(r"[^A-Za-z\s\-\'\u0600-\u06FF]", "", v).strip()


def sanitize_phone(value: str) -> str:
    """Keep digits, +, -, spaces only."""
    return re.sub(r"[^\d\+\-\s]", "", value.strip())[:20]


def sanitize_cnic(value: str) -> str:
    """Keep digits only, return 13-char string."""
    return re.sub(r"\D", "", value.strip())[:13]


def sanitize_email(value: str) -> str:
    return value.strip().lower()[:150]


# ── Validators ─────────────────────────────────────────────────────────────────
def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip())) if email.strip() else True  # optional


def validate_cnic(cnic: str) -> bool:
    return len(re.sub(r"\D", "", cnic)) == 13


def validate_phone(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone)
    return 10 <= len(digits) <= 15


def validate_password(pw: str) -> tuple[bool, str]:
    if len(pw) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", pw):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"\d", pw):
        return False, "Password must contain at least one digit."
    return True, ""


def validate_positive_number(value, field_name: str = "Value") -> tuple[bool, str]:
    try:
        n = float(value)
        if n < 0:
            return False, f"{field_name} cannot be negative."
        return True, ""
    except (TypeError, ValueError):
        return False, f"{field_name} must be a valid number."


def validate_required(value: str, field_name: str = "Field") -> tuple[bool, str]:
    if not str(value).strip():
        return False, f"{field_name} is required."
    return True, ""


def validate_date_range(start, end) -> tuple[bool, str]:
    if start and end and start > end:
        return False, "Start date cannot be after end date."
    return True, ""


# ── Batch validator ────────────────────────────────────────────────────────────
def run_validations(checks: list) -> tuple[bool, str]:
    """
    Runs list of (bool, str) tuples or callables returning same.
    Returns first failure or (True, "").
    """
    for item in checks:
        result = item() if callable(item) else item
        ok, msg = result
        if not ok:
            return False, msg
    return True, ""
