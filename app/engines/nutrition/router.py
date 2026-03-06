"""
Nutrition Engine — REST API Router

All nutrition-related endpoints: macro targets, meal plans,
meal logging, MealSnap, food search, grocery lists.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.database import users_collection
from app.engines.nutrition.macro_calculator import (
    ActivityLevel,
    FitnessGoal,
    Gender,
    MacroTargets,
    calculate_macro_targets,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response Models ─────────────────────────────────────


class CalculateTargetsRequest(BaseModel):
    weight_kg: float
    height_cm: float
    age: int
    gender: str  # "male" or "female"
    activity_level: str = "moderately_active"
    goal: str = "fat_loss"
    # Optional: if provided, targets are saved to the user's MongoDB document
    user_id: str | None = None
    meal_count: int = 4
    dietary_restrictions: list[str] = []
    allergies: list[str] = []


class GenerateMealPlanRequest(BaseModel):
    user_id: str
    meal_count: int = 4


class AdjustMealPlanRequest(BaseModel):
    user_id: str
    feedback: str


class LogMealRequest(BaseModel):
    user_id: str
    meal_type: str  # "breakfast", "lunch", "dinner", "snack"
    items: list[dict[str, Any]]
    image_url: str | None = None
    ai_confidence: float | None = None
    source: str = "manual"


class MealSnapCorrectionRequest(BaseModel):
    user_id: str
    original_result: dict[str, Any]
    corrections: dict[str, Any]


class GroceryListRequest(BaseModel):
    user_id: str


# ── Macro Targets ─────────────────────────────────────────────────


@router.post("/targets/calculate")
async def calculate_targets(req: CalculateTargetsRequest):
    """Calculate macro targets from user biometrics and goals.

    If ``user_id`` is provided the calculated targets **and** the user's
    biometric data are upserted into MongoDB so that subsequent calls to
    ``/meal-plan/generate`` and ``/targets/{user_id}`` work correctly.
    """
    try:
        gender = Gender(req.gender.lower())
        activity = ActivityLevel(req.activity_level.lower())
        goal = FitnessGoal(req.goal.lower())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {e}")

    targets = calculate_macro_targets(
        weight_kg=req.weight_kg,
        height_cm=req.height_cm,
        age=req.age,
        gender=gender,
        activity_level=activity,
        goal=goal,
    )

    # Persist to MongoDB when user_id is supplied (non-empty)
    if req.user_id and req.user_id.strip():
        targets_snapshot = {
            "calories": targets.target_calories,
            "protein_g": targets.protein_g,
            "carbs_g": targets.carbs_g,
            "fat_g": targets.fat_g,
            "goal": goal.value,
            "explanation": targets.explanation,
        }
        await users_collection().update_one(
            {"firebase_uid": req.user_id},
            {
                "$set": {
                    "firebase_uid": req.user_id,
                    "weight_kg": req.weight_kg,
                    "height_cm": req.height_cm,
                    "age": req.age,
                    "gender": req.gender.lower(),
                    "activity_level": req.activity_level.lower(),
                    "smp_goal": goal.value,
                    "meal_count_per_day": req.meal_count,
                    "dietary_restrictions": req.dietary_restrictions,
                    "allergies": req.allergies,
                    "current_targets": targets_snapshot,
                }
            },
            upsert=True,
        )
        logger.info("Targets calculated and saved for user %s", req.user_id)

    return targets.model_dump()


@router.get("/targets/{user_id}")
async def get_user_targets(user_id: str):
    """Get the user's current cached macro targets."""
    user = await users_collection().find_one(
        {"firebase_uid": user_id},
        {"current_targets": 1, "_id": 0},
    )
    if not user or not user.get("current_targets"):
        raise HTTPException(
            status_code=404,
            detail="No targets found. Calculate targets first.",
        )
    return user["current_targets"]


# ── Meal Plans ────────────────────────────────────────────────────


@router.post("/meal-plan/generate")
async def generate_meal_plan_endpoint(req: GenerateMealPlanRequest):
    """Generate today's AI meal plan."""
    from app.engines.nutrition.meal_planner import (
        generate_meal_plan,
        save_meal_plan,
    )

    # Fetch user profile — create a minimal stub if not yet in MongoDB
    # (this happens when the user completes onboarding but Firestore→MongoDB
    # sync hasn't run yet; targets will be calculated on the fly from defaults)
    user = await users_collection().find_one({"firebase_uid": req.user_id})
    if not user:
        user = {"firebase_uid": req.user_id}

    # Calculate targets (or use cached)
    targets_data = user.get("current_targets")
    if targets_data:
        targets = MacroTargets(
            bmr=0,
            tdee=0,
            target_calories=targets_data["calories"],
            protein_g=targets_data["protein_g"],
            carbs_g=targets_data["carbs_g"],
            fat_g=targets_data["fat_g"],
            goal=FitnessGoal(user.get("smp_goal", user.get("goal", "fat_loss"))),
            explanation="Cached targets",
        )
    else:
        targets = calculate_macro_targets(
            weight_kg=user.get("weight_kg", user.get("weight", 70)),
            height_cm=user.get("height_cm", user.get("height", 170)),
            age=user.get("age", 25),
            gender=Gender(user.get("gender", "male").lower()),
            activity_level=ActivityLevel(user.get("activity_level", "moderately_active")),
            goal=FitnessGoal(user.get("smp_goal", user.get("goal", "fat_loss"))),
        )

    plan = await generate_meal_plan(
        user_context=user,
        targets=targets,
        meal_count=req.meal_count,
    )

    # Save to DB
    plan_id = await save_meal_plan(req.user_id, plan)
    plan["plan_id"] = plan_id

    return plan


