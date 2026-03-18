# Frontend / Backend Data Mapping

## 1. What the Frontend Currently Collects
We have THREE different places where user data is collected.

**Screen 1: `UserDetailsScreen.dart` (Account Onboarding)** (Saved to Firebase `users` collection)
- `name` (String)
- `age` (int)
- `weight` (int, kg)
- `height` (int, cm)
- `gender` ("Male", "Female", "Others")
- `mobile` (from Auth)

**Screen 2: `QuestionnaireScreen.dart` (Nutrition/General Onboarding)** (State only; NOT saved to Firebase)
- **Goal:** "Build Muscles", "Fat loss", "Maintenance"
- **Timeline:** Value (int) + Unit ("Months" / "Years")
- **Diet Preference:** "Veg", "Non-veg"
- **Meal Frequency:** (int, e.g., 3 meals a day)

**Screen 3: SWP Onboarding Screens (Workout Specific)** (State only; NOT saved to Firebase)
- `SwpGoalsScreen`: 'build_muscle', 'lose_fat', 'improve_fitness', 'increase_strength'
- `SwpTimelineScreen`: Integer + 'Months' / 'Years'
- `SwpFitnessLevelScreen`: 'Beginner (Just starting)', 'Intermediate', 'Advance'
- `SwpEquipmentScreen`: List of ['Bodyweight only', 'Dumbbells', 'Resistance bands', 'Home gym', 'Full gym access']
- `SwpSessionDurationScreen`: '10–15 min', '20–30 min', '30–45 min', '45–60 min', '60+ min'
- `SwpDaysPerWeekScreen`: 0-6 days
- `SwpInjuriesScreen`: List of ['None', 'Knee', 'Back', 'Shoulder', 'Neck', 'Other']

---

## 2. What the Python Backend Expects
In `fitcrave-datascience/app/models/user.py`, our `UserProfile` requires:
- **Biometrics:** `age`, `weight_kg`, `height_cm`, `gender` (lowercase "male"/"female")
- **Fitness / SWP:** `goal`, `activity_level`, `experience_level`, `weekly_available_days`, `session_duration_minutes`
- **Diet:** `dietary_restrictions`, `meal_count_per_day`, `allergies`
- **Hardware/Injury:** `equipment` (List of strings)

---

## 3. Discrepancies & Action Plan

To connect the two perfectly, here is what we need to code:

### Backend Schema Updates:
1.  **Add Timeline Field:** Add `target_timeline: str | None = None` to the `UserProfile`.
2.  **Add Injuries Field:** Add `injuries: list[str] = Field(default_factory=list)` to track SWP injury inputs.
3.  **Gender Enum:** Allow "other" or "prefer_not_to_say" alongside "male"/"female" in the backend.

### Frontend Flutter Updates:
1.  **Consolidate Saving Logic:** Instead of throwing the data away, we will update `ServiceManager` to have method(s) like `updateNutritionPreferences()` and `updateSWPPreferences()` that push these exact answers to the### Frontend (State -> DB logic):
3.  **String Normalization & Mapping (Frontend -> Backend):**
    *   **Diet:** "Veg" -> `['vegetarian']` in `dietary_restrictions`.
    *   **Gender:** "Male" -> `"male"`, "Female" -> `"female"`, "Others" -> `"other"`.
    *   **Fitness Level:** "Beginner (Just starting)" -> `"beginner"`, "Intermediate" -> `"intermediate"`, "Advance" -> `"advanced"`.
    *   **Duration:** Map "30–45 min" to actual integer `45` for the backend's `session_duration_minutes`.
    *   **Equipment:** Direct pass-through, just ensure they match the backend tags (e.g. "Bodyweight only" -> `"bodyweight"`, "Dumbbells" -> `"dumbbells"`).
4.  **Hook up the "Generate Plan" Buttons:** Both `QuestionnaireScreen.dart` and `SwpInjuriesScreen.dart` currently have dummy "Generate Plan" or "Next" buttons at the end of their flows. We need to update these buttons to gather all the state variables from their respective screens and push them to Firestore via `ServiceManager`.

---

## 4. Discovered Inconsistencies & Future Risks (AUDIT RESULTS)

During our audit, we found 4 major inconsistencies that need addressing before Phase 4 (Deployment/Integration):

### 1. Missing Dart Data Models (High Priority)
The Flutter `lib/models/` folder only contains community models (`post.dart`, `group.dart`).
**The Risk:** Flutter is currently handling Users, Workouts, and Meals as raw Maps (`Map<String, dynamic>`). When the Python backend generates complex nested JSON (like `WorkoutPlan` -> `WorkoutSession` -> `PlannedExercise` -> `WorkoutSet`), the frontend will be prone to null-pointer exceptions and mapping errors without strictly typed Dart Data Classes.

### 2. The Real-time "Generate Plan" Loop (High Priority)
**The Risk:** Currently, tapping "Generate Plan" in Flutter just saves the data to Firestore and instantly navigates to `swp_main_screen.dart` (which has hardcoded dummy data). It does *not* notify the Python backend that a new plan is needed. 
**The Fix Required:** We need to decide if Flutter will call the Python API directly (REST `POST /generate_plan`), or if Python will listen to a Firebase Firestore Trigger (`on_update(User)`). Without this bridge, the AI will never realize the user wants a plan.

### 3. Missing TDEE Activity Level (Medium Priority)
**The Risk:** The Python `UserProfile` schema expects `activity_level` (e.g., Sedentary, Active) to calculate calories for meal plans. The frontend onboarding *never* asks for this. It only asks for "Experience Level" (Beginner, Adv). We currently default `activity_level` to `"moderately_active"`. We should either add a quick screen or infer it from the SWP Days-Per-Week input.

### 4. Hardcoded Units (Low/Medium Priority)
**The Risk:** `UserDetailsScreen` hardcodes "kg" and "cm". The Python backend expects `weight_kg`. If a user is from a region using imperial (lbs), and they type `150` thinking it's pounds, the backend will think they are `150 kg` (330 lbs). We need to either enforce units strictly in UI with a toggle or handle conversions.
