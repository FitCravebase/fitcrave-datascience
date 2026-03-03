import os
import asyncio
import threading
import firebase_admin
from firebase_admin import credentials, firestore
from threading import Event

from app.config import settings
from app.models.user import UserProfile
from app.engines.workout.plan_generator import generate_workout_plan
from app.engines.workout.exercise_db import exercise_db

# Initialize Firebase (Ensure FIREBASE_CREDENTIALS_PATH points to a valid service account JSON locally)
db = None
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin initialized.")
        db = firestore.client()
    except Exception as e:
        print(f"⚠️ Could not initialize Firebase Admin: {e}\nEnsure '{settings.FIREBASE_CREDENTIALS_PATH}' exists and is valid.")
        print("Exiting listener.")
        exit(1)

# We use an asyncio Event to keep the script running
keep_alive = Event()

# A single persistent event loop running in a background thread.
# Firestore callbacks are synchronous, so we submit coroutines here
# via asyncio.run_coroutine_threadsafe() instead of calling asyncio.run()
# (which creates+destroys a loop on every call and breaks on rapid triggers).
_async_loop = asyncio.new_event_loop()
threading.Thread(target=_async_loop.run_forever, daemon=True, name="async-worker").start()

async def process_new_plan(user_id: str, doc_dict: dict):
    """
    Called when the listener detects requires_new_plan == True.
    """
    try:
        print(f"\n🚀 [GENERATOR TRIGGERED] User {user_id} requested a new workout plan!")
        
        # 1. Parse Firestore document into backend UserProfile model
        # We handle potential schema differences gracefully here by ensuring `None` falls back to default equivalents using `or`.
        user_profile = UserProfile(
            firebase_uid=user_id,
            email=doc_dict.get("email") or f"{user_id}@example.com",
            name=doc_dict.get("name") or "User",
            age=doc_dict.get("age") or 25,
            gender=doc_dict.get("gender") or "prefer_not_to_say",
            height_cm=doc_dict.get("height") or 170.0,
            weight_kg=doc_dict.get("weight") or 70.0,
            target_timeline=doc_dict.get("target_timeline"),
            goal=doc_dict.get("goal") or "General Fitness",
            experience_level=doc_dict.get("experience_level") or "beginner",
            weekly_available_days=doc_dict.get("weekly_available_days") or 3,
            session_duration_minutes=int(doc_dict.get("session_duration_minutes") or 45),
            equipment=doc_dict.get("equipment", []),
            injuries=doc_dict.get("injuries", []),
            dietary_restrictions=[], # Added later
            meal_count_per_day=3,
            allergies=[]
        )
        
        # 3. Generate the plan using Gemini Multi-turn Orchestrator
        print(f"🧠 Prompting Gemini 2.0 to generate a specialized {user_profile.experience_level} {user_profile.goal} plan...")
        
        plan = await generate_workout_plan(user_profile)
        
        # 4. Save the generated plan back to Firestore!
        print(f"💾 Saving {plan.plan_name} to Firestore > users/{user_id}/workout_plans")
        
        # Write the Pydantic model directly to the nested collection
        db.collection('users').document(user_id).collection('workout_plans').document('current_plan').set(
            plan.model_dump()
        )
        
        # 5. Reset the trigger flag so we don't end up in an infinite generation loop
        db.collection('users').document(user_id).update({
            'requires_new_plan': False
        })
        
        print(f"✅ Successfully finished AI Generation Pipeline for {user_id}!")
        
    except Exception as e:
        print(f"❌ Error generating plan for {user_id}: {e}")
        # Reset flag even on failure to prevent infinite crashing loop
        db.collection('users').document(user_id).update({
            'requires_new_plan': False
        })


def on_user_snapshot(col_snapshot, changes, read_time):
    """
    Callback fired by the Firestore SDK whenever a document in 'users' changes.
    """
    for change in changes:
        # We only care about modifications (since creation happens before SWP onboarding is finished)
        if change.type.name == 'MODIFIED':
            doc = change.document
            doc_dict = doc.to_dict()
            
            # Check for the magical trigger flag we added in Flutter Phase 3.5!
            if doc_dict.get('requires_new_plan') is True:
                # Submit to the persistent loop — safe to call from any thread,
                # and the loop is never closed between invocations.
                asyncio.run_coroutine_threadsafe(
                    process_new_plan(doc.id, doc_dict),
                    _async_loop,
                )


def start_listener():
    """Starts the Firestore document watcher."""
    print("🎧 Starting Firestore Listener on collection 'users'...")
    # Subscribe to the entire users collection
    users_ref = db.collection('users')
    
    # Start watching
    watcher = users_ref.on_snapshot(on_user_snapshot)
    
    try:
        # Keep the main thread alive indefinitely
        print("👀 Watching for 'requires_new_plan' triggers. Press Ctrl+C to stop.")
        keep_alive.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down listener...")
        watcher.unsubscribe()

if __name__ == "__main__":
    start_listener()