@router.get("/meal-plan/{user_id}/today")
async def get_todays_plan(user_id: str):
    """Get today's meal plan (cached). Returns 404 if none exists."""
    from app.engines.nutrition.meal_planner import get_todays_meal_plan

    plan = await get_todays_meal_plan(user_id)
    if not plan:
        raise HTTPException(
            status_code=404,
            detail="No meal plan found for today. Generate one first.",
        )
    return plan


@router.post("/meal-plan/adjust")
async def adjust_meal_plan_endpoint(req: AdjustMealPlanRequest):
    """Adjust today's meal plan based on user feedback."""
    from app.engines.nutrition.meal_planner import (
        adjust_meal_plan,
        get_todays_meal_plan,
        save_meal_plan,
    )

    current = await get_todays_meal_plan(req.user_id)
    if not current:
        raise HTTPException(
            status_code=404,
            detail="No meal plan to adjust. Generate one first.",
        )

    # Get user targets
    user = await users_collection().find_one({"firebase_uid": req.user_id})
    targets_data = user.get("current_targets", {})
    targets = MacroTargets(
        bmr=0, tdee=0,
        target_calories=targets_data.get("calories", 2000),
        protein_g=targets_data.get("protein_g", 150),
        carbs_g=targets_data.get("carbs_g", 200),
        fat_g=targets_data.get("fat_g", 67),
        goal=FitnessGoal(user.get("smp_goal", "fat_loss")),
        explanation="From user profile",
    )

    adjusted = await adjust_meal_plan(current, req.feedback, targets)
    plan_id = await save_meal_plan(req.user_id, adjusted)
    adjusted["plan_id"] = plan_id

    return adjusted


# ── Meal Logging ──────────────────────────────────────────────────


@router.post("/meal-log")
async def log_meal_endpoint(req: LogMealRequest):
    """Log a meal (manual input, MealSnap, or from plan)."""
    from app.engines.nutrition.meal_logger import log_meal

    log_id = await log_meal(
        user_id=req.user_id,
        meal_type=req.meal_type,
        items=req.items,
        image_url=req.image_url,
        ai_confidence=req.ai_confidence,
        source=req.source,
    )
    return {"log_id": log_id, "status": "logged"}


@router.get("/meal-log/{user_id}/today")
async def get_today_logs(user_id: str):
    """Get today's logged meals and daily summary."""
    from app.engines.nutrition.meal_logger import get_daily_logs, get_daily_summary

    logs = await get_daily_logs(user_id)
    summary = await get_daily_summary(user_id)

    return {"logs": logs, "summary": summary}


@router.get("/meal-log/{user_id}/weekly")
async def get_weekly_logs(user_id: str):
    """Get 7-day summary for the weekly analysis chart."""
    from app.engines.nutrition.meal_logger import get_weekly_summary

    return await get_weekly_summary(user_id)


# ── MealSnap ──────────────────────────────────────────────────────


@router.post("/mealsnap/analyze")
async def analyze_mealsnap(
    image: UploadFile = File(...),
):
    """Analyze a food image and return macro estimates."""
    from app.engines.nutrition.meal_snap import analyze_food_image

    contents = await image.read()
    mime_type = image.content_type or "image/jpeg"

    result = await analyze_food_image(contents, mime_type)
    return result.model_dump()


@router.post("/mealsnap/correct")
async def correct_mealsnap(req: MealSnapCorrectionRequest):
    """Apply user correction to a MealSnap result."""
    from app.engines.nutrition.meal_snap import MealSnapResult, apply_user_correction

    original = MealSnapResult(**req.original_result)
    corrected = await apply_user_correction(original, req.corrections, req.user_id)
    return corrected.model_dump()


# ── Food Search ───────────────────────────────────────────────────


@router.get("/food/search")
async def search_food_endpoint(
    q: str = Query(..., description="Search query for food name"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search IFCT + CalorieNinjas for food items."""
    from app.engines.nutrition.food_search import search_food

    results = await search_food(q, limit=limit)
    return [r.model_dump() for r in results]


# ── Grocery List ──────────────────────────────────────────────────


@router.post("/grocery-list/generate")
async def generate_grocery_endpoint(req: GroceryListRequest):
    """Generate a grocery list from recent meal plans."""
    from app.engines.nutrition.grocery_list import generate_grocery_list
    from app.engines.nutrition.meal_planner import get_todays_meal_plan

    # Get the latest available meal plans (today's for now)
    plan = await get_todays_meal_plan(req.user_id)
    if not plan:
        raise HTTPException(
            status_code=404,
            detail="No meal plans found. Generate a meal plan first.",
        )

    result = await generate_grocery_list([plan], req.user_id)
    return result
