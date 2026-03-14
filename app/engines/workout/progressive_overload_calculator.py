"""
Progressive Overload Calculator
================================
Reads a user's recent workout_logs from Firestore and produces a
per-exercise weight recommendation for the next plan generation.

Algorithm  (Double Progression Model — evidence-based standard used in
Stronger By Science, NSCA guidelines, and most periodization literature):

  IF all sets were completed at or above prescribed reps → increase weight
    · Upper-body compound / isolation: +2.5 kg
    · Lower-body compound             : +5.0 kg

  IF user completed all sets but failed reps on any set → keep same weight

  IF user failed to complete all sets for 2+ consecutive sessions → deload 10%

Strength Standards (Population-Based Benchmarks):
  Source: Lander (1984) + ExRx.net + Symmetric Strength (2023)
  Expressed as a ratio of bodyweight. Used for first-plan weight prescription.
"""

import logging
from typing import Dict, Optional
from google.cloud import firestore  # type: ignore

logger = logging.getLogger(__name__)


# ── Strength Standards ─────────────────────────────────────────────────────
# Format: exercise_name_slug -> { level: bw_multiplier }
# These multipliers are applied to the user's bodyweight to get a
# conservative starting weight for first-time plans.
# Source: ExRx.net Strength Standards + Symmetric Strength (2023).

STRENGTH_STANDARDS: Dict[str, Dict[str, float]] = {
    # Chest
    "barbell bench press":      {"beginner": 0.50, "intermediate": 0.75, "advanced": 1.00},
    "dumbbell bench press":     {"beginner": 0.20, "intermediate": 0.35, "advanced": 0.50},
    "incline bench press":      {"beginner": 0.40, "intermediate": 0.65, "advanced": 0.85},
    "push-up":                  {"beginner": 0.00, "intermediate": 0.00, "advanced": 0.00},  # bodyweight

    # Back
    "barbell row":              {"beginner": 0.45, "intermediate": 0.70, "advanced": 0.95},
    "dumbbell row":             {"beginner": 0.20, "intermediate": 0.35, "advanced": 0.50},
    "lat pulldown":             {"beginner": 0.55, "intermediate": 0.80, "advanced": 1.00},
    "pull-up":                  {"beginner": 0.00, "intermediate": 0.00, "advanced": 0.00},  # bodyweight
    "seated cable row":         {"beginner": 0.45, "intermediate": 0.70, "advanced": 0.90},

    # Legs
    "barbell squat":            {"beginner": 0.75, "intermediate": 1.25, "advanced": 1.75},
    "goblet squat":             {"beginner": 0.20, "intermediate": 0.35, "advanced": 0.50},
    "leg press":                {"beginner": 1.00, "intermediate": 1.50, "advanced": 2.20},
    "deadlift":                 {"beginner": 1.00, "intermediate": 1.50, "advanced": 2.00},
    "romanian deadlift":        {"beginner": 0.75, "intermediate": 1.10, "advanced": 1.50},
    "leg curl":                 {"beginner": 0.35, "intermediate": 0.55, "advanced": 0.75},
    "leg extension":            {"beginner": 0.40, "intermediate": 0.65, "advanced": 0.85},

    # Shoulders
    "overhead press":           {"beginner": 0.35, "intermediate": 0.55, "advanced": 0.70},
    "dumbbell shoulder press":  {"beginner": 0.15, "intermediate": 0.25, "advanced": 0.35},
    "lateral raise":            {"beginner": 0.05, "intermediate": 0.10, "advanced": 0.15},
    "face pull":                {"beginner": 0.20, "intermediate": 0.35, "advanced": 0.50},

    # Arms
    "barbell curl":             {"beginner": 0.25, "intermediate": 0.40, "advanced": 0.55},
    "dumbbell curl":            {"beginner": 0.10, "intermediate": 0.18, "advanced": 0.25},
    "tricep pushdown":          {"beginner": 0.25, "intermediate": 0.40, "advanced": 0.55},
    "skull crusher":            {"beginner": 0.20, "intermediate": 0.35, "advanced": 0.50},

    # Core
    "plank":                    {"beginner": 0.00, "intermediate": 0.00, "advanced": 0.00},
    "cable crunch":             {"beginner": 0.20, "intermediate": 0.35, "advanced": 0.50},
}

