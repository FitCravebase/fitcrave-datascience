# Phase 3 Implementation Report: The Workout Engine

This document details the implementation of Phase 3 of the AI Backend, focusing on the Workout Engine.

## Objective

The goal of the Workout Engine is to generate personalized, periodized workout plans, maintain a curated database of exercises, and provide rule-based progression logic (progressive overload). This aligns with the "decision-first" philosophy outlined in the system architecture, moving the cognitive burden of workout planning from the user to the AI.

## 1. The Exercise Database & Data Models

### Why We Did It
To prevent the LLM from hallucinating exercises that users wouldn't know how to perform, we needed a constrained list of allowed exercises. We also needed strong data typing to ensure the API inputs and outputs remain consistent between the frontend Flutter app, the backend FastAPI server, and the MongoDB database.

### How We Did It
1.  **Downloaded Open Source Data:** We sourced an open-source JSON database of ~800 exercises from the "Free Exercise DB" project, containing detailed muscles, equipment, and difficulty levels.
2.  **Pydantic Models:** We defined strict schemas in `app/models/workout.py`. Pydantic handles validation automatically, ensuring all incoming and outgoing data maintains its intended shape. We bound the `Exercise` model tightly to the JSON's schema.

**Code Snippet: The Exercise Model (`app/models/workout.py`)**
```python
class Exercise(BaseModel):
    name: str = Field(..., description="The name of the exercise (e.g., 'Barbell Squat')")
    level: str = Field(..., description="Difficulty level (e.g., 'beginner')")
    mechanic: Optional[str] = Field(None, description="e.g., 'compound', 'isolation'")
    force: Optional[str] = Field(None, description="e.g., 'push' or 'pull'")
    equipment: Optional[str] = Field(None, description="Equipment required")
    primaryMuscles: List[str] = Field(default_factory=list, description="Target muscles")
    secondaryMuscles: List[str] = Field(default_factory=list, description="Other muscles worked")
    instructions: List[str] = Field(default_factory=list, description="Step-by-step instructions")
    category: str = Field(..., description="e.g., 'strength', 'stretching'")
```

### The Database Loader
We created an in-memory repository to load the JSON file on startup and efficiently filter it when the LangGraph agent needs to fetch eligible exercises based on the user's available equipment or target body parts.

**Code Snippet: The Filtering Logic (`app/engines/workout/exercise_db.py`)**
```python
def filter_exercises(
    self,
    target_muscle: str = None,
    category: str = None,
    equipment: str = None,
    name_query: str = None,
    limit: int = 50
) -> List[Exercise]:
    results = self.exercises

    if target_muscle:
        results = [ex for ex in results if any(target_muscle.lower() in m.lower() for m in ex.primaryMuscles)]
    
    # ... logic for handling other filters ...
    
    return results[:limit]
```

## 2. The Workout Plan Generator

### Why We Did It
We needed a way to leverage Gemini 2.0 Flash to design intelligent routines. By utilizing Gemini's Structured Outputs feature, we can prompt the LLM to design a cohesive weekly plan while enforcing that it responds in a strictly parsable JSON format matching our Pydantic `WorkoutPlan` model.

### How We Did It
1.  **Rule-based Split Suggestion:** We built a standard Python function to select the training split (e.g., Full Body vs Push/Pull/Legs) based on user experience and days available. This saves LLM tokens and provides predictable scaffolding.
2.  **Dynamic Prompting:** The `generate_workout_plan` function dynamically injects the user's context (equipment, goals) and the `exercise_list` (filtered from the local DB) into the `WORKOUT_PLAN_PROMPT`.
3.  **LLM Call Structuring:** We established the blueprint for injecting the `FITCRAVE_SYSTEM_INSTRUCTION` (to maintain the AI's "decision-first" personality) along with the expected Pydantic schema into the future Gemini API wrapper.

**Code Snippet: Plan Generation Framing (`app/engines/workout/plan_generator.py`)**
```python
# Format the allowed exercises for the prompt
allowed_exercises_str = "\n".join(
    [f"- {ex.name} (Equipment: {ex.equipment}, Target: {', '.join(ex.primaryMuscles)})" for ex in exercise_list]
)

prompt = WORKOUT_PLAN_PROMPT.format(
    days_per_week=days_per_week,
    goal=goal,
    experience_level=experience_level,
    session_duration=user_context.get("session_duration", 45),
    equipment=equipment_str,
    exercise_list=allowed_exercises_str,
    split_type=split_type
)

# Call to the LLM (Mocked pending Phase 1 completion)
plan: WorkoutPlan = await MockLLMClient.generate_structured(
    prompt=prompt,
    system_instruction=FITCRAVE_SYSTEM_INSTRUCTION,
    response_schema=WorkoutPlan
)
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
