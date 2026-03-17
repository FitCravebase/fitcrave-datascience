"""
DEPRECATED:

This module used to expose a small FastAPI service that started the
Firestore-based SWP workout plan listener in the background. The SWP
flow has been migrated to an HTTP-queued design using the endpoint
`/api/v1/workout/plan/request` in `app.engines.workout.router`, so
this listener wrapper is no longer used and is kept only for
historical reference.
"""

import os
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.orchestrator.firestore_listener import start_listener


def _start_background_listener() -> None:
    """(Deprecated) Start the Firestore workout-plan listener in a background thread."""
    thread = threading.Thread(
        target=start_listener,
        name="firestore-listener",
        daemon=True,
    )
    thread.start()


app = FastAPI(
    title="FitCrave Workout Listener (Deprecated)",
    description=(
        "Background Firestore listener for SWP workout plan generation. "
        "Replaced by HTTP-queued workflow in app.engines.workout.router."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    _start_background_listener()


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "fitcrave-workout-listener (deprecated)",
        "env": os.getenv("APP_ENV", "production"),
    }

