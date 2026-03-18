"""
Grocery List Generator

Extracts unique ingredients from a weekly meal plan,
groups them by category, and estimates quantities.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.database import grocery_lists_collection
from app.utils.llm_client import gemini_client

logger = logging.getLogger(__name__)


GROCERY_SYSTEM = """You are FitCrave's meal planning assistant.
Generate practical grocery lists from Indian meal plans.
Group items by category and estimate realistic quantities for Indian kitchens.
Always include common Indian staples that are assumed (spices, oil, salt)."""


GROCERY_PROMPT = """Generate a weekly grocery list from this meal plan.

## Meal Plan (7 days)
{meal_plan_summary}

## Instructions
1. Extract all unique ingredients
2. Combine duplicate ingredients and sum their quantities
3. Group by grocery category
4. Add common pantry staples if not already listed
5. Estimate realistic quantities (in grams or pieces for Indian markets)

Respond in JSON:
{{
  "categories": [
    {{
      "name": "Vegetables",
      "items": [
        {{"name": "Onions", "quantity": "1 kg", "estimated_cost_inr": 40}},
        {{"name": "Tomatoes", "quantity": "500 g", "estimated_cost_inr": 30}}
      ]
    }},
    {{
      "name": "Proteins",
      "items": [...]
    }}
  ],
  "estimated_total_cost_inr": 2500,
  "tips": ["Buy seasonal vegetables to save money"]
}}"""


async def generate_grocery_list(
    meal_plans: list[dict[str, Any]],
    user_id: str,
) -> dict[str, Any]:
    """
    Generate a grocery list from meal plans.

    Args:
        meal_plans: List of daily meal plan dicts (each has "meals" key).
        user_id: For storing the result.

    Returns:
        Structured grocery list grouped by category.
    """
    # Build a concise summary of all meals for the prompt
    all_meals = []
    for day_plan in meal_plans:
        for meal in day_plan.get("meals", []):
            ingredients = ", ".join(meal.get("ingredients", []))
            all_meals.append(
                f"- {meal.get('name', 'Unknown')}: {ingredients} ({meal.get('portion_grams', 0)}g)"
            )

    meal_summary = "\n".join(all_meals) if all_meals else "No meals provided"

    prompt = GROCERY_PROMPT.format(meal_plan_summary=meal_summary)

    result = await gemini_client.generate_json(
        prompt=prompt,
        system_instruction=GROCERY_SYSTEM,
        temperature=0.3,
    )

    # Persist
    doc = {
        "user_id": user_id,
        "categories": result.get("categories", []),
        "estimated_total_cost_inr": result.get("estimated_total_cost_inr", 0),
        "tips": result.get("tips", []),
        "created_at": datetime.now(timezone.utc),
    }
    await grocery_lists_collection().insert_one(doc)

    logger.info(
        "Grocery list generated for user %s: %d categories",
        user_id, len(result.get("categories", [])),
    )
    return result
