from __future__ import annotations

from typing import Any, Dict

from fastapi import Request

from app.inbound.whatsapp_inbound_handler import handle_whatsapp_webhook as _handle_whatsapp_webhook


async def handle_whatsapp_webhook(request: Request) -> Dict[str, Any]:
    """
    Memory-layer shim that delegates to the primary WhatsApp webhook handler.
    """
    return await _handle_whatsapp_webhook(request)
