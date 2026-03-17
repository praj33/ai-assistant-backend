from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable

from fastapi import HTTPException, Request

from app.inbound.inbound_gateway import process_message


def _verify_whatsapp_webhook(request: Request, raw_body: bytes) -> bool:
    """
    Verify WhatsApp/META webhook signatures.

    - If WHATSAPP_WEBHOOK_SECRET is not configured, allow the request
      but keep this hook wired for future hardening.
    - If a secret is configured, require a valid X-Hub-Signature-256
      header computed as: sha256=HMAC_SHA256(secret, body).
    """
    secret = (os.getenv("WHATSAPP_WEBHOOK_SECRET") or os.getenv("META_APP_SECRET") or "").strip()
    if not secret:
        # Fail-open when no secret configured, but keep hook for wiring.
        return True

    signature_header = request.headers.get("X-Hub-Signature-256") or request.headers.get(
        "x-hub-signature-256"
    )
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    provided_sig = signature_header.split("=", 1)[1].strip()
    expected_sig = hmac.new(
        key=secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Constant-time comparison to avoid timing attacks
    return hmac.compare_digest(provided_sig, expected_sig)


def _to_iso_timestamp(value: Any) -> str:
    if value is None:
        return datetime.utcnow().isoformat()
    try:
        ts = int(value)
        if ts > 10**12:
            ts = int(ts / 1000)
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except Exception:
        return datetime.utcnow().isoformat()


def _iter_whatsapp_messages(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    entries = payload.get("entry", []) or []
    for entry in entries:
        # WhatsApp Cloud API shape
        for change in entry.get("changes", []) or []:
            value = change.get("value") or {}
            for message in value.get("messages", []) or []:
                yield {
                    "source": "cloud",
                    "entry": entry,
                    "change": change,
                    "value": value,
                    "message": message,
                }

        # Legacy/compat Messenger-like shape
        for event in entry.get("messaging", []) or []:
            if event.get("message"):
                yield {
                    "source": "legacy",
                    "entry": entry,
                    "event": event,
                    "message": event.get("message") or {},
                }


async def handle_whatsapp_webhook(request: Request) -> Dict[str, Any]:
    """
    Receive WhatsApp webhook events and forward into the unified inbound gateway.
    """
    try:
        raw_body = await request.body()
        if not _verify_whatsapp_webhook(request, raw_body):
            return {"status": "rejected", "reason": "webhook_verification_failed"}

        try:
            payload: Dict[str, Any] = json.loads(raw_body.decode("utf-8") or "{}")
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {str(exc)}") from exc

        messages = list(_iter_whatsapp_messages(payload))
        if not messages:
            return {"status": "ignored", "reason": "no_message_events"}

        processed = []
        ignored = []

        for item in messages:
            source = item.get("source")
            message = item.get("message") or {}

            if source == "cloud":
                msg_type = message.get("type")
                if msg_type != "text":
                    ignored.append({"reason": f"unsupported_message_type:{msg_type}"})
                    continue
                text_body = (message.get("text") or {}).get("body")
                if not text_body:
                    ignored.append({"reason": "missing_text_body"})
                    continue

                value = item.get("value") or {}
                contacts = value.get("contacts") or []
                sender_id = message.get("from") or (contacts[0].get("wa_id") if contacts else "")

                result = await process_message(
                    platform="whatsapp",
                    user_id=str(sender_id or ""),
                    message=text_body,
                    timestamp=_to_iso_timestamp(message.get("timestamp")),
                    metadata={
                        "provider": "whatsapp",
                        "source": "cloud",
                        "message_id": message.get("id"),
                        "contacts": contacts,
                        "metadata": value.get("metadata"),
                        "event": item,
                    },
                    device="mobile",
                    preferred_language="auto",
                    voice_input=False,
                )
                processed.append(result)
                continue

            # Legacy webhook payloads
            text_value = message.get("text")
            if isinstance(text_value, dict):
                text_value = text_value.get("body")
            if not text_value:
                ignored.append({"reason": "missing_text_body"})
                continue

            event = item.get("event") or {}
            sender_id = (event.get("sender") or {}).get("id", "")

            result = await process_message(
                platform="whatsapp",
                user_id=str(sender_id or ""),
                message=str(text_value),
                timestamp=_to_iso_timestamp(event.get("timestamp")),
                metadata={"provider": "whatsapp", "source": "legacy", "event": event},
                device="mobile",
                preferred_language="auto",
                voice_input=False,
            )
            processed.append(result)

        if not processed:
            return {"status": "ignored", "reason": "no_supported_messages", "ignored": ignored}

        return {
            "status": "processed",
            "count": len(processed),
            "trace_id": processed[0].get("trace_id"),
            "processed_at": datetime.utcnow().isoformat(),
            "ignored": ignored,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(exc)}") from exc
