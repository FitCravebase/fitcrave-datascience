"""
Workout Plan Generator

Uses Gemini to generate periodized workout plans based on user's
goal, experience level, available equipment, and recovery status.
"""

import json
from typing import Any, List
import logging

from app.models.workout import WorkoutPlan
from app.utils.prompts import FITCRAVE_SYSTEM_INSTRUCTION
from app.utils.llm_client import gemini_client

logger = logging.getLogger(__name__)

WORKOUT_PLAN_PROMPT = """You are FitCrave's AI Personal Trainer.
Generate a personalized {days_per_week}-day weekly workout plan.

## User Profile
Goal: {goal}
Target Timeline: {target_timeline}
Experience level: {experience_level}
Session Target Duration: {session_duration} mins

## Medical/Injury Constraints
Injuries to avoid straining: {injuries}

## Equipment Constraint
You MUST ONLY assign exercises that can be performed with the following available equipment:
{equipment}

## Instructions
1. Design a {split_type} split.
2. For each day, select 4-6 highly effective exercises appropriate for the user's experience level and equipment.
3. DO NOT assign any exercises that strain the user's listed injuries!
4. Ensure the total workout duration stays near the target duration of {session_duration} minutes.
5. Specify target reps, sets, RPE (Rate of Perceived Exertion), and rest times.
6. Provide high-level weekly coaching notes.

You must respond STRICTLY fulfilling the provided JSON schema. Ensure your response is valid JSON matching the exact schema definition.

Output Schema Details:
A JSON object with:
- plan_name: string
- goal: string
- weekly_notes: string
- sessions: list of session objects

Each session object contains:
- day: string ("Day 1", etc)
- focus_area: string
- estimated_duration_minutes: int
- exercises: list of exercise objects

Each exercise object contains:
- exercise_name: string
- notes: string or null
- sets: list of set objects

Each set object contains:
- set_number: int
- target_reps: int
- weight_kg: float
- rest_seconds: int
"""

async def generate_workout_plan(
    user_context: Any # Expecting UserProfile
) -> WorkoutPlan:
    """
    Generate a personalized workout plan using Gemini and structured outputs.
    """
    
    equipment_str = ", ".join(user_context.equipment) if user_context.equipment else "body weight only"
    injuries_str = ", ".join(user_context.injuries) if user_context.injuries else "None"
    target_timeline_str = user_context.target_timeline if user_context.target_timeline else "No specific timeline"
    
    days_per_week = user_context.weekly_available_days
    experience_level = user_context.experience_level
    goal = user_context.goal
    
    split_type = suggest_split_type(days_per_week, experience_level)
    
    prompt = WORKOUT_PLAN_PROMPT.format(
        days_per_week=days_per_week,
        goal=goal,
        target_timeline=target_timeline_str,
        experience_level=experience_level,
        session_duration=user_context.session_duration_minutes,
        equipment=equipment_str,
        injuries=injuries_str,
        split_type=split_type
    )

    # Call Gemini JSON mode
    raw_json_dict = await gemini_client.generate_json(
        prompt=prompt,
        system_instruction=FITCRAVE_SYSTEM_INSTRUCTION,
        temperature=0.2
    )
    
    # Parse the dictionary back into the Pydantic WorkoutPlan schema
    plan = WorkoutPlan.model_validate(raw_json_dict)
    
    return plan


def suggest_split_type(days_per_week: int, experience_level: str) -> str:
    """Suggest the best training split based on user parameters."""
    if experience_level == "beginner":
        return "Full Body"
    if days_per_week <= 3:
        return "Full Body"
    if days_per_week == 4:
        return "Upper/Lower"
    return "Push/Pull/Legs"
