from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from app.inbound.inbound_gateway import process_message


async def handle_reminder_event(reminder: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle reminder scheduler events through the unified inbound gateway.
    """
    reminder_id = reminder.get("reminder_id", "")
    message = reminder.get("message", "")
    user_id = reminder.get("user_id", "")
    remind_at = reminder.get("remind_at")

    # Encode a deterministic system message that the orchestrator can parse.
    inbound_message = f"deliver reminder {reminder_id}".strip()

    metadata = {
        "source": "reminder_scheduler",
        "reminder_id": reminder_id,
        "remind_at": remind_at,
        "original_message": message,
    }

    return await process_message(
        platform="reminder",
        user_id=str(user_id or ""),
        message=inbound_message,
        timestamp=datetime.utcnow().isoformat(),
        metadata=metadata,
        device="system",
        preferred_language="auto",
        voice_input=False,
    )
