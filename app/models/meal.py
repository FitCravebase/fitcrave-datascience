"""
Meal Model

Schema for meal logs, meal plans, and MealSnap results.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MealItem(BaseModel):
    """A single food item within a meal."""

    name: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    portion_grams: float
    source: Literal["manual", "mealsnap", "order", "plan"] = "manual"


class MealLog(BaseModel):
    """A logged meal."""

    user_id: str
    date: datetime
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    items: list[MealItem]

    # Totals (computed)
    total_calories: int = 0
    total_protein_g: float = 0.0
    total_carbs_g: float = 0.0
    total_fat_g: float = 0.0

    # MealSnap metadata
    image_url: str | None = None
    ai_confidence: float | None = None
    user_corrected: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)

    def compute_totals(self) -> None:
        """Recalculate totals from items."""
        self.total_calories = sum(item.calories for item in self.items)
        self.total_protein_g = sum(item.protein_g for item in self.items)
        self.total_carbs_g = sum(item.carbs_g for item in self.items)
        self.total_fat_g = sum(item.fat_g for item in self.items)


class DailyMealPlan(BaseModel):
    """An AI-generated daily meal plan."""

    user_id: str
    date: datetime
    meals: list[dict]  # Structured meal plan from Gemini
    daily_totals: dict = Field(default_factory=dict)
    coaching_note: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
