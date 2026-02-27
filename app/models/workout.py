"""
Workout Model

Schema for workout plans, workout logs, and exercise records.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WorkoutPlanExercise(BaseModel):
    """An exercise within a workout plan."""

    exercise_id: str
    name: str
    target_sets: int
    target_reps: str          # e.g., "8-10"
    target_rpe: float
    rest_seconds: int = 90
    notes: str = ""


class WorkoutPlanDay(BaseModel):
    """A single day in a workout plan."""

    day_number: int
    day_name: str             # e.g., "Push Day"
    focus: list[str]          # e.g., ["chest", "shoulders", "triceps"]
    exercises: list[WorkoutPlanExercise]
    warmup: str = ""
    cooldown: str = ""
    cardio: dict | None = None


class WorkoutPlan(BaseModel):
    """A complete workout plan."""

    user_id: str
    split_type: str           # e.g., "push_pull_legs"
    days: list[WorkoutPlanDay]
    active: bool = True
    weekly_notes: str = ""
    deload_strategy: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
