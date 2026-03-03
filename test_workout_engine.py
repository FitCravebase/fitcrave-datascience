import asyncio
import json
from datetime import datetime

from app.engines.workout.exercise_db import exercise_db
from app.engines.workout.plan_generator import generate_workout_plan
from app.engines.workout.progressive_overload import check_progression
from app.models.workout import WorkoutPlan

async def run_demo():
    print("=========================================")
    print(" FITCRAVE WORKOUT ENGINE - PHASE 3 DEMO")
    print("=========================================\n")

    # 1. Test Exercise Database
    print("[1] Loading Exercise Database...")
    print(f"Total exercises loaded: {len(exercise_db.exercises)}")
    barbell_chest = exercise_db.filter_exercises(target_muscle="chest", equipment="barbell")
    print(f"Sample db query (Chest + Barbell): Found {len(barbell_chest)} exercises.")
    if barbell_chest:
        print(f"   -> Example: {barbell_chest[0].name}")
    print("\n-----------------------------------------\n")

    # 2. Test Plan Generation
    print("[2] Generating a Workout Plan (via Mock LLM)...")
    user_context = {
        "days_per_week": 3,
        "goal": "Build muscle",
        "experience_level": "intermediate",
        "equipment": ["barbell", "dumbbells", "bench"]
    }
    print(f"User context passed: {json.dumps(user_context)}")
    
    # Pass 50 filtered exercises to simulate LLM context window limits
    allowed_exercises = exercise_db.filter_exercises(limit=50)
    
    plan = await generate_workout_plan(user_context, allowed_exercises)
    
    print("\n[Generated Plan Pydantic Object]")
    print(f"Plan Name: {plan.plan_name}")
    print(f"Goal: {plan.goal}")
    print(f"Weekly Notes: {plan.weekly_notes}")
    print("\n-----------------------------------------\n")

    # 3. Test Progressive Overload
    print("[3] Testing Progressive Overload Logic...")
    print("Scenario: User just completed 3 sets of Barbell Bench Press.")
    print("Target was 8 reps @ RPE 8.")
    
    # Simulate user logging their sets efficiently
    logged_session = {
        "sets": [
            {"reps": 8, "weight": 60.0, "rpe": 7.0},
            {"reps": 8, "weight": 60.0, "rpe": 7.5},
            {"reps": 8, "weight": 60.0, "rpe": 8.0}
        ]
    }
    
    # We pass 2 consecutive identical successful sessions to trigger progression
    recent_sessions = [logged_session, logged_session]

    recommendation = check_progression(
        exercise_id="barbell_bench_press",
        exercise_name="Barbell Bench Press",
        equipment_type="barbell",
        target_reps=8,
        target_rpe=8.0,
        recent_sessions=recent_sessions
    )

    print(f"\n[Algorithm Recommendation]")
    if recommendation:
        print(f"Reasoning: {recommendation.reasoning}")
        print(f"New Recommended Weight: {recommendation.recommended_weight} kg (Up from {recommendation.current_weight} kg)")
    else:
        print("No progression recommended at this time.")
    
    print("\n=========================================")
    print(" DEMO COMPLETE")
    print("=========================================\n")

if __name__ == "__main__":
    # Python 3.11+ asyncio run pattern
    asyncio.run(run_demo())
