"""
Coaching Model

Schema for coaching logs and notification records.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CoachingLog(BaseModel):
    """A coaching interaction record."""

    user_id: str
    date: datetime
    type: Literal["daily_briefing", "reactive", "weekly_review"]
    content: str
    trigger_event: str | None = None
    read_by_user: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
