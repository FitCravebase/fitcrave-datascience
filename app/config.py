"""
Application configuration — loaded from environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the FitCrave AI backend."""

    # --- App ---
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    APP_HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"

    # --- Google Gemini ---
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3-flash-preview"
    GEMINI_VISION_MODEL: str = "gemini-3-flash-preview"

    # --- MongoDB ---
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "fitcrave"

    # --- Firebase ---
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-service-account.json"

    # --- External APIs ---
    CALORIENINJA_API_KEY: str = ""
    YOUTUBE_API_KEY: str = ""

    # --- Notification Scheduling ---
    DAILY_BRIEFING_CRON: str = "0 7 * * *"
    WEEKLY_REVIEW_CRON: str = "0 20 * * 0"

    # --- Safety Thresholds ---
    MIN_CALORIES_MALE: int = 1500
    MIN_CALORIES_FEMALE: int = 1200
    MAX_WEIGHT_LOSS_KG_PER_WEEK: float = 1.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
