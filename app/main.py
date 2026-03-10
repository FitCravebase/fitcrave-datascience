"""
FitCrave AI Backend — Main Application Entry Point

FastAPI server that exposes the AI orchestrator, nutrition engine,
workout engine, and coaching engine as REST endpoints.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    # --- Startup ---
    print(f"🚀 FitCrave AI Backend starting on {settings.APP_HOST}:{settings.APP_PORT}")
    print(f"📊 Environment: {settings.APP_ENV}")

    # Initialize MongoDB connection via motor/beanie
    await init_db()
    # TODO: Initialize Gemini LLM client
    # TODO: Initialize Firebase Admin SDK
    # TODO: Start APScheduler for coaching notifications

    yield

    # --- Shutdown ---
    print("🛑 FitCrave AI Backend shutting down...")
    # TODO: Close database connections
    # TODO: Shutdown scheduler


app = FastAPI(
    title="FitCrave AI Backend",
    description=(
        "Decision-first AI health platform. "
        "Nutrition Engine, Workout Engine, and Coaching Engine "
        "powered by Google Gemini."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow Flutter app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to your Flutter app's domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "fitcrave-ai"}


# ------------------------------------------------------------------
# Route Registration (uncomment as engines are built)
# ------------------------------------------------------------------
# from app.engines.nutrition.router import router as nutrition_router
# from app.engines.workout.router import router as workout_router
# from app.engines.coaching.router import router as coaching_router
# from app.orchestrator.router import router as orchestrator_router

# app.include_router(orchestrator_router, prefix="/api/v1/chat", tags=["Orchestrator"])
# app.include_router(nutrition_router, prefix="/api/v1/nutrition", tags=["Nutrition"])
# app.include_router(workout_router, prefix="/api/v1/workout", tags=["Workout"])
# app.include_router(coaching_router, prefix="/api/v1/coaching", tags=["Coaching"])
