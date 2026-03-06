"""
Meal Planner

Uses Gemini to generate personalized meal plans based on the user's
macro targets, dietary restrictions, cultural preferences, and feedback history.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.database import meal_plans_collection
from app.engines.nutrition.macro_calculator import MacroTargets
from app.utils.llm_client import gemini_client

logger = logging.getLogger(__name__)


MEAL_PLAN_SYSTEM_INSTRUCTION = """You are FitCrave's nutrition AI — an expert Indian dietitian.
You create detailed, practical daily meal plans that prioritize Indian cuisine.
Your plans always hit macro targets within 5% tolerance.
Every recommendation includes a brief "why" — the decision-first approach.
You never suggest extreme diets and always maintain nutritional balance."""


MEAL_PLAN_PROMPT = """Generate a detailed daily meal plan for today.

## User Profile
- Name: {name}
- Age: {age}, Gender: {gender}
- Weight: {weight_kg} kg, Height: {height_cm} cm
- Goal: {goal}
- Activity Level: {activity_level}
- Experience: {experience_level}

## Today's Macro Targets
- Calories: {calories} kcal
- Protein: {protein_g}g
- Carbs: {carbs_g}g
- Fat: {fat_g}g

## Dietary Restrictions
{restrictions}

## Allergies
{allergies}

## Preferences
- Meals per day: {meal_count}
- Disliked foods: {disliked_foods}

## Instructions
1. Generate exactly {meal_count} meals that HIT the macro targets (within 5% tolerance)
2. Prioritize common, practical Indian foods
3. Include portion sizes in grams
4. Each meal must list: meal_type, name, ingredients, portion_grams, calories, protein_g, carbs_g, fat_g
5. Briefly explain WHY you chose each meal (the "decision-first" approach)
6. Include a coaching_note about today's plan

Respond in JSON format:
{{
  "meals": [
    {{
      "meal_type": "breakfast",
      "name": "Paneer Paratha with Curd",
      "ingredients": ["whole wheat flour", "paneer", "spices", "curd"],
      "portion_grams": 300,
      "calories": 450,
      "protein_g": 22,
      "carbs_g": 45,
      "fat_g": 18,
      "prep_time_minutes": 20,
      "reasoning": "High protein start to support muscle recovery"
    }}
  ],
  "daily_totals": {{ "calories": 2200, "protein_g": 160, "carbs_g": 220, "fat_g": 73 }},
  "coaching_note": "Today's plan focuses on...",
  "tips": ["Drink at least 3L of water today"]
}}"""


ADJUST_MEAL_PROMPT = """The user wants to adjust their meal plan.

## Current Plan
{current_plan}

## User's Feedback
"{user_feedback}"

## Macro Targets (must still be hit)
- Calories: {calories} kcal
- Protein: {protein_g}g | Carbs: {carbs_g}g | Fat: {fat_g}g

## Instructions
Modify the plan based on the feedback while maintaining the same macro targets.
Only change the meals that need adjustment — keep the rest as-is.
Explain what you changed and why.

Respond in the same JSON format as the original plan."""


async def generate_meal_plan(
    user_context: dict[str, Any],
    targets: MacroTargets,
    meal_count: int = 4,
) -> dict[str, Any]:
    """Generate a personalized daily meal plan using Gemini."""

    prompt = MEAL_PLAN_PROMPT.format(
        name=user_context.get("name", "User"),
        age=user_context.get("age", 25),
        gender=user_context.get("gender", "male"),
        weight_kg=user_context.get("weight_kg", 70),
        height_cm=user_context.get("height_cm", 170),
        goal=targets.goal.value,
        activity_level=user_context.get("activity_level", "moderately_active"),
        experience_level=user_context.get("experience_level", "beginner"),
        calories=targets.target_calories,
        protein_g=targets.protein_g,
        carbs_g=targets.carbs_g,
        fat_g=targets.fat_g,
        restrictions=", ".join(user_context.get("dietary_restrictions", [])) or "None",
        allergies=", ".join(user_context.get("allergies", [])) or "None",
        meal_count=meal_count,
        disliked_foods=", ".join(user_context.get("disliked_foods", [])) or "None",
    )

    result = await gemini_client.generate_json(
        prompt=prompt,
        system_instruction=MEAL_PLAN_SYSTEM_INSTRUCTION,
        temperature=0.4,
    )

    logger.info("Meal plan generated for user '%s' — %d meals", user_context.get("name"), len(result.get("meals", [])))
    return result


async def adjust_meal_plan(
    current_plan: dict[str, Any],
    user_feedback: str,
    targets: MacroTargets,
) -> dict[str, Any]:
    """
    Adjust an existing meal plan based on user feedback.
    Example: "I don't feel like eating rice today" →
    AI swaps rice-based meals while maintaining macro targets.
    """
    import json

    prompt = ADJUST_MEAL_PROMPT.format(
        current_plan=json.dumps(current_plan, indent=2),
        user_feedback=user_feedback,
        calories=targets.target_calories,
        protein_g=targets.protein_g,
        carbs_g=targets.carbs_g,
        fat_g=targets.fat_g,
    )

    result = await gemini_client.generate_json(
        prompt=prompt,
        system_instruction=MEAL_PLAN_SYSTEM_INSTRUCTION,
        temperature=0.3,
    )

    logger.info("Meal plan adjusted based on feedback: '%s'", user_feedback[:50])
    return result


async def save_meal_plan(user_id: str, plan: dict[str, Any]) -> str:
    """Persist a meal plan to MongoDB. Returns the inserted document ID."""
    doc = {
        "user_id": user_id,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "meals": plan.get("meals", []),
        "daily_totals": plan.get("daily_totals", {}),
        "coaching_note": plan.get("coaching_note", ""),
        "tips": plan.get("tips", []),
        "created_at": datetime.now(timezone.utc),
    }
    result = await meal_plans_collection().insert_one(doc)
    logger.info("Meal plan saved for user %s — id: %s", user_id, result.inserted_id)
    return str(result.inserted_id)


async def get_todays_meal_plan(user_id: str) -> dict[str, Any] | None:
    """Fetch today's meal plan from the DB. Returns None if not found."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    doc = await meal_plans_collection().find_one(
        {"user_id": user_id, "date": today},
        sort=[("created_at", -1)],
    )
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc
