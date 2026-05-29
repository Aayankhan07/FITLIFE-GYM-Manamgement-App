"""FitLife — Payment Model"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Payment:
    id: int
    member_id: int
    membership_id: Optional[int]
    amount: float
    payment_date: date
    payment_method: str
    status: str
    invoice_number: str
    receipt_path: Optional[str] = None
    recorded_by: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    member_name: Optional[str] = None
    branch_name: Optional[str] = None
