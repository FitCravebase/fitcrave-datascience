"""
Food Search

Searches for food items and their nutritional data from:
1. IFCT (Indian Food Composition Table) — self-hosted in data/ifct_foods.json
2. CalorieNinjas API — external fallback for items not in IFCT

Used for manual meal logging.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class FoodItem(BaseModel):
    """Nutritional data for a single food item."""

    name: str
    serving_size_g: float
    calories_per_serving: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0.0
    source: str  # "ifct" or "calorieninjas"


# ------------------------------------------------------------------
# IFCT (Indian Food Composition Table) — Local Database
# ------------------------------------------------------------------
_ifct_cache: list[dict[str, Any]] = []


async def load_ifct_database() -> None:
    """
    Load the IFCT food database from data/ifct_foods.json into memory.

    Called once at application startup.

    TODO: Load and parse the JSON file.
          The IFCT dataset from NIN Hyderabad contains ~600 Indian foods
          with detailed macro and micronutrient data.
    """
    global _ifct_cache
    # TODO: Load from app/engines/nutrition/data/ifct_foods.json
    pass


async def search_ifct(query: str, limit: int = 10) -> list[FoodItem]:
    """
    Search the IFCT database for matching food items.

    Uses fuzzy string matching to handle variations in food names
    (e.g., "daal" matches "dal", "chapati" matches "chapathi").

    TODO: Implement fuzzy search over _ifct_cache.
    """
    return []


# ------------------------------------------------------------------
# CalorieNinjas API — External Fallback
# ------------------------------------------------------------------
async def search_calorieninjas(query: str) -> list[FoodItem]:
    """
    Search CalorieNinjas API for nutritional data.

    Used as a fallback when food is not found in IFCT.

    API: https://calorieninjas.com/api
    Endpoint: GET https://api.calorieninjas.com/v1/nutrition?query={query}

    TODO: Implement httpx call to CalorieNinjas API.
    """
    return []


# ------------------------------------------------------------------
# Unified Search
# ------------------------------------------------------------------
async def search_food(query: str, limit: int = 10) -> list[FoodItem]:
    """
    Search for food items across all sources.

    Priority: IFCT first (Indian-specific), then CalorieNinjas fallback.

    Returns:
        Combined and deduplicated list of matching food items.
    """
    results = await search_ifct(query, limit=limit)

    # If IFCT has few results, supplement with CalorieNinjas
    if len(results) < 3:
        external = await search_calorieninjas(query)
        results.extend(external)

    return results[:limit]
