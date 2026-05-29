"""FitLife — Diet Plan Model"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class DietMeal:
    id: int
    diet_plan_id: int
    meal_type: str
    food_items: str
    portion_size: Optional[str] = None
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fats_g: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class DietPlan:
    id: int
    member_id: int
    created_by: int
    plan_name: str
    goal: str
    total_daily_calories: int
    protein_g: int = 0
    carbs_g: int = 0
    fats_g: int = 0
    duration_weeks: int = 4
    status: str = "Draft"
    verified_by: Optional[int] = None
    ai_generated: bool = False
    rejection_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    meals: List[DietMeal] = field(default_factory=list)
