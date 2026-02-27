# FitCrave Datascience — AI Backend

> Decision-first AI health platform that removes cognitive overload from nutrition and fitness management.

## Architecture

```
fitcrave-datascience/
├── app/
│   ├── main.py                      # FastAPI entry point
│   ├── config.py                    # App configuration
│   ├── orchestrator/                # Central AI brain
│   │   ├── agent.py                 # LangGraph orchestrator
│   │   ├── intent_classifier.py     # Route user intent
│   │   └── context_manager.py       # User context retrieval
│   ├── engines/
│   │   ├── nutrition/               # SMP + MealSnap + Logging
│   │   │   ├── meal_planner.py
│   │   │   ├── macro_calculator.py
│   │   │   ├── meal_snap.py
│   │   │   ├── food_search.py
│   │   │   ├── adaptive_targets.py
│   │   │   └── data/
│   │   │       └── ifct_foods.json
│   │   ├── workout/                 # SWP + Tracking
│   │   │   ├── plan_generator.py
│   │   │   ├── exercise_db.py
│   │   │   ├── progressive_overload.py
│   │   │   ├── tracker.py
│   │   │   └── data/
│   │   │       └── exercises.json
│   │   └── coaching/                # AI Coach + Notifications
│   │       ├── daily_briefing.py
│   │       ├── reactive_coach.py
│   │       ├── weekly_review.py
│   │       └── notifier.py
│   ├── models/                      # Pydantic + DB schemas
│   │   ├── user.py
│   │   ├── meal.py
│   │   ├── workout.py
│   │   └── coaching.py
│   └── utils/
│       ├── llm_client.py            # Gemini API wrapper
│       ├── prompts.py               # All prompt templates
│       └── validators.py            # Response validation
├── tests/
├── requirements.txt
├── pyproject.toml
├── Dockerfile
└── .env.example
```

## Tech Stack

| Component | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| AI Orchestration | LangGraph |
| LLM | Google Gemini 2.0 Flash |
| Database | MongoDB (shared with Node.js backend) |
| Push Notifications | Firebase Cloud Messaging |
| Image Analysis | Gemini Vision |
| Nutrition Data | IFCT (self-hosted) + CalorieNinjas API |

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/FitCravebase/fitcrave-datascience.git
cd fitcrave-datascience

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env with your API keys

# 5. Run the server
uvicorn app.main:app --reload --port 8000
```

## Engines

### Nutrition Engine
Handles meal plan generation, MealSnap (image → macros), manual meal logging, macro calculation, and adaptive target adjustment.

### Workout Engine
Handles workout plan generation, exercise database, progressive overload tracking, and detailed workout logging (sets × reps × weight, RPE, cardio metrics).

### Coaching Engine
Handles daily briefings, reactive coaching (missed meals/workouts), weekly reviews, and push notifications via FCM.

## Related Repos

- [FitCrave2](https://github.com/FitCravebase/FitCrave2) — Flutter mobile app + Node.js community backend
