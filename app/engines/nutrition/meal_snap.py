"""
MealSnap — Image to Macros

Uses Gemini Vision to analyze food images and estimate macros.
Includes confidence scoring and user correction flow.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


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


async def analyze_food_image(image_bytes: bytes) -> MealSnapResult:
    """
    Analyze a food image using Gemini Vision and return structured macro data.

    Args:
        image_bytes: Raw image bytes from the user's camera.

    Returns:
        MealSnapResult with item breakdown and confidence scores.

    TODO: Implement Gemini Vision API call.
          1. Send image + MEALSNAP_PROMPT to Gemini
          2. Parse JSON response into MealSnapResult
          3. Set needs_user_review = True if any confidence < 0.7
    """
    pass


async def apply_user_correction(
    original_result: MealSnapResult,
    corrections: dict[str, Any],
    user_id: str,
) -> MealSnapResult:
    """
    Apply user corrections to a MealSnap result.

    Stores the original vs corrected data for future prompt improvement.

    Args:
        original_result: The AI's initial analysis.
        corrections: User's corrections (e.g., {"items": [{"name": "Chole", ...}]}).
        user_id: For storing correction history.

    Returns:
        Updated MealSnapResult with user corrections applied.

    TODO: Implement correction application and storage.
    """
    pass
