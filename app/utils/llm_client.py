"""
Gemini LLM Client

Centralized wrapper around the Google Gemini API.
All LLM calls in the application go through this module.
"""

from __future__ import annotations

from typing import Any

from app.config import settings


class GeminiClient:
    """
    Wrapper around Google Gemini API.

    Provides:
    - Text generation (for meal plans, coaching, etc.)
    - Vision analysis (for MealSnap)
    - Structured JSON output mode
    - Token usage tracking for cost monitoring
    """

    def __init__(self):
        """
        Initialize the Gemini client.

        TODO: Set up google.genai client with API key from settings.
        """
        self.model = settings.GEMINI_MODEL
        self.vision_model = settings.GEMINI_VISION_MODEL
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: The user/task prompt.
            system_instruction: Optional system-level instruction.
            temperature: Creativity parameter (0.0-1.0).
            max_tokens: Maximum output tokens.

        Returns:
            Generated text response.

        TODO: Implement using google.genai.
        """
        pass

    async def generate_json(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """
        Generate structured JSON output.

        Uses Gemini's JSON mode for reliable structured responses.
        Lower temperature for more deterministic output.

        TODO: Implement with response_mime_type="application/json".
        """
        pass

    async def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str,
    ) -> dict[str, Any]:
        """
        Analyze an image with a text prompt (MealSnap).

        Args:
            image_bytes: Raw image data.
            prompt: Analysis instructions.

        Returns:
            Structured analysis result.

        TODO: Implement using Gemini Vision with image + text input.
        """
        pass

    def get_usage_stats(self) -> dict[str, int]:
        """Return cumulative token usage stats for cost monitoring."""
        return {
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
        }


# Singleton instance
gemini_client = GeminiClient()
