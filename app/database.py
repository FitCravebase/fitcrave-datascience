from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.config import settings
from app.models.user import UserProfile
from app.models.workout import WorkoutPlan, Exercise
from app.models.meal import MealLog, DailyMealPlan

async def init_db():
    """Initialize MongoDB connection and Beanie models."""
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]
    
    await init_beanie(
        database=db,
        document_models=[
            UserProfile,
            WorkoutPlan,
            Exercise,
            MealLog,
            DailyMealPlan,
        ]
    )
    print(f"✅ Connected to MongoDB at {settings.MONGODB_URI}")
