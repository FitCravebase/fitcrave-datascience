"""
Macro Calculator

Pure-math module — no DB or LLM calls.
Computes BMR (Mifflin-St Jeor), TDEE, and goal-adjusted macros.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Gender(str, Enum):
    male = "male"
    female = "female"


class ActivityLevel(str, Enum):
    sedentary = "sedentary"
    lightly_active = "lightly_active"
    moderately_active = "moderately_active"
    very_active = "very_active"
    extremely_active = "extremely_active"


class FitnessGoal(str, Enum):
    fat_loss = "fat_loss"
    maintenance = "maintenance"
    muscle_gain = "muscle_gain"


# Multipliers
_ACTIVITY_MULTIPLIERS = {
    ActivityLevel.sedentary: 1.2,
    ActivityLevel.lightly_active: 1.375,
    ActivityLevel.moderately_active: 1.55,
    ActivityLevel.very_active: 1.725,
    ActivityLevel.extremely_active: 1.9,
}

_GOAL_ADJUSTMENTS = {
    FitnessGoal.fat_loss: -0.20,       # 20% deficit
    FitnessGoal.maintenance: 0.0,
    FitnessGoal.muscle_gain: 0.10,     # 10% surplus
}


class MacroTargets(BaseModel):
    bmr: float
    tdee: float
    target_calories: int
    protein_g: int
    carbs_g: int
    fat_g: int
    goal: FitnessGoal
    explanation: str


def calculate_macro_targets(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: Gender,
    activity_level: ActivityLevel = ActivityLevel.moderately_active,
    goal: FitnessGoal = FitnessGoal.fat_loss,
) -> MacroTargets:
    """Calculate daily macro targets using Mifflin-St Jeor."""

    # BMR (Mifflin-St Jeor)
    if gender == Gender.male:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    tdee = bmr * _ACTIVITY_MULTIPLIERS[activity_level]
    adjustment = _GOAL_ADJUSTMENTS[goal]
    target_calories = int(tdee * (1 + adjustment))

    # Macro split
    if goal == FitnessGoal.fat_loss:
        protein_g = int(weight_kg * 2.2)   # high protein for fat loss
        fat_g = int(weight_kg * 0.9)
    elif goal == FitnessGoal.muscle_gain:
        protein_g = int(weight_kg * 2.0)
        fat_g = int(weight_kg * 1.0)
    else:
        protein_g = int(weight_kg * 1.8)
        fat_g = int(weight_kg * 1.0)

    protein_cals = protein_g * 4
    fat_cals = fat_g * 9
    carbs_cals = max(target_calories - protein_cals - fat_cals, 0)
    carbs_g = int(carbs_cals / 4)

    explanation = (
        f"BMR={bmr:.0f} kcal, TDEE={tdee:.0f} kcal "
        f"({activity_level.value}). "
        f"Goal: {goal.value} → {adjustment:+.0%} "
        f"= {target_calories} kcal/day."
    )

    return MacroTargets(
        bmr=round(bmr, 1),
        tdee=round(tdee, 1),
        target_calories=target_calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        goal=goal,
        explanation=explanation,
    )
