"""FitLife — BMI Calculator Utility"""
from typing import Optional


def calculate_bmi(weight_kg: float, height_cm: float) -> Optional[float]:
    """Calculate BMI from weight (kg) and height (cm)."""
    try:
        if not weight_kg or not height_cm or height_cm <= 0:
            return None
        h_m = height_cm / 100.0
        bmi = weight_kg / (h_m * h_m)
        return round(bmi, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def get_bmi_category(bmi: float) -> str:
    """Returns BMI category string."""
    if bmi is None:
        return "Unknown"
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25.0:
        return "Normal Weight"
    elif bmi < 30.0:
        return "Overweight"
    else:
        return "Obese"


def get_bmi_color(bmi: float) -> str:
    """Returns a hex color for BMI status."""
    if bmi is None:
        return "#6B7280"
    if bmi < 18.5:
        return "#00B4D8"   # Blue — Underweight
    elif bmi < 25.0:
        return "#00E676"   # Green — Normal
    elif bmi < 30.0:
        return "#FFB800"   # Amber — Overweight
    else:
        return "#FF2D78"   # Red — Obese


def get_ideal_weight_range(height_cm: float) -> tuple[float, float]:
    """Returns (min_kg, max_kg) for BMI 18.5–24.9 given height."""
    try:
        h_m = height_cm / 100.0
        return round(18.5 * h_m * h_m, 1), round(24.9 * h_m * h_m, 1)
    except Exception:
        return 0.0, 0.0


def estimate_body_fat(bmi: float, age: int = 30) -> Optional[float]:
    """Rough Deurenberg formula for body fat %."""
    try:
        # Male formula
        bf = (1.20 * bmi) + (0.23 * age) - 16.2
        return round(max(0.0, bf), 1)
    except Exception:
        return None
