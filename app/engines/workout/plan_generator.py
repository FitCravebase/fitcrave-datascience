"""
Workout Plan Generator

Uses Gemini to generate periodized workout plans based on user's
goal, experience level, available equipment, and recovery status.
"""

from __future__ import annotations

from typing import Any


WORKOUT_PLAN_PROMPT = """You are FitCrave's workout AI. Generate a personalized weekly workout plan.

## User Profile
{user_context}

## Available Equipment
{equipment}

## Constraints
- Experience level: {experience_level}
- Available days per week: {days_per_week}
- Session duration: {session_duration} minutes
- Goal: {goal}
- Injuries/limitations: {limitations}

## Exercise Database
You MUST select exercises ONLY from this list:
{exercise_list}

## Recovery Status
- Last workout: {last_workout}
- Current recovery/readiness score: {readiness_score}/100
- Muscle soreness: {soreness}

## Instructions
1. Design a {split_type} split for {days_per_week} days
2. Select exercises from the provided database ONLY
3. Specify sets, reps, target RPE, and rest periods for each exercise
4. Include warm-up and cool-down recommendations
5. Add cardio recommendations based on goal
6. Explain WHY you chose this split and these exercises

Respond in JSON format:
{{
  "split_type": "push_pull_legs",
  "days": [
    {{
      "day_number": 1,
      "day_name": "Push Day",
      "focus": ["chest", "shoulders", "triceps"],
      "warmup": "5 min light cardio + dynamic stretches",
      "exercises": [
        {{
          "exercise_id": "barbell_bench_press",
          "name": "Barbell Bench Press",
          "sets": 4,
          "reps": "8-10",
          "target_rpe": 7.5,
          "rest_seconds": 120,
          "notes": "Focus on controlled eccentric"
        }}
      ],
      "cardio": {{
        "type": "steady_state",
        "duration_minutes": 15,
        "notes": "Incline walk at 6.0 speed 10-12% incline"
      }},
      "cooldown": "5 min stretching focusing on chest and shoulders"
    }}
  ],
  "weekly_notes": "Explanation of plan design and progression strategy",
  "deload_week": "Every 4th week, reduce volume by 40%"
}}"""


async def generate_workout_plan(
    user_context: dict[str, Any],
    exercise_list: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Generate a personalized workout plan using Gemini.

    Args:
        user_context: Full user context including equipment, experience, goals.
        exercise_list: Filtered exercises based on user's available equipment.

    Returns:
        Structured workout plan dict.

    TODO: Implement Gemini API call with WORKOUT_PLAN_PROMPT.
    """
    pass


async def suggest_split_type(
    days_per_week: int, experience_level: str, goal: str
) -> str:
    """
    Suggest the best training split based on user parameters.

    Rules (no LLM needed):
    - 2-3 days/week → Full body
    - 4 days/week → Upper/Lower
    - 5-6 days/week → Push/Pull/Legs or Bro split
    - Beginner → Always full body regardless of days
    """
    if experience_level == "beginner":
        return "full_body"
    if days_per_week <= 3:
        return "full_body"
    if days_per_week == 4:
        return "upper_lower"
    return "push_pull_legs"
