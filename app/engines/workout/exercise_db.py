"""
Exercise Database

Manages the seeded exercise database. Exercises are stored in
data/exercises.json and loaded into memory at startup.
Provides filtering by equipment, muscle group, and difficulty.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Exercise(BaseModel):
    """An exercise in the FitCrave database."""

    id: str
    name: str
    muscle_groups: list[str]  # e.g., ["chest", "triceps", "front_delts"]
    equipment: list[str]      # e.g., ["barbell", "bench"]
    difficulty: str           # "beginner", "intermediate", "advanced"
    type: str                 # "compound" or "isolation"
    category: str             # "strength", "cardio", "flexibility", "plyometric"
    instructions: str
    video_url: str | None = None


_exercise_cache: list[Exercise] = []


async def load_exercise_database() -> None:
    """
    Load exercise database from data/exercises.json into memory.

    Called once at application startup.

    TODO: Load and parse the JSON file.
    """
    global _exercise_cache
    # TODO: Load from app/engines/workout/data/exercises.json
    pass


def filter_exercises(
    equipment: list[str] | None = None,
    muscle_groups: list[str] | None = None,
    difficulty: str | None = None,
    category: str | None = None,
) -> list[Exercise]:
    """
    Filter exercises based on user's available equipment and target muscles.

    Args:
        equipment: User's available equipment. Only returns exercises
                   whose required equipment is a subset of this list.
        muscle_groups: Filter by target muscle groups.
        difficulty: Filter by difficulty level.
        category: Filter by category (strength, cardio, etc.).

    Returns:
        Filtered list of exercises.
    """
    results = _exercise_cache

    if equipment is not None:
        equipment_set = set(equipment) | {"bodyweight"}  # Always include bodyweight
        results = [
            e for e in results
            if set(e.equipment).issubset(equipment_set)
        ]

    if muscle_groups is not None:
        mg_set = set(muscle_groups)
        results = [
            e for e in results
            if mg_set.intersection(set(e.muscle_groups))
        ]

    if difficulty is not None:
        results = [e for e in results if e.difficulty == difficulty]

    if category is not None:
        results = [e for e in results if e.category == category]

    return results
