from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import HTTPException, Request

from app.inbound.inbound_gateway import process_message


def _verify_whatsapp_webhook(request: Request, payload: Dict[str, Any]) -> bool:
    """
    Best-effort verification stub. If provider secrets are not configured,
    we allow the request but keep the verification hook for future wiring.
    """
    _ = request
    _ = payload
    return True


async def handle_whatsapp_webhook(request: Request) -> Dict[str, Any]:
    """
    Receive WhatsApp webhook events and forward into the unified inbound gateway.
    """
    try:
        payload = await request.json()
        if not _verify_whatsapp_webhook(request, payload):
            return {"status": "rejected", "reason": "webhook_verification_failed"}

        entries = payload.get("entry", [])
        if not entries:
            return {"status": "ignored", "reason": "no_entries"}

        messaging_events = entries[0].get("messaging", [])
        if not messaging_events:
            return {"status": "ignored", "reason": "no_messaging_events"}

        messaging_event = messaging_events[0]
        if not messaging_event.get("message"):
            return {"status": "ignored", "reason": "non_message_event"}

        message_data = messaging_event["message"]
        if message_data.get("type") != "text":
            return {"status": "ignored", "reason": f"unsupported_message_type: {message_data.get('type')}"}

        message_text = message_data["text"]["body"]
        sender_id = messaging_event.get("sender", {}).get("id", "")

        result = await process_message(
            platform="whatsapp",
            user_id=str(sender_id or ""),
            message=message_text,
            timestamp=datetime.utcnow().isoformat(),
            metadata={"provider": "whatsapp", "event": messaging_event},
            device="mobile",
            preferred_language="auto",
            voice_input=False,
        )

        return {
            "status": "processed",
            "trace_id": result.get("trace_id"),
            "processed_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(exc)}") from exc
