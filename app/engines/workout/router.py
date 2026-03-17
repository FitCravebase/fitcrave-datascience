"""
Workout Engine — REST API Router

Queued workout plan generation for SWP (Smart Workout Planner).
The mobile app calls a lightweight endpoint which immediately enqueues
generation work in a background task and returns a quick response.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

import firebase_admin
from firebase_admin import credentials, firestore  # type: ignore

from app.config import settings
from app.models.user import UserProfile
from app.engines.workout.plan_generator import generate_workout_plan

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Firestore Admin Client (shared) ──────────────────────────────────

_db: Any | None = None


def get_db():
    """Lazily initialise the Firestore admin client."""
    global _db
    if _db is not None:
        return _db

    if not firebase_admin._apps:
        cred_path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", None)
        try:
            if cred_path:
                cred = credentials.Certificate(cred_path)
                logger.info(
                    "Firebase Admin (workout router) initialised with explicit credentials at %s",
                    cred_path,
                )
            else:
                cred = credentials.ApplicationDefault()
                logger.info(
                    "Firebase Admin (workout router) initialised with Application Default Credentials.",
                )
            firebase_admin.initialize_app(cred)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(
                "Failed to initialise Firebase Admin in workout router: %s", exc, exc_info=True
            )
            raise

    _db = firestore.client()
    return _db


# ── Request / Response Models ────────────────────────────────────────


class WorkoutPlanRequest(BaseModel):
    """Minimal request body – we read full profile from Firestore."""

    user_id: str


class WorkoutPlanStatus(BaseModel):
    status: str
    message: str | None = None


# ── Background worker ────────────────────────────────────────────────


async def _generate_and_save_plan(user_id: str) -> None:
    """
    Background task that generates a workout plan and saves it to Firestore.

    Mirrors the logic from `process_new_plan` in `firestore_listener.py`,
    but is triggered via HTTP instead of a snapshot listener.
    """
    db = get_db()

    try:
        logger.info("🏋️ Starting queued workout plan generation for user %s", user_id)

        user_doc = db.collection("users").document(user_id).get()
        if not user_doc.exists:
            logger.warning("No Firestore user document found for %s", user_id)
            db.collection("users").document(user_id).update(
                {"requires_new_plan": False, "plan_status": "error_no_profile"}
            )
            return

        doc_dict: dict[str, Any] = user_doc.to_dict() or {}

        user_profile = UserProfile(
            firebase_uid=user_id,
            email=doc_dict.get("email") or f"{user_id}@example.com",
            name=doc_dict.get("name") or "User",
            age=doc_dict.get("age") or 25,
            gender=doc_dict.get("gender") or "prefer_not_to_say",
            height_cm=doc_dict.get("height") or 170.0,
            weight_kg=doc_dict.get("weight_kg") or doc_dict.get("weight") or 70.0,
            activity_level=doc_dict.get("activity_level") or "moderately_active",
            goal=doc_dict.get("swp_goal") or "General Fitness",
            experience_level=doc_dict.get("experience_level") or "beginner",
            weekly_available_days=doc_dict.get("weekly_available_days") or 3,
            session_duration_minutes=int(
                doc_dict.get("session_duration_minutes") or 45
            ),
            equipment=doc_dict.get("equipment", []),
            dietary_restrictions=doc_dict.get("dietary_restrictions", []),
            meal_count_per_day=doc_dict.get("meal_count_per_day", 3),
            allergies=doc_dict.get("allergies", []),
        )

        # Continuity with any existing plan
        previous_plan_dict: dict[str, Any] | None = None
        existing_plan_ref = (
            db.collection("users")
            .document(user_id)
            .collection("workout_plans")
            .document("current_plan")
        )
        existing_plan_doc = existing_plan_ref.get()
        if existing_plan_doc.exists:
            previous_plan_dict = existing_plan_doc.to_dict()

        plan = await generate_workout_plan(
            user_profile, db=db, previous_plan_dict=previous_plan_dict
        )

        db.collection("users").document(user_id).collection("workout_plans").document(
            "current_plan"
        ).set(plan.model_dump())

        db.collection("users").document(user_id).update(
            {
                "requires_new_plan": False,
                "plan_status": "ready",
            }
        )

        logger.info("✅ Finished queued workout plan generation for user %s", user_id)

    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            "Error during queued workout generation for %s: %s", user_id, exc, exc_info=True
        )
        try:
            db.collection("users").document(user_id).update(
                {
                    "requires_new_plan": False,
                    "plan_status": "error_generation",
                }
            )
        except Exception:
            # Avoid crashing the worker due to update errors
            logger.exception("Failed to update plan_status after error for %s", user_id)


# ── Public endpoints ─────────────────────────────────────────────────


@router.post("/plan/request", response_model=WorkoutPlanStatus)
async def request_workout_plan(
    req: WorkoutPlanRequest, background_tasks: BackgroundTasks
):
    """
    Queue a new workout plan generation for the given user.

    This endpoint returns quickly with status=queued while the actual Gemini
    call + Firestore writes happen in a background task.
    """
    if not req.user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required")

    db = get_db()
    user_doc = db.collection("users").document(req.user_id).get()
    if not user_doc.exists:
        raise HTTPException(
            status_code=404,
            detail=f"No Firestore user document found for id={req.user_id}",
        )

    # Mark as queued so the app can show a generating state even before plan exists.
    db.collection("users").document(req.user_id).update(
        {
            "requires_new_plan": True,
            "plan_status": "queued",
        }
    )

    background_tasks.add_task(_generate_and_save_plan, req.user_id)

    return WorkoutPlanStatus(
        status="queued",
        message="Workout plan generation has been queued.",
    )

