"""
Intent Classifier

Uses Gemini to classify user messages into actionable intents,
routing them to the correct engine.
"""

from __future__ import annotations

from app.orchestrator.agent import UserIntent


INTENT_CLASSIFICATION_PROMPT = """You are the FitCrave AI intent classifier.
Given a user message, classify it into exactly ONE of these intents:

- meal_plan: User wants to generate, view, or modify their meal plan
- meal_log: User wants to log a meal they ate
- meal_snap: User is sending a food image for macro analysis
- macro_query: User is asking about calories, macros, or nutrition info
- workout_plan: User wants to generate, view, or modify their workout plan
- workout_log: User wants to log a workout session
- coaching: User wants coaching advice, motivation, or feedback on their progress
- general_chat: General health/fitness question or conversation
- progress_check: User wants to see their stats, progress, or trends
- settings: User wants to update their profile, preferences, or goals

User message: {message}

Respond with ONLY the intent name, nothing else."""


async def classify_intent(message: str, has_image: bool = False) -> UserIntent:
    """
    Classify a user message into an actionable intent.

    Args:
        message: The user's text message.
        has_image: Whether the message includes an image attachment.

    Returns:
        The classified UserIntent.

    TODO: Implement Gemini API call for intent classification.
          For MVP, can also use keyword matching as a fast path.
    """
    # Fast path: if image is attached, it's almost certainly MealSnap
    if has_image:
        return UserIntent.MEAL_SNAP

    # TODO: Call Gemini with INTENT_CLASSIFICATION_PROMPT
    # For now, default to general chat
    return UserIntent.GENERAL_CHAT
