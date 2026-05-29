"""FitLife — User Model (dataclass)"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    role_id: int
    role_name: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    branch_id: Optional[int] = None
    is_active: bool = True
    last_login: Optional[datetime] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    theme_pref: str = "dark"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        return datetime.now() < self.locked_until

    @property
    def display_name(self) -> str:
        return self.full_name or self.username

    @classmethod
    def from_row(cls, row) -> "User":
        """Create User from a DB row tuple."""
        return cls(
            id=row[0], username=row[1], password_hash=row[2],
            role_id=row[3], role_name=row[4] if len(row) > 4 else "",
            full_name=row[5] if len(row) > 5 else "",
            email=row[6] if len(row) > 6 else None,
            phone=row[7] if len(row) > 7 else None,
            branch_id=row[8] if len(row) > 8 else None,
            is_active=bool(row[9]) if len(row) > 9 else True,
        )
