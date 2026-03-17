# Phase 3 Implementation Report: The Workout Engine

This document details the implementation of Phase 3 of the AI Backend, focusing on the Workout Engine.

## Objective

The goal of the Workout Engine is to generate personalized, periodized workout plans, maintain a curated database of exercises, and provide rule-based progression logic (progressive overload). This aligns with the "decision-first" philosophy outlined in the system architecture, moving the cognitive burden of workout planning from the user to the AI.

## 1. Data Models

We use Pydantic models in `app/models/workout.py` to ensure the workout plan structure is fully typed and validated. These models are designed to match what the front-end expects for SWP dashboards:

- `WorkoutSet` → per-set reps, RPE, weight, rest.
- `PlannedExercise` → an exercise with a list of `WorkoutSet`s and optional notes.
- `WorkoutSession` → a day's routine (day label, focus area, estimated duration, list of `PlannedExercise`s).
- `WorkoutPlan` → overall weekly plan with `plan_name`, `goal`, `sessions`, and `weekly_notes`.

Validation happens automatically when we construct `WorkoutPlan(**raw_json)` from the LLM output.

## 2. The Workout Plan Generator

### Why We Did It
We needed a way to leverage Gemini 2.0 Flash to design intelligent routines. By utilizing Gemini's Structured Outputs feature, we can prompt the LLM to design a cohesive weekly plan while enforcing that it responds in a strictly parsable JSON format matching our Pydantic `WorkoutPlan` model.

### How We Did It

1.  **Rule-based Split Suggestion:** We use `suggest_split_type()` to choose a sensible split (Full Body, Upper/Lower, Push/Pull/Legs) based on `weekly_available_days` and `experience_level`. This keeps the plan structure predictable.
2.  **Dynamic Prompting:** The `generate_workout_plan` function builds `WORKOUT_PLAN_PROMPT` from the `UserProfile` (goal, experience, equipment, injuries, days per week, session duration) without passing a local exercise database. The LLM selects exercises from its own knowledge under these constraints.
3.  **LLM Call Structuring:** We call `gemini_client.generate_json(...)` with the system instruction (`FITCRAVE_SYSTEM_INSTRUCTION`) and a prompt that includes an explicit JSON schema. The returned JSON is parsed into a `WorkoutPlan`.

**Code Snippet: Plan Generation Framing (`app/engines/workout/plan_generator.py`)**
```python
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

raw_json = await gemini_client.generate_json(
    prompt=prompt,
    system_instruction=FITCRAVE_SYSTEM_INSTRUCTION,
    temperature=0.4,
)
plan = WorkoutPlan(**raw_json)
```

## 3. Progressive Overload Tracking

### Why We Did It
LLMs are generally bad at deterministic math and enforcing strict mathematical rules over a sequence of logs. Determining progressive overload (when to add weight to the bar) should be handled by classical, rule-based algorithms for safety and consistency, not by generative AI.

### How We Did It
We implemented `check_progression()`, a purely mathematical function that analyzes a user's recent performance on a specific exercise. If they hit their target reps at or below their target Rate of Perceived Exertion (RPE) across consecutive sessions, the engine recommends a safe weight bump. Lookups are used to determine standard jumps (e.g., 2.5kg for barbells, 2kg for dumbbells, or $+2$ reps if bodyweight).

**Code Snippet: Overload Rule Logic (`app/engines/workout/progressive_overload.py`)**
```python
for s in sets:
    # Did they hit target reps?
    if s.get("reps", 0) < target_reps:
        all_hit = False
        break
    # Was RPE at or below target? (lower RPE = easier = ready to progress)
    if s.get("rpe", 10) > target_rpe + 0.5:  # 0.5 tolerance
        all_hit = False
        break

if all_hit:
    increment = WEIGHT_INCREMENTS.get(equipment_type, 2.5)
    
    # E.g. Increase 60kg Bench Press by 2.5kg 
    return ProgressionRecommendation(
        current_weight=current_weight,
        recommended_weight=current_weight + increment
        # ... extra context parameters
    )
```

## Conclusion & Next Steps

All of the logic established here has been verified automatically via `pytest`, ensuring that as the broader application evolves, the constraints and calculations mapping to these modules will not break regressionally.

From here, this Workout Engine is ready to be plugged directly into the Phase 4 LangGraph Orchestrator, allowing the central agent to say "Hey, this user wants to build muscle and has dumbbells, Workout Engine, give me a plan."
