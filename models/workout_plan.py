"""FitLife — Workout Plan Model"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class WorkoutExercise:
    id: int
    workout_plan_id: int
    day_of_week: str
    exercise_name: str
    sets: int = 3
    reps: Optional[int] = None
    rest_seconds: int = 60
    duration_mins: Optional[int] = None
    weight_kg: Optional[float] = None
    notes: Optional[str] = None
    order_index: int = 1


@dataclass
class WorkoutPlan:
    id: int
    member_id: int
    created_by: int
    plan_name: str
    goal: str
    duration_weeks: int = 4
    status: str = "Draft"
    verified_by: Optional[int] = None
    ai_generated: bool = False
    rejection_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    exercises: List[WorkoutExercise] = field(default_factory=list)
