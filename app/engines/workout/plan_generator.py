"""
Workout Plan Generator

Uses Gemini to generate periodized workout plans based on the user's
goal, experience level, available equipment, injuries, and schedule.
"""

import logging
from typing import Any

from app.models.user import UserProfile
from app.models.workout import WorkoutPlan
from app.utils.llm_client import gemini_client
from app.utils.prompts import FITCRAVE_SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

WORKOUT_PLAN_PROMPT = """You are FitCrave's AI Personal Trainer.
Generate a personalized {days_per_week}-day weekly workout plan for the user below.

## User Profile
Name: {name}
Goal: {goal}
Experience level: {experience_level}
Session Target Duration: {session_duration} mins
Weekly Available Days: {days_per_week}
Equipment: {equipment}
Injuries / Limitations: {injuries}

## Instructions
1. Choose safe, appropriate exercises based on the user's goal, experience, equipment, and injuries.
2. Design a {split_type} split for the week.
3. For each day, define 4–6 exercises with sets, reps, target RPE, and rest times.
4. Keep total session duration close to the target.
5. Provide concise weekly coaching notes.

You MUST respond with a single JSON object matching this schema:
{{
  "plan_name": "string",
  "goal": "string",
  "sessions": [
    {{
      "day": "string",
      "focus_area": "string",
      "estimated_duration_minutes": 0,
      "exercises": [
        {{
          "exercise_name": "string",
          "notes": "string",
          "sets": [
            {{
              "set_number": 1,
              "target_reps": 8,
              "target_rpe": 7.5,
              "weight_kg": 0,
              "rest_seconds": 90
            }}
          ]
        }}
      ]
    }}
  ],
  "weekly_notes": "string"
}}
Do NOT include any text outside this JSON.
"""


def suggest_split_type(days_per_week: int, experience_level: str) -> str:
    """Suggest the best training split based on user parameters."""
    if experience_level.lower() == "beginner":
        return "Full Body"
    if days_per_week <= 3:
        return "Full Body"
    if days_per_week == 4:
        return "Upper/Lower"
    return "Push/Pull/Legs"


async def generate_workout_plan(
    user_profile: UserProfile,
    db: Any | None = None,
    previous_plan_dict: dict[str, Any] | None = None,
) -> WorkoutPlan:
    """
    Generate a personalized workout plan using Gemini and structured outputs.

    This function is called by the Firestore listener when `requires_new_plan` is true.
    """
    days_per_week = int(user_profile.weekly_available_days or 3)
    session_minutes = int(user_profile.session_duration_minutes or 45)
    experience_level = (user_profile.experience_level or "beginner").lower()
    goal = user_profile.goal or "General Fitness"

    equipment_str = ", ".join(user_profile.equipment) if user_profile.equipment else "bodyweight only"
    injuries_str = ", ".join(getattr(user_profile, "injuries", [])) or "none reported"

    split_type = suggest_split_type(days_per_week, experience_level)

    # Build continuity hint (if a previous plan exists)
    continuity_hint = ""
    if previous_plan_dict:
        try:
            prev_name = previous_plan_dict.get("plan_name", "previous block")
            continuity_hint = (
                f"\n\n## Program Continuity\n"
                f"The user previously followed a plan called '{prev_name}'. "
                f"Preserve overall structure but progress volume or load where appropriate."
            )
        except Exception:
            continuity_hint = ""

    prompt = WORKOUT_PLAN_PROMPT.format(
        days_per_week=days_per_week,
        name=user_profile.name,
        goal=goal,
        experience_level=experience_level,
        session_duration=session_minutes,
        equipment=equipment_str,
        injuries=injuries_str,
        split_type=split_type,
    ) + continuity_hint

    try:
        raw_json = await gemini_client.generate_json(
            prompt=prompt,
            system_instruction=FITCRAVE_SYSTEM_INSTRUCTION,
            temperature=0.4,
        )
        plan = WorkoutPlan(**raw_json)
        return plan
    except Exception as e:
        logger.error("Error generating workout plan via Gemini: %s", e, exc_info=True)
        # Fallback: minimal safe plan so the listener doesn't crash
        return WorkoutPlan(
            plan_name=f"{goal} – Simple Starter Plan",
            goal=goal,
            sessions=[],
            weekly_notes="We encountered an error generating a detailed plan. Please try again later.",
        )

