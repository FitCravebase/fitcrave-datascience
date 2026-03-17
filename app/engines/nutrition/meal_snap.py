"""
MealSnap — Food Image Analysis

Uses Gemini Vision to identify food items from a photo
and estimate their macronutrient content.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

from app.database import food_corrections_collection
from app.utils.llm_client import gemini_client

logger = logging.getLogger(__name__)


class FoodItem(BaseModel):
    name: str
    quantity_grams: int
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    confidence: float = 0.8


class MealSnapResult(BaseModel):
    items: list[FoodItem]
    total_calories: int
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    description: str = ""


MEALSNAP_PROMPT = """You are a nutrition AI. Analyze this food image.

Identify EVERY food item visible. For each, estimate:
- name, quantity_grams, calories, protein_g, carbs_g, fat_g, confidence (0.0–1.0)

Use Indian food knowledge when applicable.

Respond ONLY in JSON:
{
  "items": [
    {
      "name": "Dal Tadka",
      "quantity_grams": 200,
      "calories": 210,
      "protein_g": 12.0,
      "carbs_g": 30.0,
      "fat_g": 5.0,
      "confidence": 0.85
    }
  ],
  "total_calories": 210,
  "total_protein_g": 12.0,
  "total_carbs_g": 30.0,
  "total_fat_g": 5.0,
  "description": "A bowl of dal tadka with rice"
}"""


async def analyze_food_image(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
) -> MealSnapResult:
    """Analyze a food photo and return structured nutritional data."""
    raw = await gemini_client.analyze_image(
        image_bytes=image_bytes,
        prompt=MEALSNAP_PROMPT,
        mime_type=mime_type,
    )

    try:
        result = MealSnapResult(**raw)
        logger.info(
            "MealSnap analyzed: %d items, %d kcal total",
            len(result.items), result.total_calories,
        )
        return result
    except Exception as e:
        logger.error("Failed to parse MealSnap result: %s — raw: %s", e, raw)
        raise ValueError("Could not analyze the food image. Please try again with a clearer photo.")


async def apply_user_correction(
    original: MealSnapResult,
    corrections: dict[str, Any],
    user_id: str,
) -> MealSnapResult:
    """Apply user corrections to a MealSnap result and store for learning."""
    # Save the correction for future model improvement
    await food_corrections_collection().insert_one({
        "user_id": user_id,
        "original": original.model_dump(),
        "corrections": corrections,
    })

    # Merge corrections into items
    corrected_items = []
    for item_data in original.model_dump()["items"]:
        item_name = item_data["name"].lower()
        if item_name in corrections:
            item_data.update(corrections[item_name])
        corrected_items.append(FoodItem(**item_data))

    # Recompute totals
    total_cals = sum(i.calories for i in corrected_items)
    total_prot = sum(i.protein_g for i in corrected_items)
    total_carb = sum(i.carbs_g for i in corrected_items)
    total_fat = sum(i.fat_g for i in corrected_items)

    return MealSnapResult(
        items=corrected_items,
        total_calories=total_cals,
        total_protein_g=round(total_prot, 1),
        total_carbs_g=round(total_carb, 1),
        total_fat_g=round(total_fat, 1),
        description=original.description,
    )
