"""
Gemini LLM Client

Centralized wrapper around the Google Gemini API.
All LLM calls in the application go through this module.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)


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
        self.model = settings.GEMINI_MODEL
        self.vision_model = settings.GEMINI_VISION_MODEL
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        """Lazily initialize the Gemini client on first use."""
        if self._client is None:
            if not settings.GEMINI_API_KEY:
                raise RuntimeError(
                    "GEMINI_API_KEY is not set. Add it to your .env file."
                )
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def _track_usage(self, usage_metadata: Any) -> None:
        """Accumulate token counts from a response's usage metadata."""
        if usage_metadata is None:
            return
        self._total_input_tokens += getattr(usage_metadata, "prompt_token_count", 0) or 0
        self._total_output_tokens += getattr(usage_metadata, "candidates_token_count", 0) or 0

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
        """
        client = self._get_client()

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
        )

        response = await client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )

        self._track_usage(response.usage_metadata)
        logger.debug(
            "generate_text | model=%s | in=%d out=%d tokens",
            self.model,
            getattr(response.usage_metadata, "prompt_token_count", 0) or 0,
            getattr(response.usage_metadata, "candidates_token_count", 0) or 0,
        )

        return response.text

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
        """
        client = self._get_client()

        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            system_instruction=system_instruction,
        )

        response = await client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )

        self._track_usage(response.usage_metadata)
        logger.debug(
            "generate_json | model=%s | in=%d out=%d tokens",
            self.model,
            getattr(response.usage_metadata, "prompt_token_count", 0) or 0,
            getattr(response.usage_metadata, "candidates_token_count", 0) or 0,
        )

        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error("generate_json: failed to parse response as JSON: %s", response.text)
            raise ValueError(f"Gemini returned invalid JSON: {e}") from e

    async def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str,
        mime_type: str = "image/jpeg",
    ) -> dict[str, Any]:
        """
        Analyze an image with a text prompt (MealSnap).

        Args:
            image_bytes: Raw image data.
            prompt: Analysis instructions.
            mime_type: Image MIME type (default: image/jpeg).

        Returns:
            Structured analysis result as a dict.
        """
        client = self._get_client()

        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        config = types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
        )

        response = await client.aio.models.generate_content(
            model=self.vision_model,
            contents=[image_part, prompt],
            config=config,
        )

        self._track_usage(response.usage_metadata)
        logger.debug(
            "analyze_image | model=%s | in=%d out=%d tokens",
            self.vision_model,
            getattr(response.usage_metadata, "prompt_token_count", 0) or 0,
            getattr(response.usage_metadata, "candidates_token_count", 0) or 0,
        )

        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error("analyze_image: failed to parse response as JSON: %s", response.text)
            raise ValueError(f"Gemini returned invalid JSON for image analysis: {e}") from e

    def get_usage_stats(self) -> dict[str, int]:
        """Return cumulative token usage stats for cost monitoring."""
        return {
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
        }


# Singleton instance
gemini_client = GeminiClient()
