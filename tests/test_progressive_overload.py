"""
Tests for the progressive overload engine.
"""

from app.engines.workout.progressive_overload import check_progression


class TestProgressiveOverload:
    """Test progression detection logic."""

    def test_no_progression_insufficient_sessions(self):
        result = check_progression(
            exercise_id="barbell_bench_press",
            exercise_name="Barbell Bench Press",
            equipment_type="barbell",
            target_reps=10,
            target_rpe=8.0,
            recent_sessions=[
                {"sets": [{"reps": 10, "weight": 60, "rpe": 7.5}]}
            ],
            consecutive_sessions_required=2,
        )
        assert result is None

    def test_progression_achieved(self):
        result = check_progression(
            exercise_id="barbell_bench_press",
            exercise_name="Barbell Bench Press",
            equipment_type="barbell",
            target_reps=10,
            target_rpe=8.0,
            recent_sessions=[
                {"sets": [{"reps": 10, "weight": 60, "rpe": 7.5}, {"reps": 10, "weight": 60, "rpe": 8.0}]},
                {"sets": [{"reps": 10, "weight": 60, "rpe": 7.5}, {"reps": 10, "weight": 60, "rpe": 8.0}]},
            ],
            consecutive_sessions_required=2,
        )
        assert result is not None
        assert result.recommended_weight == 62.5  # 60 + 2.5kg barbell increment

    def test_no_progression_rpe_too_high(self):
        result = check_progression(
            exercise_id="barbell_squat",
            exercise_name="Barbell Back Squat",
            equipment_type="barbell",
            target_reps=8,
            target_rpe=7.5,
            recent_sessions=[
                {"sets": [{"reps": 8, "weight": 80, "rpe": 9.0}]},
                {"sets": [{"reps": 8, "weight": 80, "rpe": 8.5}]},
            ],
            consecutive_sessions_required=2,
        )
        assert result is None

    def test_bodyweight_progression(self):
        result = check_progression(
            exercise_id="push_ups",
            exercise_name="Push Ups",
            equipment_type="bodyweight",
            target_reps=15,
            target_rpe=7.0,
            recent_sessions=[
                {"sets": [{"reps": 15, "weight": 0, "rpe": 6.5}]},
                {"sets": [{"reps": 15, "weight": 0, "rpe": 7.0}]},
            ],
            consecutive_sessions_required=2,
        )
        assert result is not None
        assert result.recommended_reps == "17"  # 15 + 2 reps
        assert result.recommended_weight == 0
