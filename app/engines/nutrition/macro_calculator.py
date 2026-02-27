"""
Macro Calculator (Rule-Based)

Implements Mifflin-St Jeor BMR calculation, TDEE estimation,
and goal-based macro splitting. No LLM needed — pure math.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"             # Desk job, no exercise
    LIGHTLY_ACTIVE = "lightly_active"   # 1-3 days/week
    MODERATELY_ACTIVE = "moderately_active"  # 3-5 days/week
    VERY_ACTIVE = "very_active"         # 6-7 days/week
    EXTREMELY_ACTIVE = "extremely_active"    # Athlete / physical job


class FitnessGoal(str, Enum):
    FAT_LOSS = "fat_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"
    RECOMPOSITION = "recomposition"


ACTIVITY_MULTIPLIERS = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHTLY_ACTIVE: 1.375,
    ActivityLevel.MODERATELY_ACTIVE: 1.55,
    ActivityLevel.VERY_ACTIVE: 1.725,
    ActivityLevel.EXTREMELY_ACTIVE: 1.9,
}

# Grams per kg of bodyweight
MACRO_RATIOS = {
    FitnessGoal.FAT_LOSS: {"protein_g_per_kg": 2.0, "fat_g_per_kg": 0.8, "calorie_adjustment": -500},
    FitnessGoal.MUSCLE_GAIN: {"protein_g_per_kg": 1.8, "fat_g_per_kg": 1.0, "calorie_adjustment": 300},
    FitnessGoal.MAINTENANCE: {"protein_g_per_kg": 1.6, "fat_g_per_kg": 1.0, "calorie_adjustment": 0},
    FitnessGoal.RECOMPOSITION: {"protein_g_per_kg": 2.2, "fat_g_per_kg": 0.9, "calorie_adjustment": -200},
}


class MacroTargets(BaseModel):
    """Calculated daily macro targets."""

    bmr: float
    tdee: float
    target_calories: int
    protein_g: int
    fat_g: int
    carbs_g: int
    goal: FitnessGoal
    explanation: str


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: Gender) -> float:
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.

    Male:   BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) + 5
    Female: BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) - 161
    """
    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    if gender == Gender.MALE:
        bmr += 5
    else:
        bmr -= 161
    return round(bmr, 1)


def calculate_tdee(bmr: float, activity_level: ActivityLevel) -> float:
    """Calculate Total Daily Energy Expenditure."""
    return round(bmr * ACTIVITY_MULTIPLIERS[activity_level], 1)


def calculate_macro_targets(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: Gender,
    activity_level: ActivityLevel,
    goal: FitnessGoal,
) -> MacroTargets:
    """
    Calculate complete daily macro targets.

    Returns calories, protein, fat, and carbs based on:
    - Mifflin-St Jeor BMR
    - Activity-adjusted TDEE
    - Goal-based caloric adjustment and macro ratios
    """
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = calculate_tdee(bmr, activity_level)

    ratios = MACRO_RATIOS[goal]
    target_calories = int(tdee + ratios["calorie_adjustment"])

    # Safety floor
    min_cal = 1500 if gender == Gender.MALE else 1200
    target_calories = max(target_calories, min_cal)

    # Calculate macros
    protein_g = int(ratios["protein_g_per_kg"] * weight_kg)
    fat_g = int(ratios["fat_g_per_kg"] * weight_kg)

    # Remaining calories go to carbs (protein=4cal/g, fat=9cal/g, carbs=4cal/g)
    protein_cals = protein_g * 4
    fat_cals = fat_g * 9
    remaining_cals = max(target_calories - protein_cals - fat_cals, 0)
    carbs_g = int(remaining_cals / 4)

    explanation = (
        f"BMR: {bmr} kcal (Mifflin-St Jeor) → "
        f"TDEE: {tdee} kcal ({activity_level.value}) → "
        f"Target: {target_calories} kcal ({goal.value}, "
        f"{ratios['calorie_adjustment']:+d} kcal adjustment)"
    )

    return MacroTargets(
        bmr=bmr,
        tdee=tdee,
        target_calories=target_calories,
        protein_g=protein_g,
        fat_g=fat_g,
        carbs_g=carbs_g,
        goal=goal,
        explanation=explanation,
    )
