"""
MealSnap — Image to Macros

Uses Gemini Vision to analyze food images and estimate macros.
Includes confidence scoring and user correction flow.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from app.database import food_corrections_collection
from app.utils.llm_client import gemini_client

logger = logging.getLogger(__name__)


class MealSnapItem(BaseModel):
    """A single food item identified in an image."""

    name: str
    estimated_portion_grams: int
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    confidence: float  # 0.0 to 1.0


class MealSnapResult(BaseModel):
    """Complete MealSnap analysis result."""

    items: list[MealSnapItem]
    total_calories: int
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    needs_user_review: bool  # True if any item confidence < 0.7
    notes: str


MEALSNAP_PROMPT = """Analyze this image of an Indian meal. Identify each food item,
estimate the portion size, and calculate the macronutrients.

Be specific about Indian dishes — identify the exact dish (e.g., "Paneer Butter Masala"
rather than just "curry"). Estimate portions based on the plate/bowl size visible.

Return ONLY valid JSON in this exact format:
{{
  "items": [
    {{
      "name": "Dal Tadka",
      "estimated_portion_grams": 200,
      "calories": 180,
      "protein_g": 9.0,
      "carbs_g": 22.0,
      "fat_g": 6.0,
      "confidence": 0.85
    }}
  ],
  "total_calories": 180,
  "total_protein_g": 9.0,
  "total_carbs_g": 22.0,
  "total_fat_g": 6.0,
  "notes": "Portion estimate based on standard serving bowl"
}}

Be conservative with portion estimates. It's better to slightly underestimate
than to overestimate calories."""


async def analyze_food_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> MealSnapResult:
    """
    Analyze a food image using Gemini Vision and return structured macro data.

    Args:
        image_bytes: Raw image bytes from the user's camera.
        mime_type: MIME type of the image.

    Returns:
        MealSnapResult with item breakdown and confidence scores.
    """
    raw = await gemini_client.analyze_image(
        image_bytes=image_bytes,
        prompt=MEALSNAP_PROMPT,
        mime_type=mime_type,
    )

    items = [MealSnapItem(**item) for item in raw.get("items", [])]
    needs_review = any(item.confidence < 0.7 for item in items)

    result = MealSnapResult(
        items=items,
        total_calories=raw.get("total_calories", sum(i.calories for i in items)),
        total_protein_g=raw.get("total_protein_g", sum(i.protein_g for i in items)),
        total_carbs_g=raw.get("total_carbs_g", sum(i.carbs_g for i in items)),
        total_fat_g=raw.get("total_fat_g", sum(i.fat_g for i in items)),
        needs_user_review=needs_review,
        notes=raw.get("notes", ""),
    )

    logger.info(
        "MealSnap: identified %d items, total %d kcal, review needed: %s",
        len(items), result.total_calories, needs_review,
    )
    return result


async def apply_user_correction(
    original_result: MealSnapResult,
    corrections: dict[str, Any],
    user_id: str,
) -> MealSnapResult:
    """
    Apply user corrections to a MealSnap result.
    Stores the original vs corrected data for future prompt improvement.
    """
    # Store correction for future learning
    correction_doc = {
        "user_id": user_id,
        "original": original_result.model_dump(),
        "corrections": corrections,
        "created_at": datetime.now(timezone.utc),
    }
    await food_corrections_collection().insert_one(correction_doc)
    logger.info("Stored MealSnap correction from user %s", user_id)

    # Apply corrections to create updated result
    corrected_items = []
    for item_data in corrections.get("items", original_result.model_dump()["items"]):
        corrected_items.append(MealSnapItem(**item_data))

    corrected = MealSnapResult(
        items=corrected_items,
        total_calories=sum(i.calories for i in corrected_items),
        total_protein_g=sum(i.protein_g for i in corrected_items),
        total_carbs_g=sum(i.carbs_g for i in corrected_items),
        total_fat_g=sum(i.fat_g for i in corrected_items),
        needs_user_review=False,
        notes="User-corrected result",
    )
    return corrected
