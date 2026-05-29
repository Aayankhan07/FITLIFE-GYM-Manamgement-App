"""FitLife — Attendance Model"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Attendance:
    id: int
    member_id: int
    branch_id: int
    date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: str = "Present"
    recorded_by: Optional[int] = None
    notes: Optional[str] = None
    member_name: Optional[str] = None
