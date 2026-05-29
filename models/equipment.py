"""FitLife — Equipment Model"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Equipment:
    id: int
    branch_id: int
    name: str
    category: str
    quantity: int = 1
    purchase_date: Optional[date] = None
    purchase_price: Optional[float] = None
    condition: str = "Good"
    status: str = "Active"
    next_maintenance_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    branch_name: Optional[str] = None


@dataclass
class MaintenanceRecord:
    id: int
    equipment_id: int
    date: date
    description: str
    cost: Optional[float] = None
    performed_by: Optional[str] = None
    status: str = "Completed"
    created_at: Optional[datetime] = None
