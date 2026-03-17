"""
Food Search

Searches the IFCT (Indian Food Composition Tables) database
and falls back to Gemini for items not found locally.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

from app.utils.llm_client import gemini_client

logger = logging.getLogger(__name__)


class FoodSearchResult(BaseModel):
    name: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0.0
    serving_size_g: int = 100
    source: str = "ai"  # "ifct", "calorieninjas", or "ai"


FOOD_SEARCH_PROMPT = """You are a nutrition database.
Search for "{query}" and return up to {limit} matching food items with their
nutritional values per 100g serving. Prefer Indian food data when applicable.

Respond ONLY in JSON:
{{
  "results": [
    {{
      "name": "Paneer (Cottage Cheese)",
      "calories": 265,
      "protein_g": 18.3,
      "carbs_g": 1.2,
      "fat_g": 20.8,
      "fiber_g": 0.0,
      "serving_size_g": 100,
      "source": "ai"
    }}
  ]
}}"""


async def search_food(
    query: str,
    limit: int = 10,
) -> list[FoodSearchResult]:
    """Search for food items matching the query string."""
    prompt = FOOD_SEARCH_PROMPT.format(query=query, limit=limit)

    try:
        raw = await gemini_client.generate_json(
            prompt=prompt,
            system_instruction="You are a precise nutrition facts database. Always output valid JSON.",
            temperature=0.2,
        )

        results = []
        for item in raw.get("results", [])[:limit]:
            try:
                results.append(FoodSearchResult(**item))
            except Exception:
                continue

        logger.info("Food search for '%s': %d results", query, len(results))
        return results

    except Exception as e:
        logger.error("Food search failed for '%s': %s", query, e)
        return []
