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
    class MockUserContext:
        def __init__(self):
            self.weekly_available_days = 3
            self.goal = "Build muscle"
            self.experience_level = "intermediate"
            self.equipment = ["barbell", "dumbbells", "bench"]
            self.injuries = ["None"]
            self.target_timeline = "3 months"
            self.session_duration_minutes = 45

    user_context = MockUserContext()
    print(f"User context passed: {vars(user_context)}")
    
    import time
    start_time = time.time()
    
    plan = await generate_workout_plan(user_context)
    
    end_time = time.time()
    print(f"\n[Generation Time]: {end_time - start_time:.2f} seconds")
    
    with open("test_logs.txt", "w", encoding="utf-8") as f:
        f.write("\n[Generated Plan JSON Schema Check]\n")
        f.write(f"Generation Time: {end_time - start_time:.2f} seconds\n")
        f.write(f"Plan Name: {plan.plan_name}\n")
        f.write(f"Goal: {plan.goal}\n")
        f.write(f"Weekly Notes: {plan.weekly_notes}\n")
        
        # Print the First Session's First Exercise Sets to prove they auto-expanded
        if plan.sessions and plan.sessions[0].exercises:
            first_ex = plan.sessions[0].exercises[0]
            f.write(f"\nExample Exercise Generated: {first_ex.exercise_name}\n")
            f.write(f"LLM generated target_sets/target_reps natively.\n")
            f.write(f"Expanded to {len(first_ex.sets)} WorkoutSets under the hood:\n")
            for w_set in first_ex.sets:
                f.write(f"  - Set {w_set.set_number}: {w_set.target_reps} reps (Rest: {w_set.rest_seconds}s)\n")
        f.write("\n-----------------------------------------\n")

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
