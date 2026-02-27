"""
Daily Briefing Generator

Generates a morning push notification with:
- Today's meal plan summary
- Today's workout preview
- Any target adjustments
- Motivational note based on recent adherence
"""

from __future__ import annotations

from typing import Any


DAILY_BRIEFING_PROMPT = """You are FitCrave's AI coach generating a morning briefing.

## User Context
{user_context}

## Today's Meal Plan
{meal_plan}

## Today's Workout
{workout_plan}

## Recent Stats
- Streak: {streak_days} days
- Yesterday's adherence: meal={meal_adherence}%, workout={workout_adherence}%
- Weight trend: {weight_trend}

## Instructions
Generate a brief, friendly morning message (max 150 words) that:
1. Greets the user by name
2. Summarizes today's nutrition targets and key meals
3. Previews today's workout (if any)
4. Notes any progressions or achievements
5. Adds a motivational touch based on their streak/progress
6. If targets were adjusted, briefly explain WHY

Tone: Supportive, confident, decision-first (tell them what to do, not ask).
"""


async def generate_daily_briefing(user_id: str) -> dict[str, Any]:
    """
    Generate the daily morning briefing for a user.

    Called by APScheduler cron job at the configured time (default 7 AM IST).

    Args:
        user_id: The user to generate the briefing for.

    Returns:
        Dict with briefing content and notification payload.

    TODO: Implement by:
        1. Fetch user context
        2. Generate/retrieve today's meal plan
        3. Get today's workout from active plan
        4. Call Gemini with DAILY_BRIEFING_PROMPT
        5. Return structured notification payload
    """
    pass
