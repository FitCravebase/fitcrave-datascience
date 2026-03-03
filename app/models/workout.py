"""
Workout Engine Database Models

These Pydantic models define the structured data for workouts, ensuring
both the API inputs/outputs and the LLM generations are strictly typed
and validated before use.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Exercise(BaseModel):
    """
    Represents a single exercise definition from the database.
    Matches the schema of the downloaded `exercises.json` DB.
    """
    name: str = Field(..., description="The name of the exercise (e.g., 'Barbell Squat')")
    level: str = Field(..., description="Difficulty level (e.g., 'beginner')")
    mechanic: Optional[str] = Field(None, description="e.g., 'compound', 'isolation'")
    force: Optional[str] = Field(None, description="e.g., 'push' or 'pull'")
    equipment: Optional[str] = Field(None, description="Equipment required (e.g., 'barbell', 'body only')")
    primaryMuscles: List[str] = Field(default_factory=list, description="The specific target muscles")
    secondaryMuscles: List[str] = Field(default_factory=list, description="Other muscles worked")
    instructions: List[str] = Field(default_factory=list, description="Step-by-step instructions")
    category: str = Field(..., description="e.g., 'strength', 'stretching'")


class WorkoutSet(BaseModel):
    """
    Represents a single set of an exercise performed or planned.
    """
    set_number: int = Field(..., description="The order of the set (1, 2, 3...)")
    target_reps: int = Field(..., description="The planned number of repetitions")
    actual_reps: Optional[int] = Field(None, description="The actual number of repetitions performed")
    target_rpe: Optional[float] = Field(None, description="Target Rate of Perceived Exertion (1.0 - 10.0)")
    actual_rpe: Optional[float] = Field(None, description="Actual RPE recorded by user")
    weight_kg: float = Field(0.0, description="Weight used in kg. 0 indicates bodyweight.")
    rest_seconds: int = Field(90, description="Rest period after this set in seconds")


class PlannedExercise(BaseModel):
    """
    Represents an exercise as part of a workout session, containing its sets.
    """
    exercise_name: str = Field(..., description="The name of the exercise to perform")
    sets: List[WorkoutSet] = Field(..., description="The planned sets for this exercise")
    notes: Optional[str] = Field(None, description="Any specific form cues or LLM coaching notes")


class WorkoutSession(BaseModel):
    """
    Represents a single daily workout routine.
    """
    day: str = Field(..., description="Day of the week or plan (e.g., 'Monday', 'Day 1')")
    focus_area: str = Field(..., description="Main focus of the workout (e.g., 'Push', 'Legs', 'Full Body')")
    exercises: List[PlannedExercise] = Field(..., description="List of exercises in the session")
    estimated_duration_minutes: int = Field(..., description="Estimated time to complete session")


class WorkoutPlan(BaseModel):
    """
    Represents a full periodized workout plan (typically a week).
    This is what the LLM will output.
    """
    plan_name: str = Field(..., description="A catchy, descriptive name for the routine")
    goal: str = Field(..., description="The primary goal (e.g., 'Hypertrophy', 'Strength', 'Fat Loss')")
    sessions: List[WorkoutSession] = Field(..., description="The individual workout days")
    weekly_notes: str = Field(..., description="High-level coaching advice for the week")
