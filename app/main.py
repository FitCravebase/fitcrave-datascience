from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import os

from beanie import init_beanie
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.database import connect_db, close_db, get_db
from app.models.user import UserProfile
from app.models.workout import WorkoutPlan
from app.engines.nutrition.router import router as nutrition_router
from app.engines.workout.router import router as workout_router
from graph.graph_builder import graph
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ChatRequest(BaseModel):
    latest_message: str
    session_id: str
    user_id: str
    user_name: Optional[str] = None
    location: Optional[str] = None
    user_profile: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    user_id: str
    session_id: str
    user_name: Optional[str] = None
    location: Optional[str] = None
    agent_data: Optional[Dict[str, Any]] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = os.getenv("APP_PORT", "8080")
    env = os.getenv("APP_ENV", "development")
    logger.info("FitCrave AI Backend starting on %s:%s [%s]", host, port, env)

    # Connect Motor client and ping MongoDB
    await connect_db()

    # Initialise Beanie ODM with all Document models
    await init_beanie(
        database=get_db(),
        document_models=[UserProfile, WorkoutPlan],
    )
    logger.info("Beanie ODM initialised")

    yield

    await close_db()
    logger.info("FitCrave AI Backend shutting down...")


app = FastAPI(
    title="FitCrave AI Backend",
    description="API for the Nutrition and Fitness AI Agent",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Flutter app to connect
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(nutrition_router, prefix="/api/v1/nutrition", tags=["Nutrition"])
app.include_router(workout_router, prefix="/api/v1/workout", tags=["Workout"])


@app.get("/health", tags=["System"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "fitcrave-ai"}


@app.get("/")
def read_root():
    return {"message": "Welcome to the FitCrave AI Backend"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    logger.info(f"Received /chat request - Session: {request.session_id}, User: {request.user_id}")
    logger.debug(f"Request payload: {request.model_dump()}")

    try:
        result = await graph.ainvoke(
            {
                "messages": [("user", request.latest_message)],
                "agent_data": {
                    "session_id": request.session_id,
                    "user_id": request.user_id,
                    "user_name": request.user_name,
                    "location": request.location,
                    "user_profile": request.user_profile,
                },
            },
            config={"configurable": {"thread_id": request.session_id, "user_id": request.user_id}},
        )

        logger.debug(f"LangGraph computation complete. Final state: {result}")

        messages = result.get("messages", [])
        if messages:
            last_msg = messages[-1].content
            if isinstance(last_msg, list):
                response_text = " ".join(
                    [str(b.get("text", "")) for b in last_msg if isinstance(b, dict) and "text" in b]
                )
            else:
                response_text = str(last_msg)
        else:
            response_text = "No response generated"

        agent_data = result.get("agent_data", {})

        logger.info(f"Successfully processed response for Session: {request.session_id}")

        return ChatResponse(
            response=response_text,
            user_id=request.user_id,
            session_id=request.session_id,
            user_name=request.user_name,
            location=request.location,
            agent_data=agent_data,
        )
    except Exception as e:
        logger.error(f"Exception during /chat: {e}", exc_info=True)
        return ChatResponse(
            response="An unexpected server error occurred while contacting the AI.",
            user_id=request.user_id,
            session_id=request.session_id,
            agent_data={"error": str(e)},
        )
