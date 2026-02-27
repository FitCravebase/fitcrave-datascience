"""
Tests for the macro calculator.

These test the fully-implemented rule-based macro calculator
to ensure BMR, TDEE, and macro calculations are correct.
"""

from app.engines.nutrition.macro_calculator import (
    ActivityLevel,
    FitnessGoal,
    Gender,
    calculate_bmr,
    calculate_macro_targets,
    calculate_tdee,
)


class TestBMR:
    """Test BMR calculations using Mifflin-St Jeor."""

    def test_male_bmr(self):
        # 25-year-old male, 75kg, 175cm
        bmr = calculate_bmr(weight_kg=75, height_cm=175, age=25, gender=Gender.MALE)
        # (10 × 75) + (6.25 × 175) - (5 × 25) + 5 = 750 + 1093.75 - 125 + 5 = 1723.75
        assert bmr == 1723.8

    def test_female_bmr(self):
        # 25-year-old female, 60kg, 165cm
        bmr = calculate_bmr(weight_kg=60, height_cm=165, age=25, gender=Gender.FEMALE)
        # (10 × 60) + (6.25 × 165) - (5 × 25) - 161 = 600 + 1031.25 - 125 - 161 = 1345.25
        assert bmr == 1345.2


class TestTDEE:
    """Test TDEE calculations."""

    def test_sedentary_tdee(self):
        tdee = calculate_tdee(bmr=1700, activity_level=ActivityLevel.SEDENTARY)
        assert tdee == 2040.0

    def test_moderately_active_tdee(self):
        tdee = calculate_tdee(bmr=1700, activity_level=ActivityLevel.MODERATELY_ACTIVE)
        assert tdee == 2635.0


class TestMacroTargets:
    """Test complete macro target calculation."""

    def test_fat_loss_targets(self):
        targets = calculate_macro_targets(
            weight_kg=75,
            height_cm=175,
            age=25,
            gender=Gender.MALE,
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
            goal=FitnessGoal.FAT_LOSS,
        )
        assert targets.target_calories > 1500  # Above safety floor
        assert targets.protein_g == 150  # 2.0 × 75
        assert targets.fat_g == 60  # 0.8 × 75

    def test_safety_floor_male(self):
        # Very low weight should not go below 1500 cal for male
        targets = calculate_macro_targets(
            weight_kg=50,
            height_cm=160,
            age=30,
            gender=Gender.MALE,
            activity_level=ActivityLevel.SEDENTARY,
            goal=FitnessGoal.FAT_LOSS,
        )
        assert targets.target_calories >= 1500

    def test_safety_floor_female(self):
        targets = calculate_macro_targets(
            weight_kg=45,
            height_cm=150,
            age=30,
            gender=Gender.FEMALE,
            activity_level=ActivityLevel.SEDENTARY,
            goal=FitnessGoal.FAT_LOSS,
        )
        assert targets.target_calories >= 1200
