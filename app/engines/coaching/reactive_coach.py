"""
Reactive Coach

Triggers coaching messages based on user behavior events:
- Missed a meal → nudge to log/eat
- Missed a workout → supportive message + reschedule suggestion
- Hit a milestone → celebration message
- Unusual pattern detected → proactive intervention
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class CoachingTrigger(str, Enum):
    """Events that trigger reactive coaching."""

    MISSED_MEAL = "missed_meal"
    MISSED_WORKOUT = "missed_workout"
    STREAK_MILESTONE = "streak_milestone"        # 7, 14, 30 days etc.
    WEIGHT_MILESTONE = "weight_milestone"
    PROGRESSION_ACHIEVED = "progression_achieved"
    LOW_ADHERENCE = "low_adherence"              # < 50% for 3+ days
    OVERTRAINING_RISK = "overtraining_risk"      # High volume + low recovery
    CALORIE_SURPLUS_ALERT = "calorie_surplus_alert"
    CALORIE_DEFICIT_TOO_LOW = "calorie_deficit_too_low"


REACTIVE_COACHING_PROMPT = """You are FitCrave's AI coach responding to a user event.

## User Context
{user_context}

## Trigger Event
Type: {trigger_type}
Details: {trigger_details}

## Instructions
Generate a short coaching message (max 100 words):
1. Acknowledge the situation without judgment
2. Provide a specific, actionable suggestion
3. Connect it to their goal
4. Keep the tone supportive and decision-first

Examples of tone:
- NOT: "You missed your workout today. Try to be more consistent."
- YES: "Rest days happen! I've moved today's leg workout to tomorrow and adjusted your
  meal plan to match the lower activity. Your protein target stays the same."
"""


async def handle_trigger(
    user_id: str,
    trigger: CoachingTrigger,
    details: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate a reactive coaching message for a trigger event.

    Args:
        user_id: The user who triggered the event.
        trigger: The type of trigger event.
        details: Additional context about the event.

    Returns:
        Coaching message and any plan adjustments.

    TODO: Implement Gemini call + any automatic plan adjustments.
    """
    pass


async def check_for_triggers(user_id: str) -> list[CoachingTrigger]:
    """
    Check if any coaching triggers should fire for a user.

    Called periodically (e.g., every 2 hours) to detect:
    - Missed meals (no log by expected mealtime)
    - Missed workouts (no log by end of day for scheduled workout)
    - Milestones reached

    TODO: Implement trigger detection logic.
    """
    return []
