"""FitLife — Audit Log Model"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AuditLog:
    id: int
    user_id: Optional[int]
    action: str
    module: Optional[str] = None
    record_id: Optional[int] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: Optional[datetime] = None
    username: Optional[str] = None