# Increment to apply per progressive overload cycle (in kg)
_UPPER_BODY_INCREMENT_KG = 2.5
_LOWER_BODY_INCREMENT_KG = 5.0

_LOWER_BODY_EXERCISES = {"squat", "leg press", "deadlift", "lunge", "leg curl", "leg extension"}


def _is_lower_body(exercise_name: str) -> bool:
    name_lower = exercise_name.lower()
    return any(lb in name_lower for lb in _LOWER_BODY_EXERCISES)


def get_starting_weight(
    exercise_name: str,
    weight_kg: float,
    experience_level: str,
) -> float:
    """
    Return a recommended starting weight (kg) for an exercise based on
    the user's bodyweight and experience level.

    Uses the STRENGTH_STANDARDS lookup table. Falls back to a conservative
    generic estimate if the exercise is not in the table.
    """
    name_lower = exercise_name.lower().strip()
    exp = experience_level.lower()
    if exp not in ("beginner", "intermediate", "advanced"):
        exp = "beginner"

    # Exact match first
    if name_lower in STRENGTH_STANDARDS:
        multiplier = STRENGTH_STANDARDS[name_lower][exp]
        return round(multiplier * weight_kg / 2.5) * 2.5  # Round to nearest 2.5 kg

    # Partial / substring match
    for key, levels in STRENGTH_STANDARDS.items():
        if key in name_lower or name_lower in key:
            multiplier = levels[exp]
            return round(multiplier * weight_kg / 2.5) * 2.5

    # Generic fallback — conservative defaults
    generic = {"beginner": 0.30, "intermediate": 0.50, "advanced": 0.70}[exp]
    return round(generic * weight_kg / 2.5) * 2.5


def compute_overload_weights(
    uid: str,
    db: firestore.Client,
) -> Dict[str, float]:
    """
    Reads the last 4 weeks of workout_logs for a user and returns a dict of:
        { exercise_name_lower -> recommended_weight_kg }

    Uses the Double Progression model:
    - All sets completed → increment
    - Any set failed → keep same weight
    - 2 consecutive failures → deload 10%
    """
    from datetime import datetime, timedelta

    weights: Dict[str, float] = {}
    consecutive_failures: Dict[str, int] = {}

    today = datetime.utcnow()
    # Collect last 28 days of log document IDs
    date_keys = [
        (today - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(28)
    ]

    logs = []
    for date_key in date_keys:
        doc_ref = db.collection("users").document(uid).collection("workout_logs").document(date_key)
        doc = doc_ref.get()
        if doc.exists:
            logs.append(doc.to_dict())

    # Process logs oldest → newest to correctly track consecutive failures
    for log in reversed(logs):
        for ex in log.get("exercises", []):
            name = ex.get("exercise_name", "").strip().lower()
            ex_sets = ex.get("sets", [])
            if not ex_sets:
                continue

            all_completed = all(s.get("completed", False) for s in ex_sets)
            last_weight = max(
                (s.get("weight_kg", 0.0) for s in ex_sets),
                default=0.0
            )

            if last_weight == 0.0:
                continue  # Bodyweight exercise, skip

            if all_completed:
                consecutive_failures[name] = 0
                # Progressive overload
                increment = _LOWER_BODY_INCREMENT_KG if _is_lower_body(name) else _UPPER_BODY_INCREMENT_KG
                weights[name] = last_weight + increment
            else:
                consecutive_failures[name] = consecutive_failures.get(name, 0) + 1
                if consecutive_failures[name] >= 2:
                    # Deload: reduce by 10%
                    weights[name] = round((last_weight * 0.9) / 2.5) * 2.5
                    logger.info(f"Deload applied for '{name}': {last_weight} → {weights[name]} kg")
                    consecutive_failures[name] = 0
                else:
                    weights[name] = last_weight  # Stay at same weight

    return weights
