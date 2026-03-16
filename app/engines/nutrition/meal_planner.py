"""
Meal Planner

Generates daily meal plans using Gemini, tailored to the user's
macro targets, dietary restrictions, and Indian food preferences.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.database import meal_plans_collection, users_collection
from app.engines.nutrition.macro_calculator import MacroTargets
from app.utils.llm_client import gemini_client

logger = logging.getLogger(__name__)


MEAL_PLAN_SYSTEM = """You are FitCrave's expert Indian nutritionist AI.
Generate a practical daily meal plan using common Indian foods.
Each meal must include realistic portion sizes, calorie and macro estimates.
Respect the user's dietary restrictions and allergies."""


def _build_plan_prompt(targets: MacroTargets, meal_count: int, user_context: dict) -> str:
    restrictions = user_context.get("dietary_restrictions", [])
    allergies = user_context.get("allergies", [])

    return f"""Create a {meal_count}-meal daily plan hitting these targets:
- Calories: {targets.target_calories} kcal
- Protein: {targets.protein_g}g
- Carbs: {targets.carbs_g}g
- Fat: {targets.fat_g}g
- Goal: {targets.goal.value}

Dietary restrictions: {', '.join(restrictions) if restrictions else 'None'}
Allergies: {', '.join(allergies) if allergies else 'None'}

Respond ONLY in JSON:
{{
  "meals": [
    {{
      "meal_type": "breakfast",
      "name": "Oats Upma with Vegetables",
      "ingredients": ["rolled oats", "mixed vegetables", "peanuts"],
      "portion_grams": 300,
      "calories": 380,
      "protein_g": 14,
      "carbs_g": 52,
      "fat_g": 12,
      "instructions": "Brief cooking method"
    }}
  ],
  "total_calories": {targets.target_calories},
  "total_protein_g": {targets.protein_g},
  "total_carbs_g": {targets.carbs_g},
  "total_fat_g": {targets.fat_g},
  "notes": "..."
}}"""


async def generate_meal_plan(
    user_context: dict[str, Any],
    targets: MacroTargets,
    meal_count: int = 4,
) -> dict[str, Any]:
    """Generate a daily meal plan via Gemini."""
    prompt = _build_plan_prompt(targets, meal_count, user_context)

    result = await gemini_client.generate_json(
        prompt=prompt,
        system_instruction=MEAL_PLAN_SYSTEM,
        temperature=0.5,
    )

    # Attach metadata
    result["date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result["user_id"] = user_context.get("firebase_uid", "")
    result["meal_count"] = meal_count

    return result


async def save_meal_plan(user_id: str, plan: dict[str, Any]) -> str:
    """Upsert today's meal plan into MongoDB."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    result = await meal_plans_collection().update_one(
        {"user_id": user_id, "date": today},
        {"$set": {**plan, "user_id": user_id, "date": today, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )

    plan_id = str(result.upserted_id) if result.upserted_id else today
    logger.info("Meal plan saved for user %s on %s", user_id, today)
    return plan_id


async def get_todays_meal_plan(user_id: str) -> dict[str, Any] | None:
    """Retrieve today's cached meal plan."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    plan = await meal_plans_collection().find_one(
        {"user_id": user_id, "date": today},
        {"_id": 0},
    )
    return plan


async def adjust_meal_plan(
    current_plan: dict[str, Any],
    feedback: str,
    targets: MacroTargets,
) -> dict[str, Any]:
    """Adjust an existing meal plan based on user feedback."""
    prompt = f"""Here is the user's current meal plan:
{current_plan}

The user's daily targets are:
- Calories: {targets.target_calories}, Protein: {targets.protein_g}g, Carbs: {targets.carbs_g}g, Fat: {targets.fat_g}g

User feedback: "{feedback}"

Adjust the plan based on the feedback while staying close to the macro targets.
Output the FULL updated meal plan in the same JSON format. Return ONLY valid JSON."""

    result = await gemini_client.generate_json(
        prompt=prompt,
        system_instruction=MEAL_PLAN_SYSTEM,
        temperature=0.4,
    )

    result["date"] = current_plan.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    result["user_id"] = current_plan.get("user_id", "")
    result["adjusted_from_feedback"] = feedback

    return result
