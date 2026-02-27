"""
User Model

Extended user profile for the AI backend.
Mirrors and extends the Node.js backend's User model.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WeightEntry(BaseModel):
    """A single weight measurement."""

    date: datetime
    weight_kg: float


class MacroTargetSnapshot(BaseModel):
    """Current calculated macro targets."""

    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int
    last_calculated: datetime
    adjustment_reason: str = ""


class UserProfile(BaseModel):
    """Complete user profile for AI decision-making."""

    # Identity (from existing User model)
    firebase_uid: str
    name: str
    email: str
    mobile: str | None = None

    # Biometrics
    age: int
    weight_kg: float
    height_cm: float
    gender: str  # "male" or "female"

    # Fitness Profile
    activity_level: str = "moderately_active"
    goal: str = "fat_loss"
    experience_level: str = "beginner"

    # Preferences
    dietary_restrictions: list[str] = Field(default_factory=list)
    cultural_preferences: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    disliked_foods: list[str] = Field(default_factory=list)

    # Equipment
    equipment: list[str] = Field(default_factory=list)

    # Schedule
    weekly_available_days: int = 5
    session_duration_minutes: int = 60
    preferred_workout_time: str | None = None  # "morning", "afternoon", "evening"
    meal_count_per_day: int = 4

    # Computed Values
    current_targets: MacroTargetSnapshot | None = None
    weight_history: list[WeightEntry] = Field(default_factory=list)

    # Tracking
    fcm_token: str | None = None  # For push notifications
    onboarding_complete: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
