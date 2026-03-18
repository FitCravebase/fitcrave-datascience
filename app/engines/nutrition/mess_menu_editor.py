import logging
from typing import Any
from pydantic import BaseModel
from app.utils.llm_client import gemini_client
from app.engines.nutrition.mess_menu_analyzer import WeeklyMessPlanResult

logger = logging.getLogger(__name__)

def build_edit_prompt(current_plan: dict, context: str) -> str:
    return f"""You are an expert nutritionist AI. Here is the user's current 7-day meal plan in JSON:

{current_plan}

The user wants to add an item. The user's instruction is: "{context}".

Your task is to:
1. Identify the macronutrients and calories for the new item.
2. Add this new item to the `items` list of the specified day's specified meal. Make sure to provide `quantity_grams`, `approximate_measure`, `calories`, `protein_g`, `carbs_g`, and `fat_g` for the new item.
3. Recalculate the `total_calories`, `total_protein_g`, `total_carbs_g`, and `total_fat_g` for that specific meal.
4. Recalculate the `daily_calories`, `daily_protein_g`, `daily_carbs_g`, and `daily_fat_g` for that day.
5. Output the FULL UPDATED 7-day meal plan strictly in the identical JSON format as provided, with the modifications applied. Do not change the other days or meals. Return ONLY valid JSON.
"""

async def edit_mess_menu(
    current_plan: dict,
    context: str
) -> dict:
    prompt = build_edit_prompt(current_plan, context)
    
    try:
        result_dict = await gemini_client.generate_json(
            prompt=prompt,
            system_instruction="You are a JSON-only nutrition API. You must strictly output the modified WeeklyMessPlanResult JSON."
        )
        # Validate schema
        WeeklyMessPlanResult(**result_dict)
        return result_dict
    except Exception as e:
        logger.error(f"Failed to edit Weekly Mess Menu LLM output - Error: {e}")
        raise ValueError("Failed to update the weekly plan with the custom item.")
