"""FitLife — Progress Model"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class ProgressRecord:
    id: int
    member_id: int
    trainer_id: Optional[int]
    record_date: date
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    body_fat_pct: Optional[float] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    arm_cm: Optional[float] = None
    bench_press_max_kg: Optional[float] = None
    squat_max_kg: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
