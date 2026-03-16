from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import HTTPException, Request

from app.inbound.inbound_gateway import process_message
from app.services.telegram_contact_service import TelegramContactService


async def handle_telegram_webhook(request: Request) -> Dict[str, Any]:
    """
    Receive Telegram Bot API updates and forward into the unified inbound gateway.
    """
    try:
        payload = await request.json()
        message = payload.get("message", {})
        if not message or not message.get("text"):
            return {"status": "ignored", "reason": "no_text_message"}

        chat = message.get("chat", {})
        sender = message.get("from", {})
        text = message.get("text", "")

        contact_service = TelegramContactService()
        contact_service.save_from_telegram_message(chat, sender)

        chat_id = chat.get("id")
        sender_id = sender.get("id") or chat_id
        preferred_language = sender.get("language_code", "auto")

        result = await process_message(
            platform="telegram",
            user_id=str(sender_id or ""),
            message=text,
            timestamp=datetime.utcnow().isoformat(),
            metadata={"provider": "telegram", "update": payload},
            device="mobile",
            preferred_language=preferred_language,
            voice_input=False,
        )

        return {
            "status": "processed",
            "trace_id": result.get("trace_id"),
            "processed_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(exc)}") from exc
