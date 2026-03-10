"""
Food Search

Searches for food items and their nutritional data from:
1. IFCT (Indian Food Composition Table) — self-hosted in data/ifct_foods.json
2. CalorieNinjas API — external fallback for items not in IFCT

Used for manual meal logging and building the nutrition knowledge base.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel
from rapidfuzz import fuzz, process

from app.config import settings

logger = logging.getLogger(__name__)


class FoodItem(BaseModel):
    """Nutritional data for a single food item."""

    name: str
    hindi_name: str | None = None
    category: str | None = None
    serving_size_g: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0.0
    source: str  # "ifct" or "calorieninjas"


# ------------------------------------------------------------------
# IFCT (Indian Food Composition Table) — Local Database
# ------------------------------------------------------------------
_ifct_cache: list[dict[str, Any]] = []
_ifct_names: list[str] = []  # Pre-built list for rapidfuzz


async def load_ifct_database() -> None:
    """
    Load the IFCT food database from data/ifct_foods.json into memory.
    Called once at application startup.
    """
    global _ifct_cache, _ifct_names

    data_path = Path(__file__).parent / "data" / "ifct_foods.json"
    if not data_path.exists():
        logger.warning("IFCT database not found at %s", data_path)
        return

    with open(data_path, encoding="utf-8") as f:
        _ifct_cache = json.load(f)

    # Build a combined search index: "English Name | Hindi Name"
    _ifct_names = []
    for item in _ifct_cache:
        parts = [item["name"]]
        if item.get("hindi_name"):
            parts.append(item["hindi_name"])
        _ifct_names.append(" | ".join(parts))

    logger.info("✅ IFCT database loaded: %d foods", len(_ifct_cache))


async def search_ifct(query: str, limit: int = 10) -> list[FoodItem]:
    """
    Search the IFCT database for matching food items.
    Uses rapidfuzz for fuzzy string matching to handle variations
    (e.g., "daal" matches "dal", "chapati" matches "chapathi").
    """
    if not _ifct_cache:
        return []

    # Use token_set_ratio for better matching of partial / reordered terms
    matches = process.extract(
        query,
        _ifct_names,
        scorer=fuzz.token_set_ratio,
        limit=limit,
        score_cutoff=45,  # minimum match quality
    )

    results: list[FoodItem] = []
    for match_text, score, idx in matches:
        item = _ifct_cache[idx]
        results.append(
            FoodItem(
                name=item["name"],
                hindi_name=item.get("hindi_name"),
                category=item.get("category"),
                serving_size_g=item["serving_size_g"],
                calories=item["calories"],
                protein_g=item["protein_g"],
                carbs_g=item["carbs_g"],
                fat_g=item["fat_g"],
                fiber_g=item.get("fiber_g", 0.0),
                source="ifct",
            )
        )
    return results


# ------------------------------------------------------------------
# CalorieNinjas API — External Fallback
# ------------------------------------------------------------------
async def search_calorieninjas(query: str) -> list[FoodItem]:
    """
    Search CalorieNinjas API for nutritional data.
    Used as a fallback when food is not found in IFCT.
    """
    api_key = settings.CALORIENINJA_API_KEY
    if not api_key:
        logger.debug("CalorieNinjas API key not set — skipping external search")
        return []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.calorieninjas.com/v1/nutrition",
                params={"query": query},
                headers={"X-Api-Key": api_key},
            )
            response.raise_for_status()
            data = response.json()

        results: list[FoodItem] = []
        for item in data.get("items", []):
            results.append(
                FoodItem(
                    name=item.get("name", query).title(),
                    serving_size_g=item.get("serving_size_g", 100),
                    calories=item.get("calories", 0),
                    protein_g=item.get("protein_g", 0),
                    carbs_g=item.get("carbs_g", 0),
                    fat_g=item.get("fat_g", 0),
                    fiber_g=item.get("fiber_g", 0),
                    source="calorieninjas",
                )
            )
        return results

    except httpx.HTTPError as e:
        logger.error("CalorieNinjas API error: %s", e)
        return []


# ------------------------------------------------------------------
# Unified Search
# ------------------------------------------------------------------
async def search_food(query: str, limit: int = 10) -> list[FoodItem]:
    """
    Search for food items across all sources.
    Priority: IFCT first (Indian-specific), then CalorieNinjas fallback.
    """
    results = await search_ifct(query, limit=limit)

    # If IFCT has few results, supplement with CalorieNinjas
    if len(results) < 3:
        external = await search_calorieninjas(query)
        results.extend(external)

    return results[:limit]
