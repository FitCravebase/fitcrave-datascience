import pytest
from app.engines.workout.exercise_db import exercise_db

def test_exercise_db_loads_data():
    """Test that the database successfully loads exercises from JSON."""
    assert len(exercise_db.exercises) > 0, "No exercises loaded from JSON."

def test_exercise_db_filtering_by_target():
    """Test filtering by a specific target muscle."""
    # The JSON uses muscles like 'abdominals', 'chest', etc.
    results = exercise_db.filter_exercises(target_muscle="abdominals")
    assert len(results) > 0
    for ex in results:
        assert any("abdominals" in m.lower() for m in ex.primaryMuscles)

def test_exercise_db_filtering_by_equipment():
    """Test filtering by required equipment."""
    results = exercise_db.filter_exercises(equipment="barbell")
    assert len(results) > 0
    for ex in results:
        assert ex.equipment and ex.equipment.lower() == "barbell"

def test_exercise_db_filtering_by_name():
    """Test partial name matching."""
    results = exercise_db.filter_exercises(name_query="squat")
    assert len(results) > 0
    # At least one result should have squat in the name
    assert any("squat" in ex.name.lower() for ex in results)

def test_exercise_db_limit():
    """Test that the limit parameter works."""
    results = exercise_db.filter_exercises(limit=5)
    assert len(results) <= 5
