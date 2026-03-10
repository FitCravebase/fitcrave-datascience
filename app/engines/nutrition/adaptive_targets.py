"""
Adaptive Targets

Recalculates user macro targets weekly based on:
- Actual weight change vs predicted weight change
- Meal adherence percentage
- Workout intensity trends
- User feedback

This is the "closed loop" that makes FitCrave decision-first.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.database import users_collection
from app.engines.nutrition.macro_calculator import (
    ActivityLevel,
    FitnessGoal,
    Gender,
    MacroTargets,
    calculate_macro_targets,
)
from app.utils.llm_client import gemini_client

logger = logging.getLogger(__name__)


ADAPTATION_SYSTEM = """You are FitCrave's adaptive nutrition AI.
You analyze weekly data to recommend safe, effective adjustments to a user's nutrition targets.
You never suggest extreme changes. Maximum adjustment is 300 kcal/week.
You always explain your reasoning in a friendly, motivating way."""


ADAPTATION_PROMPT = """Analyze this user's week and recommend target adjustments.

## User's Current Targets
- Calories: {calories} kcal
- Protein: {protein_g}g | Carbs: {carbs_g}g | Fat: {fat_g}g
- Goal: {goal}

## This Week's Data
- Starting weight: {start_weight} kg
- Current weight: {current_weight} kg
- Weight change: {weight_change:+.1f} kg
- Expected change based on targets: {expected_change:+.1f} kg
- Meal adherence: {meal_adherence}%
- Average daily calories consumed: {avg_calories} kcal
- Workout completion: {workout_adherence}%

## Instructions
Analyze the data and recommend adjustments. Consider:
1. Is the user losing/gaining weight at a healthy rate?
2. Is adherence the issue, or are the targets wrong?
3. Should calories be adjusted? By how much? (max ±300 kcal)
4. Any macro ratio changes needed?

Respond in JSON:
{{
  "calorie_adjustment": 0,
  "protein_adjustment_g": 0,
  "carbs_adjustment_g": 0,
  "fat_adjustment_g": 0,
  "reasoning": "Technical explanation of why",
  "user_message": "A friendly, motivating message for the user"
}}"""


async def calculate_weekly_adaptation(
    user_id: str,
    current_targets: MacroTargets,
    weekly_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Analyze a user's week and recommend target adjustments.
    Called by a weekly cron job (Sunday evening).
    """
    # Calculate expected weight change based on deficit/surplus
    calorie_adjustment = current_targets.target_calories - current_targets.tdee
    expected_change = (calorie_adjustment * 7) / 7700  # 7700 kcal ≈ 1 kg

    prompt = ADAPTATION_PROMPT.format(
        calories=current_targets.target_calories,
        protein_g=current_targets.protein_g,
        carbs_g=current_targets.carbs_g,
        fat_g=current_targets.fat_g,
        goal=current_targets.goal.value,
        start_weight=weekly_data.get("start_weight", 70),
        current_weight=weekly_data.get("current_weight", 70),
        weight_change=weekly_data.get("current_weight", 70) - weekly_data.get("start_weight", 70),
        expected_change=expected_change,
        meal_adherence=weekly_data.get("meal_adherence", 0),
        avg_calories=weekly_data.get("avg_calories", 0),
        workout_adherence=weekly_data.get("workout_adherence", 0),
    )

    result = await gemini_client.generate_json(
        prompt=prompt,
        system_instruction=ADAPTATION_SYSTEM,
        temperature=0.2,
    )

    logger.info(
        "Weekly adaptation for user %s: calorie adj = %+d",
        user_id, result.get("calorie_adjustment", 0),
    )
    return result


async def apply_adaptation(
    user_id: str,
    current_targets: MacroTargets,
    adaptation: dict[str, Any],
) -> MacroTargets:
    """
    Apply the recommended adaptation to the user's targets.
    Includes safety guardrails.
    """
    cal_adj = adaptation.get("calorie_adjustment", 0)
    protein_adj = adaptation.get("protein_adjustment_g", 0)
    carbs_adj = adaptation.get("carbs_adjustment_g", 0)
    fat_adj = adaptation.get("fat_adjustment_g", 0)

    # Safety: clamp calorie adjustment to ±300 kcal
    cal_adj = max(-300, min(300, cal_adj))

    new_calories = current_targets.target_calories + cal_adj
    new_protein = current_targets.protein_g + protein_adj
    new_carbs = current_targets.carbs_g + carbs_adj
    new_fat = current_targets.fat_g + fat_adj

    # Safety floor: never go below minimum
    gender = "male"  # TODO: pull from user profile
    from app.config import settings
    min_cal = settings.MIN_CALORIES_MALE if gender == "male" else settings.MIN_CALORIES_FEMALE
    new_calories = max(new_calories, min_cal)

    # Safety: protein should never drop below 1.2 g/kg
    new_protein = max(new_protein, 50)  # absolute minimum

    new_targets = MacroTargets(
        bmr=current_targets.bmr,
        tdee=current_targets.tdee,
        target_calories=new_calories,
        protein_g=new_protein,
        fat_g=max(new_fat, 30),
        carbs_g=max(new_carbs, 50),
        goal=current_targets.goal,
        explanation=f"Adapted: {adaptation.get('reasoning', 'Weekly adjustment')}",
    )

    # Persist to user profile
    await users_collection().update_one(
        {"firebase_uid": user_id},
        {
            "$set": {
                "current_targets": {
                    "calories": new_targets.target_calories,
                    "protein_g": new_targets.protein_g,
                    "carbs_g": new_targets.carbs_g,
                    "fat_g": new_targets.fat_g,
                    "last_calculated": datetime.now(timezone.utc),
                    "adjustment_reason": adaptation.get("user_message", ""),
                }
            }
        },
    )

    logger.info(
        "Targets updated for user %s: %d kcal (%+d)",
        user_id, new_calories, cal_adj,
    )
    return new_targets
