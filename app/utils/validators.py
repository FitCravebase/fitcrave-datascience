"""
Response Validators

Validates LLM responses to ensure they meet safety and quality standards.
Catches hallucinations, unsafe recommendations, and schema violations.
"""

from __future__ import annotations

from app.config import settings


def validate_calorie_target(calories: int, gender: str) -> tuple[bool, str]:
    """
    Validate that a calorie target is within safe bounds.

    Returns:
        (is_valid, error_message)
    """
    min_cal = settings.MIN_CALORIES_MALE if gender == "male" else settings.MIN_CALORIES_FEMALE

    if calories < min_cal:
        return False, f"Calorie target {calories} is below minimum safe threshold ({min_cal})"
    if calories > 5000:
        return False, f"Calorie target {calories} seems unreasonably high"
    return True, ""


def validate_exercise_exists(exercise_id: str, valid_exercises: set[str]) -> bool:
    """Ensure an AI-suggested exercise exists in our database (prevents hallucination)."""
    return exercise_id in valid_exercises


def validate_macro_totals(
    protein_g: float, carbs_g: float, fat_g: float, target_calories: int, tolerance: float = 0.10
) -> tuple[bool, str]:
    """
    Validate that macro breakdown matches target calories within tolerance.

    Protein: 4 cal/g, Carbs: 4 cal/g, Fat: 9 cal/g
    """
    computed_calories = (protein_g * 4) + (carbs_g * 4) + (fat_g * 9)
    diff_pct = abs(computed_calories - target_calories) / target_calories

    if diff_pct > tolerance:
        return False, (
            f"Macro breakdown ({computed_calories:.0f} cal) doesn't match "
            f"target ({target_calories} cal) — {diff_pct:.0%} off"
        )
    return True, ""


def validate_weight_progression(
    current_weight: float, recommended_weight: float, max_jump_pct: float = 0.10
) -> tuple[bool, str]:
    """
    Validate that a weight progression recommendation is reasonable.

    Max 10% jump to prevent injury.
    """
    if current_weight == 0:
        return True, ""

    jump_pct = (recommended_weight - current_weight) / current_weight
    if jump_pct > max_jump_pct:
        return False, (
            f"Weight jump from {current_weight}kg to {recommended_weight}kg "
            f"is {jump_pct:.0%} — exceeds {max_jump_pct:.0%} safety limit"
        )
    return True, ""
