"""FitLife — Membership Model"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class MembershipPlan:
    id: int
    plan_name: str
    duration_days: int
    price: float
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None


@dataclass
class Membership:
    id: int
    member_id: int
    plan_id: int
    start_date: date
    end_date: date
    status: str = "Active"
    created_at: Optional[datetime] = None
