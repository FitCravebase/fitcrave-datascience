"""
Mess Menu Analyzer

Uses Gemini Vision to read a physical mess menu, extract the available food options,
and generate a recommended Breakfast, Lunch, and Dinner plan based on the user's
daily calorie and macronutrient targets, as well as their dietary preferences.
"""

import logging
from typing import Any

from pydantic import BaseModel

from app.utils.llm_client import gemini_client

logger = logging.getLogger(__name__)


class MealRecommendationItem(BaseModel):
    name: str
    quantity_grams: int
    approximate_measure: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float

class MealRecommendationGroup(BaseModel):
    items: list[MealRecommendationItem]
    total_calories: int
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float

class DailyMessPlan(BaseModel):
    breakfast: MealRecommendationGroup
    lunch: MealRecommendationGroup
    dinner: MealRecommendationGroup
    daily_calories: int
    daily_protein_g: float
    daily_carbs_g: float
    daily_fat_g: float
    notes: str

class WeeklyMessPlanResult(BaseModel):
    monday: DailyMessPlan
    tuesday: DailyMessPlan
    wednesday: DailyMessPlan
    thursday: DailyMessPlan
    friday: DailyMessPlan
    saturday: DailyMessPlan
    sunday: DailyMessPlan
    weekly_notes: str


def build_mess_menu_prompt(
    targets: dict[str, Any],
    diet_preference: str,
    additional_items: list[str] = None
) -> str:
    """Builds the prompt instructing Gemini how to parse the weekly menu and generate the plan."""
    
    # Extract user constraints
    t_cals = targets.get("calories", 2000)
    t_prot = targets.get("protein_g", 150)
    t_carb = targets.get("carbs_g", 250)
    t_fat = targets.get("fat_g", 70)
    
    custom_items_str = ""
    if additional_items and len(additional_items) > 0:
        custom_items_str = f"The user additionally has the following custom food items available that you may incorporate to hit targets: {', '.join(additional_items)}."

    return f"""You are an expert nutritionist AI. The user has provided an image of their weekly mess/cafeteria timetable.
    
Your task is to:
1. Read ALL the available food items from the menu image for ALL SEVEN DAYS.
2. Select the BEST items to form a complete, healthy day of eating across three meals (Breakfast, Lunch, Dinner) for EVERY DAY of the week.
   - You must STRICTLY map the correct food to the correct day as shown in the timetable. Do not suggest a Wednesday item for Monday.
3. The user's dietary preference is: {diet_preference}. You MUST STRICTLY honor this. (e.g., If Vegetarian, DO NOT recommend meat or eggs). 
4. The user's daily macro targets are approximately:
   - Calories: {t_cals}
   - Protein: {t_prot}g 
   - Carbs: {t_carb}g
   - Fats: {t_fat}g
   
{custom_items_str}

Try your best to get the sum of Breakfast, Lunch, and Dinner as close to these daily targets as possible for each day. 
For each item, provide an EXACT `quantity_grams` (e.g., 200) and an `approximate_measure` in natural terms useful to a college student (e.g., "1 bowl", "2 rotis", "1 cup", "1 piece").
Estimate the macros for each item accurately based on the portions.

Return ONLY valid JSON in this exact format (do this for all 7 days: monday, tuesday, wednesday, thursday, friday, saturday, sunday):
{{
  "monday": {{
    "breakfast": {{
      "items": [
        {{
          "name": "Poha",
          "quantity_grams": 150,
          "approximate_measure": "1 moderate bowl",
          "calories": 250,
          "protein_g": 5.0,
          "carbs_g": 40.0,
          "fat_g": 8.0
        }}
      ],
      "total_calories": 250,
      "total_protein_g": 5.0,
      "total_carbs_g": 40.0,
      "total_fat_g": 8.0
    }},
    "lunch": ... ,
    "dinner": ... ,
    "daily_calories": 250,
    "daily_protein_g": 5.0,
    "daily_carbs_g": 40.0,
    "daily_fat_g": 8.0,
    "notes": "Focused on high protein lentils for lunch."
  }},
  "tuesday": {{ ... }},
  "wednesday": {{ ... }},
  "thursday": {{ ... }},
  "friday": {{ ... }},
  "saturday": {{ ... }},
  "sunday": {{ ... }},
  "weekly_notes": "General advice for the week..."
}}
"""

async def analyze_mess_menu(
    image_bytes: bytes,
    targets: dict[str, Any],
    diet_preference: str,
    additional_items: list[str] = None,
    mime_type: str = "image/jpeg"
) -> WeeklyMessPlanResult:
    """
    Analyzes the mess menu image using Gemini Vision to provide a full 7-day meal plan.
    """
    
    prompt = build_mess_menu_prompt(targets, diet_preference, additional_items)
    
    raw = await gemini_client.analyze_image(
        image_bytes=image_bytes,
        prompt=prompt,
        mime_type=mime_type,
    )

    try:
        # Pydantic will handle parsing and validation
        result = WeeklyMessPlanResult(**raw)
        logger.info(
            "Weekly Mess Menu analyzed successfully. Targets: Calories %d, Protein %dg", 
            targets.get("calories", 0), targets.get("protein_g", 0)
        )
        return result
    except Exception as e:
        logger.error(f"Failed to parse Weekly Mess Menu LLM output: {raw} - Error: {e}")
        # Re-raise to be handled by the router
        raise ValueError("Failed to generate a valid weekly plan from the provided menu image.")
