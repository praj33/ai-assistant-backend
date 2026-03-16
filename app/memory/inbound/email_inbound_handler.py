from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import HTTPException, Request

from app.inbound.inbound_gateway import process_message


async def handle_email_webhook(request: Request) -> Dict[str, Any]:
    """
    Receive inbound email events and forward into the unified inbound gateway.
    """
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            payload = await request.json()
        else:
            raw_body = await request.body()
            payload = {"content": raw_body.decode("utf-8")}

        email_content = payload.get("content", "") or payload.get("text", "") or payload.get("body", "")
        sender = payload.get("from", payload.get("sender", ""))
        subject = payload.get("subject", "No Subject")

        if not email_content:
            return {"status": "ignored", "reason": "empty_content"}

        message_text = f"Subject: {subject}\n\n{email_content}"

        result = await process_message(
            platform="email",
            user_id=str(sender or ""),
            message=message_text,
            timestamp=datetime.utcnow().isoformat(),
            metadata={"provider": "email", "payload": payload},
            device="desktop",
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
