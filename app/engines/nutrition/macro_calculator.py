"""
Macro calculator for the Smart Meal Plan (SMP) engine.

This module provides:
- Gender, ActivityLevel, FitnessGoal enums
- MacroTargets model
- calculate_macro_targets(...) helper

The goal is to produce sensible calorie + macro targets that are stable for
production use, not to be nutritionally perfect. Formulas are based on a
standard Mifflin‑St Jeor BMR + activity multiplier + goal adjustment.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Gender(str, Enum):
  male = "male"
  female = "female"


class ActivityLevel(str, Enum):
  sedentary = "sedentary"
  lightly_active = "lightly_active"
  moderately_active = "moderately_active"
  very_active = "very_active"


class FitnessGoal(str, Enum):
  fat_loss = "fat_loss"
  maintenance = "maintenance"
  muscle_gain = "muscle_gain"


class MacroTargets(BaseModel):
  """Calorie + macro targets for a single day."""

  bmr: float = Field(..., description="Basal Metabolic Rate (kcal)")
  tdee: float = Field(..., description="Total Daily Energy Expenditure (kcal)")
  target_calories: float = Field(..., description="Adjusted calories for the goal")
  protein_g: float
  carbs_g: float
  fat_g: float
  goal: FitnessGoal
  explanation: str


def _bmr_mifflin_st_jeor(
  weight_kg: float,
  height_cm: float,
  age: int,
  gender: Gender,
) -> float:
  if gender == Gender.male:
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
  return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161


def _activity_multiplier(level: ActivityLevel) -> float:
  return {
    ActivityLevel.sedentary: 1.2,
    ActivityLevel.lightly_active: 1.375,
    ActivityLevel.moderately_active: 1.55,
    ActivityLevel.very_active: 1.725,
  }[level]


def _goal_adjustment(goal: FitnessGoal) -> float:
  # Fraction of TDEE to target.
  return {
    FitnessGoal.fat_loss: 0.8,       # ~20% deficit
    FitnessGoal.maintenance: 1.0,
    FitnessGoal.muscle_gain: 1.1,    # ~10% surplus
  }[goal]


def calculate_macro_targets(
  *,
  weight_kg: float,
  height_cm: float,
  age: int,
  gender: Gender,
  activity_level: ActivityLevel,
  goal: FitnessGoal,
) -> MacroTargets:
  """Compute daily calorie + macro targets."""

  bmr = _bmr_mifflin_st_jeor(weight_kg, height_cm, age, gender)
  tdee = bmr * _activity_multiplier(activity_level)

  target_calories = tdee * _goal_adjustment(goal)

  # Protein: 1.8–2.0 g/kg for fat loss / muscle gain, 1.6 g/kg for maintenance.
  if goal in (FitnessGoal.fat_loss, FitnessGoal.muscle_gain):
    protein_g = weight_kg * 2.0
  else:
    protein_g = weight_kg * 1.6

  # Fat: ~25% of calories.
  fat_calories = target_calories * 0.25
  fat_g = fat_calories / 9.0

  # Carbs: remaining calories.
  remaining_calories = target_calories - (protein_g * 4.0 + fat_g * 9.0)
  carbs_g = max(0.0, remaining_calories / 4.0)

  explanation_parts: list[Literal[str] | str] = [
    "Targets based on Mifflin‑St Jeor BMR, activity multiplier, and goal adjustment.",
    f"Goal: {goal.value.replace('_', ' ')}.",
  ]

  explanation = " ".join(explanation_parts)

  return MacroTargets(
    bmr=round(bmr),
    tdee=round(tdee),
    target_calories=round(target_calories),
    protein_g=round(protein_g),
    carbs_g=round(carbs_g),
    fat_g=round(fat_g),
    goal=goal,
    explanation=explanation,
  )

