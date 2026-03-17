import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore

from app.database import users_collection
from app.models.user import UserProfile
from app.engines.workout.plan_generator import generate_workout_plan

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Firebase (Ensure FIREBASE_CREDENTIALS_PATH points to a valid service account JSON locally)
db_client = None
if not firebase_admin._apps:
    try:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            firebase_admin.initialize_app()
        logger.info("✅ Firebase Admin initialized in Workout Router.")
        db_client = firestore.client()
    except Exception as e:
        logger.warning(f"⚠️ Could not initialize Firebase Admin: {e}")
else:
    db_client = firestore.client()

class GenerateSwpRequest(BaseModel):
    firebase_uid: str

@router.post("/generate-swp")
async def generate_swp(request: GenerateSwpRequest):
    user_id = request.firebase_uid
    logger.info(f"🚀 [GENERATOR TRIGGERED] User {user_id} requested a new workout plan via HTTP!")
    
    try:
        # 1. Fetch user from MongoDB
        user_doc = await users_collection().find_one({"firebaseUid": user_id})
        if not user_doc:
            logger.warning(f"User {user_id} not found in MongoDB. Generating generic profile.")
            user_profile = UserProfile(
                firebase_uid=user_id,
                email=f"{user_id}@example.com",
                name="User",
                age=25,
                gender="prefer_not_to_say",
                height_cm=170.0,
                weight_kg=70.0,
                target_timeline=None,
                goal="General Fitness",
                experience_level="beginner",
                weekly_available_days=3,
                session_duration_minutes=45,
                equipment=[],
                injuries=[],
                dietary_restrictions=[],
                meal_count_per_day=3,
                allergies=[]
            )
        else:
            # Handle potential schema differences gracefully by ensuring `None` falls back to default equivalents using `or`.
            user_profile = UserProfile(
                firebase_uid=user_id,
                email=user_doc.get("email") or f"{user_id}@example.com",
                name=user_doc.get("name") or "User",
                age=user_doc.get("age") or 25,
                gender=user_doc.get("gender") or "prefer_not_to_say",
                height_cm=user_doc.get("height") or 170.0,
                weight_kg=user_doc.get("weight_kg") or user_doc.get("weight") or 70.0,
                target_timeline=user_doc.get("target_timeline"),
                goal=user_doc.get("swp_goal") or "General Fitness",
                experience_level=user_doc.get("experience_level") or "beginner",
                weekly_available_days=user_doc.get("weekly_available_days") or 3,
                session_duration_minutes=int(user_doc.get("session_duration_minutes") or 45),
                equipment=user_doc.get("equipment", []),
                injuries=user_doc.get("injuries", []),
                dietary_restrictions=[],
                meal_count_per_day=3,
                allergies=[]
            )
        
        # 2. Check for an existing plan to maintain program continuity
        previous_plan_dict = None
        if db_client:
            existing_plan_ref = db_client.collection('users').document(user_id).collection('workout_plans').document('current_plan')
            existing_plan_doc = existing_plan_ref.get()
            if existing_plan_doc.exists:
                previous_plan_dict = existing_plan_doc.to_dict()
                logger.info(f"🔄 Found existing plan for {user_id}. Enforcing Program Continuity.")
            else:
                logger.info(f"🆕 No existing plan found for {user_id}. Generating a brand new Mesocycle.")
        
        # 3. Generate the plan using Gemini
        logger.info(f"🧠 Prompting Gemini to generate a specialized {user_profile.experience_level} {user_profile.goal} plan...")
        
        plan = await generate_workout_plan(user_profile, db=db_client, previous_plan_dict=previous_plan_dict)
        
        # 4. Save the generated plan back to Firestore (Flutter reads it from there)
        if db_client:
            logger.info(f"💾 Saving {plan.plan_name} to Firestore > users/{user_id}/workout_plans")
            db_client.collection('users').document(user_id).collection('workout_plans').document('current_plan').set(
                plan.model_dump()
            )
            
            # Reset the trigger flag just in case
            db_client.collection('users').document(user_id).update({
                'requires_new_plan': False
            })
        
        logger.info(f"✅ Successfully finished AI Generation Pipeline for {user_id}!")
        return {"status": "success", "message": "Workout plan generated successfully", "plan": plan.model_dump()}
        
    except Exception as e:
        logger.error(f"❌ Error generating plan for {user_id}: {e}", exc_info=True)
        # Try to reset flag even on failure to prevent infinite crashing loop on Flutter side
        if db_client:
            try:
                db_client.collection('users').document(user_id).update({'requires_new_plan': False})
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))
