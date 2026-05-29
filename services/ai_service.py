"""
FitLife — AI Service
Smart Ask chat + AI plan generation with graceful fallback.
"""
import logging
import json
from typing import Optional
from config.constants import ROLE_ADMIN, ROLE_MANAGER, ROLE_TRAINER, ROLE_MEMBER

logger = logging.getLogger(__name__)


def _load_settings() -> dict:
    try:
        with open("config/settings.json", "r", encoding="utf-8") as f:
            return json.load(f).get("ai", {})
    except Exception:
        return {}


def is_api_configured() -> bool:
    s = _load_settings()
    key = s.get("api_key", "").strip()
    return bool(key and key not in ("", "your-openai-api-key-here"))


def ask_question(question: str, role: str, user_id: int,
                 context: Optional[str] = None) -> dict:
    """Ask AI a question; returns rule-based answer if API not configured."""
    try:
        if not is_api_configured():
            answer = _rule_based_response(question, role)
            _log_qa(user_id, question, answer)
            return {"success": True, "answer": answer, "source": "rule_based",
                    "note": "AI key not configured — using built-in responses."}

        from openai import OpenAI
        settings = _load_settings()
        api_key = settings.get("api_key", "")
        model = settings.get("model", "gpt-3.5-turbo")
        max_tokens = int(settings.get("max_tokens", 500))

        client = OpenAI(api_key=api_key)
        system_prompt = _build_system_prompt(role)
        if context:
            system_prompt += f"\n\nContext: {context}"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        answer = response.choices[0].message.content.strip()
        _log_qa(user_id, question, answer)
        return {"success": True, "answer": answer, "source": "openai"}

    except Exception as e:
        logger.error(f"ask_question error: {e}", exc_info=True)
        answer = _rule_based_response(question, role)
        return {"success": True, "answer": answer, "source": "rule_based",
                "note": f"AI unavailable: {e}"}


def generate_workout_plan(member_name: str, goal: str, weeks: int,
                          fitness_level: str = "Intermediate") -> dict:
    prompt = (f"Create a {weeks}-week workout plan for {member_name}. "
              f"Goal: {goal}. Level: {fitness_level}. Format: Day|Exercise|Sets|Reps|Rest")
    if not is_api_configured():
        return {"success": True, "plan": _fallback_workout(goal, weeks), "source": "rule_based"}
    r = ask_question(prompt, ROLE_TRAINER, 0)
    return {"success": True, "plan": r.get("answer", ""), "source": r.get("source")}


def generate_diet_plan(member_name: str, goal: str, calories: int) -> dict:
    prompt = (f"Create a daily diet plan for {member_name}. "
              f"Goal: {goal}. Calories: {calories} kcal. Format: Meal|Food|Qty|Cal|Protein|Carbs|Fat")
    if not is_api_configured():
        return {"success": True, "plan": _fallback_diet(goal, calories), "source": "rule_based"}
    r = ask_question(prompt, ROLE_TRAINER, 0)
    return {"success": True, "plan": r.get("answer", ""), "source": r.get("source")}


def _build_system_prompt(role: str) -> str:
    base = (
        "You are an intelligent, capable, and helpful AI assistant for FitLife, a premium gym chain. "
        "You can act as a personal trainer, a dietitian, a business consultant, or a general helpful AI like ChatGPT. "
        "Feel free to generate detailed workout plans, comprehensive diet schedules, business strategies, or answer ANY fitness and health-related question without hesitation. "
        "Always structure your responses beautifully using Markdown (headings, bold text, lists). "
        "Use Rs. for currency when discussing prices."
    )
    return base


def _rule_based_response(question: str, role: str) -> str:
    q = question.lower()
    if any(w in q for w in ["workout", "exercise", "training"]):
        return ("Workout tips:\n• Compound lifts 3x/week\n• Progressive overload\n"
                "• 7-9h sleep\n• 3-4L water/day\n\n⚠️ Configure AI key for personalized plans.")
    if any(w in q for w in ["diet", "food", "nutrition", "calorie", "protein"]):
        return ("Nutrition basics:\n• Protein: 1.6-2.2g/kg\n• Carbs: 3-5g/kg\n• Fats: 0.8-1g/kg\n"
                "• Whole foods: rice, chicken, eggs, lentils\n\n⚠️ Configure AI key for custom plans.")
    if any(w in q for w in ["revenue", "billing", "payment"]) and role in (ROLE_ADMIN, ROLE_MANAGER):
        return ("Finance tips:\n• Target 60%+ collection before month-end\n"
                "• Follow up overdue by 10th\n• Send renewal reminders 7 days before expiry")
    return ("I'm FitLife AI. Ask me about:\n• Workout & exercise\n• Nutrition & diet\n"
            "• Progress & goals\n\n⚠️ Configure OpenAI key in Settings for full AI capabilities.")


def _fallback_workout(goal: str, weeks: int) -> str:
    return (f"Sample {goal} Plan ({weeks} weeks):\n"
            "Mon: Bench Press 4x8, Incline DB 3x10, Tricep Dips 3x12\n"
            "Tue: Deadlift 4x5, Pull-ups 3x8, Barbell Curl 3x12\n"
            "Thu: Squat 4x8, Leg Press 3x12, Calf Raise 4x15\n"
            "Fri: OHP 4x8, Lateral Raise 3x15, Face Pull 3x15")


def _fallback_diet(goal: str, calories: int) -> str:
    return (f"{goal} Diet ({calories} kcal):\n"
            "Breakfast: 3 eggs + oats + banana\nLunch: Chicken 200g + rice 150g + salad\n"
            "Snack: Yogurt + nuts\nDinner: Beef 150g + roti x2 + veggies\n"
            "Pre-workout: Banana + whey protein")


def _log_qa(user_id: int, question: str, answer: str) -> None:
    try:
        from database.connection import DatabaseConnection
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "INSERT INTO smart_ask_logs (user_id,question,answer,created_at) VALUES (?,?,?,GETDATE())",
                (user_id, question[:4000], answer[:4000])
            )
    except Exception:
        pass


def get_chat_history(user_id: int, limit: int = 20) -> list:
    try:
        from database.connection import DatabaseConnection
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "SELECT TOP (?) question, answer, created_at FROM smart_ask_logs "
                "WHERE user_id=? AND answer!='' ORDER BY created_at DESC",
                (limit, user_id)
            )
            return list(reversed(cursor.fetchall()))
    except Exception as e:
        logger.error(f"get_chat_history error: {e}")
        return []


def clear_chat_history(user_id: int) -> dict:
    try:
        from database.connection import DatabaseConnection
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("DELETE FROM smart_ask_logs WHERE user_id=?", (user_id,))
        return {"success": True, "message": "Chat history cleared."}
    except Exception as e:
        return {"success": False, "message": str(e)}
