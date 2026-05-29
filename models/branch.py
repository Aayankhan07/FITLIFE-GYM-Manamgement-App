"""FitLife — Branch Model"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Branch:
    id: int
    branch_name: str
    city: str
    address: str
    phone: str
    email: Optional[str] = None
    capacity: int = 100
    opening_date: Optional[date] = None
    status: str = "Active"
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
