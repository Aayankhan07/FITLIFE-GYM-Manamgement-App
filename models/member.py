"""FitLife — Member Model"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Member:
    id: int
    user_id: Optional[int]
    branch_id: int
    trainer_id: Optional[int]
    full_name: str
    cnic: str
    date_of_birth: date
    phone: str
    email: Optional[str] = None
    emergency_contact: Optional[str] = None
    address: Optional[str] = None
    photo_path: Optional[str] = None
    fitness_goal: str = "Maintenance"
    health_conditions: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    bmi: Optional[float] = None
    join_date: Optional[date] = None
    membership_plan_id: Optional[int] = None
    expiry_date: Optional[date] = None
    status: str = "Active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    branch_name: Optional[str] = None
    trainer_name: Optional[str] = None
    plan_name: Optional[str] = None
