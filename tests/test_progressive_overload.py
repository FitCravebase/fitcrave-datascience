from app.engines.workout.progressive_overload import check_progression, ProgressionRecommendation

def test_progression_warranted():
    """Test that it recommends a weight increase when target reps are met at/below RPE limit."""
    recent_sessions = [
        {"sets": [{"reps": 10, "weight": 60, "rpe": 7.0}]},
        {"sets": [{"reps": 10, "weight": 60, "rpe": 6.5}]}
    ]
    
    rec = check_progression(
        exercise_id="bench_press",
        exercise_name="Bench Press",
        equipment_type="barbell",
        target_reps=10,
        target_rpe=8.0,
        recent_sessions=recent_sessions,
        consecutive_sessions_required=2
    )
    
    assert rec is not None
    assert isinstance(rec, ProgressionRecommendation)
    assert rec.current_weight == 60
    assert rec.recommended_weight == 62.5 # Barbell increment is 2.5
    assert rec.recommended_reps == "10"


def test_no_progression_if_reps_missed():
    """Test that it does NOT recommend progression if reps fall short."""
    recent_sessions = [
        {"sets": [{"reps": 10, "weight": 60, "rpe": 7.0}]},
        {"sets": [{"reps": 8, "weight": 60, "rpe": 8.5}]} # Missed target reps
    ]
    
    rec = check_progression(
        exercise_id="bench_press",
        exercise_name="Bench Press",
        equipment_type="barbell",
        target_reps=10,
        target_rpe=8.0,
        recent_sessions=recent_sessions,
        consecutive_sessions_required=2
    )
    
    assert rec is None


def test_no_progression_if_rpe_too_high():
    """Test that it does NOT recommend progression if the set was too hard (RPE missed)."""
    recent_sessions = [
        {"sets": [{"reps": 10, "weight": 60, "rpe": 7.0}]},
        {"sets": [{"reps": 10, "weight": 60, "rpe": 9.5}]} # Reached failure, RPE > 8.0
    ]
    
    rec = check_progression(
        exercise_id="bench_press",
        exercise_name="Bench Press",
        equipment_type="barbell",
        target_reps=10,
        target_rpe=8.0,
        recent_sessions=recent_sessions,
        consecutive_sessions_required=2
    )
    
    assert rec is None


def test_bodyweight_progression():
    """Test that it progresses reps instead of weight for bodyweight exercises."""
    recent_sessions = [
        {"sets": [{"reps": 15, "weight": 0, "rpe": 6.0}]},
        {"sets": [{"reps": 15, "weight": 0, "rpe": 6.0}]}
    ]
    
    rec = check_progression(
        exercise_id="pushups",
        exercise_name="Push-ups",
        equipment_type="bodyweight",
        target_reps=15,
        target_rpe=8.0,
        recent_sessions=recent_sessions,
        consecutive_sessions_required=2
    )
    
    assert rec is not None
    assert rec.current_weight == 0
    assert rec.recommended_weight == 0
    assert rec.recommended_reps == "17" # Increments reps by 2
