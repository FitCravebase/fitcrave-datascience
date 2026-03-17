"""
Workout Engine — Exercise Database

Handles loading and querying the local JSON database of exercises.
This ensures the LLM only generates workout plans using exercises that
we actually have data (instructions, muscles, equipment) for.
"""

import json
import logging
from pathlib import Path
from typing import List

from app.models.workout import Exercise

logger = logging.getLogger(__name__)

# Path to the downloaded exercises.json
DB_PATH = Path(__file__).parent / "data" / "exercises.json"


class ExerciseDatabase:
    """
    In-memory database of all available exercises loaded from JSON.
    """

    def __init__(self):
        self.exercises: List[Exercise] = []
        self._load_database()

    def _load_database(self) -> None:
        """Loads and parses the JSON file into Pydantic models."""
        if not DB_PATH.exists():
            logger.error(f"Failed to find exercise database at {DB_PATH}")
            return

        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self.exercises = [Exercise(**item) for item in data]
            logger.info(f"Successfully loaded {len(self.exercises)} exercises into memory.")
        except Exception as e:
            logger.error(f"Error loading exercise database: {str(e)}")

    def get_all_equipment(self) -> List[str]:
        """Returns a unique list of all equipment requirements."""
        return sorted({ex.equipment for ex in self.exercises})

    def get_all_target_muscles(self) -> List[str]:
        """Returns a unique list of all primary target muscles."""
        muscles = set()
        for ex in self.exercises:
            muscles.update(ex.primaryMuscles)
        return sorted(list(muscles))

    def get_all_categories(self) -> List[str]:
        """Returns a unique list of all categories."""
        return sorted({ex.category for ex in self.exercises})

    def filter_exercises(
        self,
        target_muscle: str = None,
        category: str = None,
        equipment: str = None,
        name_query: str = None,
        limit: int = 50
    ) -> List[Exercise]:
        """
        Retrieves a filtered list of exercises.
        
        Args:
            target_muscle: Exact match for a specific muscle (e.g., 'pectorals')
            body_part: Exact match for a broad region (e.g., 'chest')
            equipment: Exact match for required equipment (e.g., 'barbell')
            name_query: Partial string match (case-insensitive) on the name
            limit: Maximum number of results to return
        """
        results = self.exercises

        if target_muscle:
            results = [ex for ex in results if any(target_muscle.lower() in m.lower() for m in ex.primaryMuscles)]
        
        if category:
            results = [ex for ex in results if ex.category.lower() == category.lower()]

        if equipment:
            results = [ex for ex in results if ex.equipment and ex.equipment.lower() == equipment.lower()]

        if name_query:
            query = name_query.lower()
            results = [ex for ex in results if query in ex.name.lower()]

        return results[:limit]

# Initialize a global instance to be imported and used by the orchestrator/engines
# so that the JSON is only loaded from disk once on startup.
exercise_db = ExerciseDatabase()
