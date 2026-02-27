"""
Workout Tracker

Handles logging workout sessions with full detail:
- Sets × reps × weight for strength exercises
- Duration × distance × pace for cardio
- RPE per set
- Rest times
- Session notes
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class StrengthSet(BaseModel):
    """A single set of a strength exercise."""

    set_number: int
    reps: int
    weight_kg: float
    rpe: float | None = None      # Rate of Perceived Exertion (1-10)
    rest_seconds: int | None = None
    completed: bool = True
    notes: str = ""


class CardioSession(BaseModel):
    """A cardio exercise session."""

    duration_minutes: float
    distance_km: float | None = None
    avg_pace_min_per_km: float | None = None
    avg_heart_rate: int | None = None
    notes: str = ""


class ExerciseLog(BaseModel):
    """A logged exercise within a workout session."""

    exercise_id: str
    exercise_name: str
    exercise_type: str  # "strength" or "cardio"
    sets: list[StrengthSet] | None = None    # For strength exercises
    cardio: CardioSession | None = None      # For cardio exercises
    notes: str = ""


class WorkoutSession(BaseModel):
    """A complete workout session."""

    user_id: str
    date: datetime
    plan_id: str | None = None  # Reference to the workout plan
    day_name: str = ""          # e.g., "Push Day"
    exercises: list[ExerciseLog]
    overall_rpe: float | None = None
    duration_minutes: int | None = None
    notes: str = ""


async def log_workout(session: WorkoutSession) -> dict[str, Any]:
    """
    Log a complete workout session to the database.

    Also triggers:
    1. Progressive overload check for each exercise
    2. Coaching engine notification if workout was skipped/modified
    3. Updates readiness score factors

    Args:
        session: The complete workout session data.

    Returns:
        Confirmation with any progression recommendations.

    TODO: Implement MongoDB insert + trigger progressive overload checks.
    """
    pass


async def get_exercise_history(
    user_id: str,
    exercise_id: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Get recent history for a specific exercise.

    Used by progressive overload engine to determine progression.

    TODO: Implement MongoDB query.
    """
    return []
