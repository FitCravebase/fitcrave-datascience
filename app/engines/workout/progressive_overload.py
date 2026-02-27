"""
Progressive Overload Engine (Rule-Based)

Tracks workout performance over time and determines when to
increase weight, reps, or volume. No LLM needed — pure logic.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ProgressionRecommendation(BaseModel):
    """A recommendation to progress on an exercise."""

    exercise_id: str
    exercise_name: str
    current_weight: float
    recommended_weight: float
    current_reps: str
    recommended_reps: str
    reasoning: str


# ------------------------------------------------------------------
# Progression Rules
# ------------------------------------------------------------------
# Rule: If user hit all target reps at target RPE for 2 consecutive
# sessions → increase weight by the smallest meaningful increment.

WEIGHT_INCREMENTS = {
    "barbell": 2.5,    # 2.5 kg (1.25 kg plates each side)
    "dumbbell": 2.0,   # 2 kg jump
    "cable": 2.5,      # One pin
    "machine": 5.0,    # One plate
    "bodyweight": 0,   # Progress via reps, not weight
}


def check_progression(
    exercise_id: str,
    exercise_name: str,
    equipment_type: str,
    target_reps: int,
    target_rpe: float,
    recent_sessions: list[dict[str, Any]],
    consecutive_sessions_required: int = 2,
) -> ProgressionRecommendation | None:
    """
    Check if a user should progress on an exercise.

    Args:
        exercise_id: The exercise identifier.
        exercise_name: Human-readable name.
        equipment_type: Type of equipment (for weight increment lookup).
        target_reps: The target reps per set.
        target_rpe: The target RPE per set.
        recent_sessions: Last N sessions of this exercise,
                         each containing: {"sets": [{"reps": int, "weight": float, "rpe": float}]}.
        consecutive_sessions_required: How many sessions must hit target before progression.

    Returns:
        ProgressionRecommendation if progression is warranted, None otherwise.
    """
    if len(recent_sessions) < consecutive_sessions_required:
        return None

    # Check the last N sessions
    sessions_to_check = recent_sessions[-consecutive_sessions_required:]

    all_hit = True
    current_weight = 0.0

    for session in sessions_to_check:
        sets = session.get("sets", [])
        if not sets:
            all_hit = False
            break

        current_weight = sets[0].get("weight", 0)

        for s in sets:
            # Did they hit target reps?
            if s.get("reps", 0) < target_reps:
                all_hit = False
                break
            # Was RPE at or below target? (lower RPE = easier = ready to progress)
            if s.get("rpe", 10) > target_rpe + 0.5:  # 0.5 tolerance
                all_hit = False
                break

        if not all_hit:
            break

    if not all_hit:
        return None

    # Calculate progression
    increment = WEIGHT_INCREMENTS.get(equipment_type, 2.5)

    if equipment_type == "bodyweight":
        # Progress via reps for bodyweight exercises
        return ProgressionRecommendation(
            exercise_id=exercise_id,
            exercise_name=exercise_name,
            current_weight=0,
            recommended_weight=0,
            current_reps=str(target_reps),
            recommended_reps=str(target_reps + 2),
            reasoning=(
                f"Hit {target_reps} reps at RPE ≤{target_rpe} for "
                f"{consecutive_sessions_required} sessions. Adding 2 reps."
            ),
        )

    return ProgressionRecommendation(
        exercise_id=exercise_id,
        exercise_name=exercise_name,
        current_weight=current_weight,
        recommended_weight=current_weight + increment,
        current_reps=str(target_reps),
        recommended_reps=str(target_reps),
        reasoning=(
            f"Hit {target_reps} reps × {current_weight}kg at RPE ≤{target_rpe} for "
            f"{consecutive_sessions_required} sessions. "
            f"Increasing by {increment}kg to {current_weight + increment}kg."
        ),
    )
