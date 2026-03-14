# YouTube Video Integration — V2 Architecture Plan

## Problem Statement

The current implementation uses fuzzy string matching against a local `exercises.json` database to look up `video_id`s. This fails for most AI-generated exercises because:

1. The LLM frequently generates valid, real exercises not present in our 873-exercise database.
2. The fuzzy matcher falls back to a YouTube search URL for most exercises.
3. The embedded YouTube player (which provides a better UX) is rarely utilized.

---

## Proposed Solution: Lazy Load + Firestore Global Cache + Gemini Function Calling

### Architecture Overview

```
Plan Generation (no YouTube API calls)
  └─ LLM outputs exercise name + youtube_search_query field

User taps exercise card in the Flutter app
  └─ Flutter checks Firestore cache: exercise_video_cache/{exercise_name_slug}
      ├─ CACHE HIT  → use cached video_id → embed YoutubePlayer
      └─ CACHE MISS → call YouTube Data API → store result in cache → embed YoutubePlayer
```

### Why This Combination Works

| Problem | Solution |
|---|---|
| YouTube API rate limit (100 searches/day) | Lazy load: API only called when user taps, not at plan generation |
| Novel exercises not in local DB | LLM-provided `youtube_search_query` is precise for any exercise |
| Repeat API calls for same exercise | Firestore global cache: each exercise API-fetched only once, ever |
| Cache cold-start latency | Fallback search URL shown while first fetch happens; result cached immediately |

---

## Implementation Plan

### Step 1 — Add `youtube_search_query` to LLM Output Schema

**File:** `app/engines/workout/plan_generator.py`

Add `youtube_search_query: str` to the `LLMPlannedExercise` Pydantic model and the prompt schema. The LLM will generate a precise search string it knows is appropriate for each exercise it picks.

```python
class LLMPlannedExercise(BaseModel):
    exercise_name: str
    target_sets: int
    target_reps: int
    rest_seconds: int
    notes: Optional[str]
    youtube_search_query: str  # NEW: e.g. "incline cable fly proper form tutorial"
```

Update the prompt to instruct the LLM:
```
Each exercise object must also include:
- youtube_search_query: A precise YouTube search query to find a tutorial video
  (e.g. "barbell squat proper form beginner tutorial")
```

**Remove:** The fuzzy matching block in `plan_generator.py` (the `thefuzz` import and the post-processing loop). Plan generation becomes instant with no local DB lookups.

---

### Step 2 — Firestore Cache Collection

Create a Firestore collection: `exercise_video_cache`

**Document ID:** URL-safe slug of exercise name (e.g., `incline-cable-fly`)

**Document structure:**
```json
{
  "exercise_name": "Incline Cable Fly",
  "video_id": "abc123XYZ",
  "youtube_search_query": "incline cable fly proper form tutorial",
  "fetched_at": "2025-03-05T09:00:00Z"
}
```

This cache is **global** — shared across all users. Once fetched for any user, it's free for every subsequent user.

---

### Step 3 — Flutter Lazy Load on Card Expand

**File:** `lib/screens/swp_workout_details_screen.dart`

When a user expands an exercise card:

1. Check Firestore cache (`exercise_video_cache/{slug}`)
2. **Cache HIT:** Use `video_id` → show `YoutubePlayer` immediately
3. **Cache MISS:**
   - Show the YouTube search fallback URL button immediately (non-blocking UX)
   - Call a backend Cloud Function or direct REST endpoint to trigger a YouTube API search
   - On result: save to Firestore cache + update UI with embedded player

**Flutter-side cache check (pseudocode):**
```dart
final slug = exercise.exerciseName.toLowerCase().replaceAll(' ', '-');
final cacheDoc = await FirebaseFirestore.instance
  .collection('exercise_video_cache')
  .doc(slug)
  .get();

if (cacheDoc.exists) {
  final videoId = cacheDoc['video_id'];
  // Show YoutubePlayer(videoId: videoId)
} else {
  // Show fallback search URL button
  // Trigger background fetch + cache write
}
```

---

### Step 4 — YouTube Fetch Cloud Function / API Endpoint (Optional)

For the background fetch triggered in Step 3, two options:

**Option A (Simple):** Call the YouTube API directly from the Python backend via a FastAPI endpoint `POST /api/v1/exercises/fetch-video` that accepts `{ exercise_name, youtube_search_query }`, searches YouTube, writes to Firestore, and returns `{ video_id }`.

**Option B (Serverless):** Deploy a Firebase Cloud Function that is triggered by the Firestore cache miss (via a Firestore `onWrite` trigger or direct HTTP call from Flutter).

Option A is simpler and fits our existing FastAPI architecture.

---

## Rate Limit Analysis

| Scenario | API Calls Used |
|---|---|
| Plan generated | 0 (no YouTube calls at generation time) |
| User views exercise (cache miss) | 1 call = 100 units |
| User views same exercise again | 0 (cache hit, free forever) |
| All ~300 common exercises cached | 0 ongoing cost |
| 10,000 unit/day free quota | Supports **100 brand-new exercise first-views per day** |

In practice, after the first ~1-2 weeks of real user activity, the cache will be populated for all common exercises and YouTube API usage approaches zero.

---

## Files to Modify

| File | Change |
|---|---|
| `app/models/workout.py` | Add `youtube_search_query` to `LLMPlannedExercise` |
| `app/engines/workout/plan_generator.py` | Add `youtube_search_query` to prompt; remove fuzzy matching block |
| `app/api/routes/exercises.py` | New endpoint: `POST /exercises/fetch-video` |
| `lib/models/workout.dart` | Add `youtubeSearchQuery` field to `PlannedExercise` |
| `lib/screens/swp_workout_details_screen.dart` | Lazy load on card expand with Firestore cache check |

---

## Dependencies (Already Installed)

- `google-api-python-client` — YouTube API (already in `requirements.txt`)
- `youtube_player_flutter` — Embedded player (already in `pubspec.yaml`)
- `cloud_firestore` — Cache storage (already in `pubspec.yaml`)
