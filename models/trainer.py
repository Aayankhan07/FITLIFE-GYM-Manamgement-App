"""FitLife — Trainer Model"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Trainer:
    id: int
    user_id: Optional[int]
    branch_id: int
    full_name: str
    cnic: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    photo_path: Optional[str] = None
    specialization: str = "General Fitness"
    monthly_salary: float = 0.0
    hire_date: Optional[date] = None
    qualification: Optional[str] = None
    certifications: Optional[str] = None
    status: str = "Active"
    performance_rating: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    branch_name: Optional[str] = None
