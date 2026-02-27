"""
Context Manager

Responsible for pulling and assembling user context from the database.
This context is injected into every LLM call so the AI has full awareness
of the user's profile, recent meals, workouts, and trends.
"""

from __future__ import annotations

from typing import Any


async def get_user_context(user_id: str) -> dict[str, Any]:
    """
    Assemble comprehensive user context for AI decision-making.

    Pulls from MongoDB:
        - User profile (age, weight, height, goals, restrictions, equipment)
        - Current macro targets
        - Recent meal logs (last 7 days)
        - Recent workout logs (last 7 days)
        - Weight history trend
        - Adherence stats (meal logging %, workout completion %)
        - Active workout plan summary

    Returns:
        A dictionary containing all relevant user context.

    TODO: Implement MongoDB queries via motor/beanie.
    """
    context = {
        "profile": {},          # User profile data
        "targets": {},          # Current macro/calorie targets
        "recent_meals": [],     # Last 7 days of meal logs
        "recent_workouts": [],  # Last 7 days of workout logs
        "weight_trend": [],     # Weight history (last 30 days)
        "adherence": {
            "meal_logging_pct": 0.0,
            "workout_completion_pct": 0.0,
        },
        "active_plan": {},      # Current workout plan summary
    }

    # TODO: Fetch from database
    return context


def format_context_for_prompt(context: dict[str, Any]) -> str:
    """
    Format user context into a string suitable for injection into LLM prompts.

    Keeps the context concise to minimize token usage while preserving
    all decision-relevant information.

    TODO: Implement formatting logic.
    """
    return str(context)
