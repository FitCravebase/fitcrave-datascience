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

from typing import Any

from app.engines.nutrition.macro_calculator import (
    FitnessGoal,
    MacroTargets,
    calculate_macro_targets,
)


ADAPTATION_PROMPT = """You are FitCrave's adaptive nutrition AI.

## User's Current Targets
{current_targets}

## This Week's Data
- Starting weight: {start_weight} kg
- Current weight: {current_weight} kg
- Weight change: {weight_change:+.1f} kg
- Expected change based on targets: {expected_change:+.1f} kg
- Meal adherence: {meal_adherence}%
- Average daily calories consumed: {avg_calories} kcal
- Workout completion: {workout_adherence}%

## Goal: {goal}

## Instructions
Analyze the data and recommend adjustments. Consider:
1. Is the user losing/gaining weight at a healthy rate?
2. Is adherence the issue, or are the targets wrong?
3. Should calories be adjusted? By how much?
4. Any macro ratio changes needed?

Respond in JSON:
{{
  "calorie_adjustment": 0,  // positive = increase, negative = decrease
  "protein_adjustment_g": 0,
  "reasoning": "...",
  "user_message": "A friendly, motivating explanation for the user"
}}"""


async def calculate_weekly_adaptation(
    user_id: str,
    current_targets: MacroTargets,
    weekly_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Analyze a user's week and recommend target adjustments.

    Called by a weekly cron job (Sunday evening).

    Args:
        user_id: The user's ID.
        current_targets: Their current macro targets.
        weekly_data: Aggregated data for the past 7 days.

    Returns:
        Adjustment recommendations with reasoning.

    TODO: Implement Gemini API call with ADAPTATION_PROMPT.
    """
    pass


async def apply_adaptation(
    user_id: str,
    current_targets: MacroTargets,
    adaptation: dict[str, Any],
) -> MacroTargets:
    """
    Apply the recommended adaptation to the user's targets.

    Includes safety guardrails:
    - Never go below minimum calorie floor
    - Maximum 300 kcal adjustment per week
    - Alert if weight loss > 1 kg/week

    TODO: Implement with safety checks and database update.
    """
    pass
