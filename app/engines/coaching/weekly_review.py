"""
Weekly Review

Generates end-of-week analysis including:
- Adherence stats
- Weight trend analysis
- Macro averages vs targets
- Progressive overload progress
- Next week's adjustments
"""

from __future__ import annotations

from typing import Any


WEEKLY_REVIEW_PROMPT = """You are FitCrave's AI coach generating a weekly review.

## User Context
{user_context}

## This Week's Summary
- Meals logged: {meals_logged}/{meals_expected}
- Workouts completed: {workouts_completed}/{workouts_planned}
- Average daily calories: {avg_calories} kcal (target: {target_calories})
- Average protein: {avg_protein}g (target: {target_protein}g)
- Weight change: {weight_change:+.1f} kg
- Exercises progressed: {progressions}
- Streak: {streak} days

## Target Adjustments Made
{adjustments}

## Instructions
Generate a comprehensive but concise weekly review (max 250 words):
1. Celebrate wins first (any metric they did well on)
2. Honest but compassionate analysis of gaps
3. Specific adjustments for next week with rationale
4. One key focus area for the coming week
5. End with motivation tied to their long-term goal

Tone: Like a supportive personal trainer who genuinely cares about results.
"""


async def generate_weekly_review(user_id: str) -> dict[str, Any]:
    """
    Generate the end-of-week review for a user.

    Called by APScheduler cron job (default Sunday 8 PM IST).

    Args:
        user_id: The user to review.

    Returns:
        Weekly review content + any target adjustment recommendations.

    TODO: Implement by aggregating week's data and calling Gemini.
    """
    pass
