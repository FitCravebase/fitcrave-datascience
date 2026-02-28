"""
Workout Plan Generator

Uses Gemini to generate periodized workout plans based on user's
goal, experience level, available equipment, and recovery status.
"""

import json
from typing import Any, List
import logging

from app.models.workout import WorkoutPlan, Exercise
# Provided by Phase 1 - assuming an async generate_structured function exists
# from app.utils.llm_client import generate_structured_response
from app.utils.prompts import FITCRAVE_SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

WORKOUT_PLAN_PROMPT = """You are FitCrave's AI Personal Trainer.
Generate a personalized {days_per_week}-day weekly workout plan.

## User Profile
Goal: {goal}
Experience level: {experience_level}
Session Target Duration: {session_duration} mins

## Equipment Constraint
You MUST ONLY assign exercises that can be performed with:
{equipment}

## Allowed Exercise Database
You MUST ONLY select exercises from this exact list. Do not invent exercises.
{exercise_list}

## Instructions
1. Design a {split_type} split.
2. For each day, select 4-6 exercises from the Allowed Exercise Database.
3. Use the exact `name` and `id` from the Allowed DB.
4. Specify target reps, sets, RPE (Rate of Perceived Exertion), and rest times.
5. Provide high-level weekly coaching notes.

You must respond STRICTLY fulfilling the provided JSON schema.
"""


class MockLLMClient:
    """Mock LLM client until Phase 1 builds the real `utils/llm_client.py`"""
    @staticmethod
    async def generate_structured(prompt: str, system_instruction: str, response_schema: Any) -> Any:
        logger.info("Mock LLM call made. Returning dummy parsed Pydantic model.")
        # We would normally use the Gemini GenAI SDK with `response_schema=WorkoutPlan`
        # Here we mock a successful parsing.
        return WorkoutPlan(
            plan_name="Mocked Hypertrophy Block",
            goal="muscle_gain",
            sessions=[],
            weekly_notes="Focus on progressive overload."
        )


async def generate_workout_plan(
    user_context: dict[str, Any],
    exercise_list: List[Exercise],
) -> WorkoutPlan:
    """
    Generate a personalized workout plan using Gemini and structured outputs.
    """
    
    equipment_str = ", ".join(user_context.get("equipment", ["body weight"]))
    days_per_week = user_context.get("days_per_week", 3)
    experience_level = user_context.get("experience_level", "beginner")
    goal = user_context.get("goal", "general_fitness")
    
    split_type = suggest_split_type(days_per_week, experience_level)
    
    # Format the allowed exercises for the prompt
    allowed_exercises_str = "\n".join(
        [f"- {ex.name} (Equipment: {ex.equipment}, Target: {', '.join(ex.primaryMuscles)})" for ex in exercise_list]
    )
    
    prompt = WORKOUT_PLAN_PROMPT.format(
        days_per_week=days_per_week,
        goal=goal,
        experience_level=experience_level,
        session_duration=user_context.get("session_duration", 45),
        equipment=equipment_str,
        exercise_list=allowed_exercises_str,
        split_type=split_type
    )

    # In production, this imports and uses the real central llm_client.
    # plan: WorkoutPlan = await llm_client.generate_structured_response(...)
    plan: WorkoutPlan = await MockLLMClient.generate_structured(
        prompt=prompt,
        system_instruction=FITCRAVE_SYSTEM_INSTRUCTION,
        response_schema=WorkoutPlan
    )
    
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
