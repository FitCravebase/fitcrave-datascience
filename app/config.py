import os
from dataclasses import dataclass


@dataclass
class Settings:
  """Runtime configuration loaded from environment variables."""

  # Database
  MONGODB_URI: str = os.getenv("MONGODB_URI", "")
  MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "fitcrave")

  # Gemini / Google GenAI
  # NOTE: For local development you may hardcode GEMINI_API_KEY here if desired,
  # but in production prefer setting it via environment variables / secrets.
  GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "AIzaSyCrr25g6dCrz5xIWeCRH9YJSVFkDhZfjAw")

  # Default models chosen for SWP and nutrition engines:
  # - TEXT: gemini-3-flash-preview
  # - VISION: gemini-3-flash-preview
  GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
  GEMINI_VISION_MODEL: str = os.getenv("GEMINI_VISION_MODEL", "gemini-3-flash-preview")


settings = Settings()

