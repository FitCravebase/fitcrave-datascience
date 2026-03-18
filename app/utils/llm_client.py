"""
Gemini LLM Client

Provides a singleton wrapper around Google GenAI SDK
for text generation and image analysis.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """
    Lazily initialize the GenAI client.

    Cloud Run may start the container before env vars are set correctly; we
    avoid crashing at import time and instead raise a clear error only when
    the LLM is actually invoked.
    """
    global _client
    if _client is not None:
        return _client

    api_key = getattr(settings, "GEMINI_API_KEY", "") or ""
    if not api_key.strip():
        raise ValueError(
            "GEMINI_API_KEY is missing. Set it as an environment variable in Cloud Run "
            "or provide it in your .env file."
        )

    _client = genai.Client(api_key=api_key)
    return _client


class GeminiClient:
    """Thin wrapper providing JSON-oriented helpers over Gemini."""

    def __init__(self) -> None:
        self._model = settings.GEMINI_MODEL
        self._vision_model = settings.GEMINI_VISION_MODEL

    # ── helpers ────────────────────────────────────────────────────

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        """Strip markdown fences and parse the first JSON object/array."""
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip()
        cleaned = cleaned.rstrip("`").strip()
        return json.loads(cleaned)

    # ── public API ────────────────────────────────────────────────

    async def generate_json(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.4,
    ) -> dict[str, Any]:
        """Generate text with Gemini and parse the response as JSON."""
        contents = prompt
        if system_instruction:
            contents = system_instruction + "\n\n" + prompt

        response = await _get_client().aio.models.generate_content(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(temperature=temperature),
        )
        return self._extract_json(response.text)

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        """Generate plain-text response with Gemini."""
        contents = prompt
        if system_instruction:
            contents = system_instruction + "\n\n" + prompt

        response = await _get_client().aio.models.generate_content(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(temperature=temperature),
        )
        return response.text

    async def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str,
        mime_type: str = "image/jpeg",
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """Send an image + prompt to Gemini Vision and parse JSON response."""
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        response = await _get_client().aio.models.generate_content(
            model=self._vision_model,
            contents=[prompt, image_part],
            config=types.GenerateContentConfig(temperature=temperature),
        )
        return self._extract_json(response.text)


# Singleton instance used across the app
gemini_client = GeminiClient()
