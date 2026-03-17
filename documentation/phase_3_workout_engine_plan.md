# FitCrave AI Backend: Workout Engine – Current Design Overview

## Goal

The Workout Engine generates personalized, periodized workout plans for the SWP (Smart Workout Planner) feature. It:

- Listens to Firestore for `requires_new_plan` triggers on `users/{uid}`.
- Converts the user document into a typed `UserProfile`.
- Calls Gemini via `generate_workout_plan(...)` to produce a `WorkoutPlan`.
- Writes the plan back to `users/{uid}/workout_plans/current_plan`.

## Key Components

- `app/models/user.py` → `UserProfile` (biometrics, goals, SWP fields like `weekly_available_days`, `session_duration_minutes`, `equipment`, `injuries`).
- `app/models/workout.py` → `WorkoutPlan` + nested models for sessions, exercises, and sets.
- `app/engines/workout/plan_generator.py` → Builds a prompt from `UserProfile` and uses `gemini_client.generate_json` to get a JSON plan that is parsed into `WorkoutPlan`.
- `app/engines/workout/progressive_overload.py` → Optional rule-based logic for progression (not yet wired into Firestore).
- `app/orchestrator/firestore_listener.py` → Watches the Firestore `users` collection, runs `generate_workout_plan` when `requires_new_plan` is `true`, saves the result, and clears the flag.

Gemini models are configured via `app/config.py`:

- `GEMINI_MODEL` (default `gemini-2.0-pro`) for text.
- `GEMINI_VISION_MODEL` (default `gemini-2.0-flash`) for image analysis in other engines.
