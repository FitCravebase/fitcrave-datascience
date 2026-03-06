"""
Meal Logger

CRUD operations for meal logs — tracks what the user actually ate.
Provides daily and weekly summaries for the dashboard and adaptive targets.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from app.database import meal_logs_collection

logger = logging.getLogger(__name__)


async def log_meal(
    user_id: str,
    meal_type: str,
    items: list[dict[str, Any]],
    image_url: str | None = None,
    ai_confidence: float | None = None,
    source: str = "manual",
) -> str:
    """
    Log a meal entry.

    Args:
        user_id: Firebase UID.
        meal_type: "breakfast", "lunch", "dinner", or "snack".
        items: List of food items with macros.
        image_url: Optional MealSnap image URL.
        ai_confidence: Optional AI confidence score.
        source: "manual", "mealsnap", "plan", or "order".

    Returns:
        Inserted document ID as string.
    """
    # Compute totals
    total_calories = sum(item.get("calories", 0) for item in items)
    total_protein = sum(item.get("protein_g", 0) for item in items)
    total_carbs = sum(item.get("carbs_g", 0) for item in items)
    total_fat = sum(item.get("fat_g", 0) for item in items)

    # Tag each item with its source
    for item in items:
        item.setdefault("source", source)

    doc = {
        "user_id": user_id,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "meal_type": meal_type,
        "items": items,
        "total_calories": total_calories,
        "total_protein_g": total_protein,
        "total_carbs_g": total_carbs,
        "total_fat_g": total_fat,
        "image_url": image_url,
        "ai_confidence": ai_confidence,
        "user_corrected": False,
        "created_at": datetime.now(timezone.utc),
    }

    result = await meal_logs_collection().insert_one(doc)
    logger.info(
        "Logged %s for user %s: %d kcal, %dP/%dC/%dF",
        meal_type, user_id, total_calories,
        int(total_protein), int(total_carbs), int(total_fat),
    )
    return str(result.inserted_id)


async def get_daily_logs(user_id: str, date: str | None = None) -> list[dict[str, Any]]:
    """Get all meal logs for a user on a given date (default: today)."""
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    cursor = meal_logs_collection().find(
        {"user_id": user_id, "date": date},
        {"_id": 0},
    ).sort("created_at", 1)

    return await cursor.to_list(length=50)


def _compute_summary(logs: list[dict[str, Any]], date_str: str) -> dict[str, Any]:
    """Helper to compute nutrition summary from a list of logs."""
    total_calories = sum(log.get("total_calories", 0) for log in logs)
    total_protein = sum(log.get("total_protein_g", 0) for log in logs)
    total_carbs = sum(log.get("total_carbs_g", 0) for log in logs)
    total_fat = sum(log.get("total_fat_g", 0) for log in logs)

    # Per-meal breakdown
    by_meal = {}
    for log in logs:
        mt = log.get("meal_type", "other")
        if mt not in by_meal:
            by_meal[mt] = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
        by_meal[mt]["calories"] += log.get("total_calories", 0)
        by_meal[mt]["protein_g"] += log.get("total_protein_g", 0)
        by_meal[mt]["carbs_g"] += log.get("total_carbs_g", 0)
        by_meal[mt]["fat_g"] += log.get("total_fat_g", 0)

    return {
        "date": date_str,
        "total_calories": total_calories,
        "total_protein_g": round(total_protein, 1),
        "total_carbs_g": round(total_carbs, 1),
        "total_fat_g": round(total_fat, 1),
        "meals_logged": len(logs),
        "by_meal": by_meal,
    }


async def get_daily_summary(user_id: str, date: str | None = None) -> dict[str, Any]:
    """
    Get aggregated daily nutrition summary.
    Used by the calorie tracker widget.
    """
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
    logs = await get_daily_logs(user_id, date)
    return _compute_summary(logs, date)


async def get_weekly_summary(user_id: str) -> list[dict[str, Any]]:
    """
    Get daily summaries for the past 7 days.
    Used by the weekly analysis chart widget.
    Optimized to use a single batch query.
    """
    today = datetime.now(timezone.utc)
    start_date = (today - timedelta(days=6)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    cursor = meal_logs_collection().find(
        {"user_id": user_id, "date": {"$gte": start_date, "$lte": end_date}},
        {"_id": 0},
    ).sort("created_at", 1)
    
    all_logs = await cursor.to_list(length=1000)

    # Group logs by date
    logs_by_date = {}
    for log in all_logs:
        logs_by_date.setdefault(log["date"], []).append(log)

    summaries = []
    for i in range(6, -1, -1):  # 6 days ago → today
        day = today - timedelta(days=i)
        date_str = day.strftime("%Y-%m-%d")
        
        day_logs = logs_by_date.get(date_str, [])
        summary = _compute_summary(day_logs, date_str)
        summary["day_label"] = day.strftime("%a")  # Mon, Tue, etc.
        summaries.append(summary)

    return summaries


async def delete_meal_log(user_id: str, log_id: str) -> bool:
    """Delete a specific meal log entry."""
    from bson import ObjectId
    result = await meal_logs_collection().delete_one(
        {"_id": ObjectId(log_id), "user_id": user_id}
    )
    return result.deleted_count > 0
