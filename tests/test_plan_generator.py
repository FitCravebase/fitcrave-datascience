import pytest
from app.engines.workout.plan_generator import suggest_split_type

def test_suggest_split_type_beginner():
    """Test that beginners always get full body."""
    assert suggest_split_type(5, "beginner") == "Full Body"
    assert suggest_split_type(2, "beginner") == "Full Body"

def test_suggest_split_type_intermediate_3_days():
    """Test 3 days or less gives full body."""
    assert suggest_split_type(3, "intermediate") == "Full Body"
    assert suggest_split_type(2, "advanced") == "Full Body"

def test_suggest_split_type_intermediate_4_days():
    """Test 4 days gives upper/lower."""
    assert suggest_split_type(4, "intermediate") == "Upper/Lower"
    assert suggest_split_type(4, "advanced") == "Upper/Lower"

def test_suggest_split_type_intermediate_5_days():
    """Test 5+ days gives push/pull/legs."""
    assert suggest_split_type(5, "intermediate") == "Push/Pull/Legs"
    assert suggest_split_type(6, "advanced") == "Push/Pull/Legs"
