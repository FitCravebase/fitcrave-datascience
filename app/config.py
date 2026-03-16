"""
Application settings — loaded from environment variables / .env file.
"""

from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv(override=True)


class _Settings:
    """Simple settings container read from env vars."""

    @property
    def MONGODB_URI(self) -> str:
        return os.getenv("MONGODB_URI", "mongodb://localhost:27017")

    @property
    def MONGODB_DB_NAME(self) -> str:
        return os.getenv("MONGODB_DB_NAME", "fitcrave")

    @property
    def GEMINI_API_KEY(self) -> str:
        return os.getenv("GEMINI_API_KEY", "")

    @property
    def GEMINI_MODEL(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    @property
    def GEMINI_VISION_MODEL(self) -> str:
        return os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash")

    @property
    def FIREBASE_CREDENTIALS_PATH(self) -> str:
        return os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-service-account.json")

    @property
    def APP_ENV(self) -> str:
        return os.getenv("APP_ENV", "development")

    @property
    def APP_PORT(self) -> int:
        return int(os.getenv("APP_PORT", "8000"))

    @property
    def APP_HOST(self) -> str:
        return os.getenv("APP_HOST", "0.0.0.0")


settings = _Settings()
