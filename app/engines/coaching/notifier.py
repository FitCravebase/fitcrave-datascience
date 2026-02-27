"""
Push Notification Sender

Sends push notifications via Firebase Cloud Messaging (FCM).
Used by the coaching engine for daily briefings, reactive coaching,
and weekly reviews.
"""

from __future__ import annotations

from typing import Any


async def send_push_notification(
    user_id: str,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
) -> bool:
    """
    Send a push notification to a specific user via FCM.

    Args:
        user_id: The target user's ID.
        title: Notification title.
        body: Notification body text.
        data: Optional data payload for the app to process.

    Returns:
        True if sent successfully.

    TODO: Implement using firebase_admin.messaging:
        1. Look up user's FCM token from database
        2. Construct firebase_admin.messaging.Message
        3. Send via firebase_admin.messaging.send()
    """
    pass


async def send_batch_notifications(
    notifications: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Send notifications to multiple users in a batch.

    Used for daily briefings — generates all briefings in one pass,
    then sends them in a batch for efficiency.

    Args:
        notifications: List of {user_id, title, body, data} dicts.

    Returns:
        Summary of sent/failed notifications.

    TODO: Implement using firebase_admin.messaging.send_each().
    """
    pass
