"""
Workout Plan Generator

Uses Gemini to generate periodized workout plans based on user's
goal, experience level, available equipment, and recovery status.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from thefuzz import process, fuzz

from app.models.workout import WorkoutPlan, LLMWorkoutPlan
from app.engines.workout.exercise_db import exercise_db
from app.engines.workout.progressive_overload_calculator import (
    get_starting_weight, compute_overload_weights
)
from app.utils.prompts import FITCRAVE_SYSTEM_INSTRUCTION
from app.utils.llm_client import gemini_client

logger = logging.getLogger(__name__)

WORKOUT_PLAN_PROMPT = """You are FitCrave's AI Personal Trainer.
Generate a personalized {days_per_week}-day weekly workout plan.

## User Profile
Goal: {goal}
Target Timeline: {target_timeline}
Experience level: {experience_level}
Body Weight: {body_weight_kg} kg
Session Target Duration: {session_duration} mins

## Medical/Injury Constraints
Injuries to avoid straining: {injuries}

## Equipment Constraint
You MUST ONLY assign exercises that can be performed with the following available equipment:
{equipment}

## Weight / Loading Instructions
{weight_instructions}

{continuity_instructions}

## Instructions
1. Recommend the optimal split (Full Body, Upper/Lower, PPL, or Custom) based on the user's goal, experience level, equipment, days per week, and session duration.
2. For each day, select 4-6 highly effective exercises appropriate for the user's experience level and equipment.
3. DO NOT assign any exercises that strain the user's listed injuries!
4. Ensure the total workout duration stays near the target duration of {session_duration} minutes.
5. Specify target reps, sets, RPE (Rate of Perceived Exertion), rest times, and a starting weight for EVERY exercise.
6. For bodyweight exercises (push-ups, pull-ups, planks, etc.) set weight_kg to 0.0.
7. Provide high-level weekly coaching notes.

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
- target_sets: int (e.g., 4)
- target_reps: int (e.g., 10)
- rest_seconds: int (e.g., 90)
- weight_kg: float (e.g., 60.0 — suggested working weight in kg; 0.0 for bodyweight)
- target_rpe: float (e.g., 7.5 — target exertion on a 1-10 scale; 7=3 reps left, 8=2 reps left, 9=1 rep left)
- notes: string or null
"""

async def generate_workout_plan(
    user_context: Any,  # Expecting UserProfile
    db=None,            # Firestore AsyncClient — used for progressive overload lookup
    previous_plan_dict: Optional[Dict] = None
) -> WorkoutPlan:
    """
    Generate a personalized workout plan using Gemini and structured outputs.
    Prescribes weights using:
      - Progressive overload history (if workout_logs exist)
      - ExRx.net population-based strength standards (first plan)
    """
    equipment_str = ", ".join(user_context.equipment) if user_context.equipment else "body weight only"
    injuries_str  = ", ".join(user_context.injuries)  if user_context.injuries  else "None"
    target_timeline_str = user_context.target_timeline or "No specific timeline"
    body_weight_kg = getattr(user_context, 'weight_kg', 70.0)
    experience_level = user_context.experience_level

    # ── Weight context for the prompt ─────────────────────────────────────
    overload_weights: Dict[str, float] = {}
    if db and hasattr(user_context, 'firebase_uid'):
        try:
            overload_weights = compute_overload_weights(user_context.firebase_uid, db)
        except Exception as e:
            logger.warning(f"Could not compute overload weights: {e}")

    if overload_weights:
        lines = [f"  - {name}: {kg} kg" for name, kg in overload_weights.items()]
        weight_instructions = (
            "The user has previous workout data. Use these EXACT weights from their last session "
            "(already adjusted for progressive overload). If an exercise is not listed below, "
            "prescribe a sensible weight based on the user's bodyweight and experience:\n"
            + "\n".join(lines)
        )
    else:
        weight_instructions = (
            f"This is likely the user's FIRST plan. Prescribe conservative starting weights "
            f"using population-based strength standards (ExRx.net). "
            f"User bodyweight is {body_weight_kg} kg, experience level is {experience_level}. "
            f"For beginners, target roughly 40-60% of estimated 1RM. "
            f"For bodyweight exercises, set weight_kg to 0.0."
        )

    continuity_instructions = ""
    if previous_plan_dict:
        # Simplify the previous plan to avoid token bloat and ensure focus
        simple_sessions = []
        for session in previous_plan_dict.get('sessions', []):
            simple_ex = [{"exercise_name": e.get("exercise_name")} for e in session.get('exercises', [])]
            simple_sessions.append({
                "day": session.get("day"),
                "focus_area": session.get("focus_area"),
                "exercises": simple_ex
            })
            
        continuity_instructions = (
            "## PROGRAM CONTINUITY (CRITICAL)\n"
            "You are advancing the user to the next week of their current mesocycle. "
            "You MUST keep the exact same sessions and exercise selections as their previous plan below. "
            "Your ONLY job is to update the target_sets, target_reps, target_rpe, and weight_kg based on the progressive overload data.\n"
            f"PREVIOUS PLAN STRUCTURE:\n{json.dumps(simple_sessions, indent=2)}"
        )
        
    prompt = WORKOUT_PLAN_PROMPT.format(
        days_per_week=user_context.weekly_available_days,
        goal=user_context.goal,
        target_timeline=target_timeline_str,
        experience_level=experience_level,
        body_weight_kg=body_weight_kg,
        session_duration=user_context.session_duration_minutes,
        equipment=equipment_str,
        injuries=injuries_str,
        weight_instructions=weight_instructions,
        continuity_instructions=continuity_instructions,
    )

    # Call Gemini JSON mode
    raw_json_dict = await gemini_client.generate_json(
        prompt=prompt,
        system_instruction=FITCRAVE_SYSTEM_INSTRUCTION,
        temperature=0.2
    )
    
    # Parse the dictionary back into the lean LLM Pydantic schema
    llm_plan = LLMWorkoutPlan.model_validate(raw_json_dict)
    
    # Expand the lean LLM representation into the full Firestore schema (with WorkoutSet arrays)
    plan = llm_plan.to_firestore_model()
    
    # --- PHASE 3: Fuzzy Matching & YouTube Fallback ---
    # Create a simple dictionary of allowed names to their objects for fast lookup
    allowed_names = {ex.name: ex for ex in exercise_db.exercises}
    allowed_name_list = list(allowed_names.keys())
    
    for session in plan.sessions:
        for p_ex in session.exercises:
            best_match, score = process.extractOne(
                p_ex.exercise_name, 
                allowed_name_list, 
                scorer=fuzz.token_sort_ratio
            )
            
            if score >= 85:
                # Strong match! We can safely use our DB exercise and its specific video ID
                matched_db_ex = allowed_names[best_match]
                p_ex.exercise_name = matched_db_ex.name # Correct the typo into official name
                p_ex.video_id = matched_db_ex.video_id
            else:
                # Weak or no match (LLM hallucinated a completely new valid exercise)
                # Fallback to the Universal YouTube search link
                query = quote_plus(f"How to do {p_ex.exercise_name} exercise proper form tutorial")
                p_ex.youtube_search_url = f"https://www.youtube.com/results?search_query={query}"
                p_ex.video_id = None
                
                logger.warning(
                    f"Exercise '{p_ex.exercise_name}' not found locally (Best match: {best_match} @ {score}%). "
                    f"Generated fallback URL."
                )
    
    return plan
