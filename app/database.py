"""
MongoDB Async Client

Provides a singleton motor client and typed collection accessors
for the FitCrave AI backend.
"""

from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    """Initialize the motor client and verify connectivity."""
    global _client, _db

    logger.info("Connecting to MongoDB at %s …", settings.MONGODB_URI)
    _client = AsyncIOMotorClient(settings.MONGODB_URI)
    _db = _client[settings.MONGODB_DB_NAME]

    # Quick ping to validate the connection
    await _client.admin.command("ping")
    logger.info("✅ MongoDB connected — database: %s", settings.MONGODB_DB_NAME)


async def close_db() -> None:
    """Gracefully close the motor client."""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        logger.info("🛑 MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    """Return the active database handle (call after connect_db)."""
    if _db is None:
        raise RuntimeError("Database not initialised — call connect_db() first")
    return _db


# ── Collection Accessors ──────────────────────────────────────────


def users_collection():
    """User profiles (extended with nutrition/workout prefs)."""
    return get_db()["users"]


def meal_logs_collection():
    """Individual meal log entries."""
    return get_db()["meal_logs"]


def meal_plans_collection():
    """AI-generated daily meal plans."""
    return get_db()["meal_plans"]


def food_corrections_collection():
    """MealSnap user corrections (for prompt improvement)."""
    return get_db()["food_corrections"]


def grocery_lists_collection():
    """Generated grocery lists."""
    return get_db()["grocery_lists"]
