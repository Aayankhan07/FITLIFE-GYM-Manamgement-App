"""FitLife — Formatters Utility"""
from datetime import date, datetime
from typing import Optional


def format_currency(amount: float, symbol: str = "Rs.") -> str:
    """Format number as currency: Rs. 50,000"""
    try:
        return f"{symbol} {amount:,.0f}"
    except (ValueError, TypeError):
        return f"{symbol} 0"


def format_date(d, fmt: str = "%d/%m/%Y") -> str:
    """Format date to string."""
    if d is None:
        return "—"
    try:
        if isinstance(d, (date, datetime)):
            return d.strftime(fmt)
        return str(d)
    except Exception:
        return str(d) if d else "—"


def format_datetime(dt, fmt: str = "%d/%m/%Y %H:%M") -> str:
    """Format datetime to string."""
    if dt is None:
        return "—"
    try:
        if isinstance(dt, datetime):
            return dt.strftime(fmt)
        return str(dt)
    except Exception:
        return str(dt) if dt else "—"


def format_percentage(value: float, decimals: int = 1) -> str:
    try:
        return f"{value:.{decimals}f}%"
    except (ValueError, TypeError):
        return "0%"


def format_bmi(bmi: Optional[float]) -> str:
    if bmi is None:
        return "—"
    try:
        val = float(bmi)
        if val < 18.5:
            category = "Underweight"
        elif val < 25:
            category = "Normal"
        elif val < 30:
            category = "Overweight"
        else:
            category = "Obese"
        return f"{val:.1f} ({category})"
    except (ValueError, TypeError):
        return "—"


def format_phone(phone: Optional[str]) -> str:
    if not phone:
        return "—"
    p = "".join(c for c in phone if c.isdigit())
    if len(p) == 11:
        return f"{p[:4]}-{p[4:]}"
    return phone


def format_cnic(cnic: Optional[str]) -> str:
    if not cnic:
        return "—"
    c = "".join(c for c in cnic if c.isdigit())
    if len(c) == 13:
        return f"{c[:5]}-{c[5:12]}-{c[12]}"
    return cnic


def truncate(text: str, max_len: int = 50) -> str:
    if not text:
        return ""
    return text if len(text) <= max_len else text[:max_len - 3] + "..."


def days_until(d: Optional[date]) -> Optional[int]:
    """Returns number of days until a date (negative if past)."""
    if d is None:
        return None
    try:
        if isinstance(d, datetime):
            d = d.date()
        return (d - date.today()).days
    except Exception:
        return None


def status_to_icon(status: str) -> str:
    mapping = {
        "Active": "✅", "Inactive": "⭕", "Expired": "❌",
        "Suspended": "🚫", "Paid": "✅", "Unpaid": "❌",
        "Overdue": "🔴", "Partial": "🟡", "Pending": "⏳",
        "Good": "🟢", "Fair": "🟡", "Damaged": "🔴", "New": "✨",
        "Present": "✅", "Absent": "❌", "Late": "⚠️",
    }
    return mapping.get(status, "—")
