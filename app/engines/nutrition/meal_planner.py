"""
Meal Planner

Uses Gemini to generate personalized meal plans based on the user's
macro targets, dietary restrictions, cultural preferences, and feedback history.
"""

from __future__ import annotations

from typing import Any

from app.engines.nutrition.macro_calculator import MacroTargets


MEAL_PLAN_PROMPT = """You are FitCrave's nutrition AI. Generate a detailed daily meal plan.

## User Profile
{user_context}

## Today's Macro Targets
- Calories: {calories} kcal
- Protein: {protein}g
- Carbs: {carbs}g
- Fat: {fat}g

## Dietary Restrictions
{restrictions}

## Cultural Preferences
{cultural_preferences}

## User Feedback (foods they liked/disliked)
{feedback}

## Instructions
1. Generate {meal_count} meals + snacks that HIT the macro targets (within 5% tolerance)
2. Prioritize Indian foods matching the user's cultural preferences
3. Include portion sizes in grams
4. Each meal should list: name, ingredients, portion, calories, protein, carbs, fat
5. Briefly explain WHY you chose each meal (the "decision-first" approach)

Respond in JSON format:
{{
  "meals": [
    {{
      "meal_type": "breakfast",
      "name": "...",
      "ingredients": ["..."],
      "portion_grams": 300,
      "calories": 450,
      "protein_g": 25,
      "carbs_g": 50,
      "fat_g": 12,
      "reasoning": "High protein start to support muscle recovery from yesterday's workout"
    }}
  ],
  "daily_totals": {{ "calories": ..., "protein_g": ..., "carbs_g": ..., "fat_g": ... }},
  "coaching_note": "Brief note about today's plan and how it fits their goals"
}}"""


async def generate_meal_plan(
    user_context: dict[str, Any],
    targets: MacroTargets,
    meal_count: int = 4,
) -> dict[str, Any]:
    """
    Generate a personalized daily meal plan using Gemini.

    Args:
        user_context: Full user context from context_manager.
        targets: Calculated macro targets for the day.
        meal_count: Number of main meals (default 4).

    Returns:
        Structured meal plan dict.

    TODO: Implement Gemini API call with MEAL_PLAN_PROMPT.
    """
    pass


async def adjust_meal_plan(
    current_plan: dict[str, Any],
    user_feedback: str,
    targets: MacroTargets,
) -> dict[str, Any]:
    """
    Adjust an existing meal plan based on user feedback.

    Example: "I don't feel like eating rice today" →
    AI swaps rice-based meals while maintaining macro targets.

    TODO: Implement with Gemini.
    """
    pass
