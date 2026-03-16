from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from app.core.assistant_orchestrator import handle_assistant_request
from app.services.bucket_service import BucketService


def _build_internal_request(
    *,
    message: str,
    platform: str,
    device: str,
    session_id: str,
    voice_input: bool,
    preferred_language: str = "auto",
    principal: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    authenticated_user_context = {
        "auth_method": f"{platform}_inbound",
        "principal": principal or session_id or f"{platform}_anonymous",
        "platform": platform,
        "device": device,
    }
    if session_id:
        authenticated_user_context["session_id"] = str(session_id)

    context = {
        "platform": platform,
        "device": device,
        "session_id": str(session_id or ""),
        "voice_input": voice_input,
        "preferred_language": preferred_language,
        "detected_language": None,
        "authenticated_user_context": authenticated_user_context,
        "user_context": authenticated_user_context,
    }
    if metadata:
        context["inbound_metadata"] = metadata

    return {
        "version": "3.0.0",
        "input": {"message": message},
        "context": context,
    }


async def process_message(
    *,
    platform: str,
    user_id: str,
    message: str,
    timestamp: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    device: str = "unknown",
    preferred_language: str = "auto",
    voice_input: bool = False,
) -> Dict[str, Any]:
    """
    Normalize inbound events and route into the full Mitra pipeline:
    Safety -> Intelligence -> Enforcement -> Orchestrator -> Execution.
    """
    if not message:
        return {"status": "ignored", "reason": "empty_message"}

    internal_request = _build_internal_request(
        message=message,
        platform=platform,
        device=device,
        session_id=str(user_id or ""),
        voice_input=voice_input,
        preferred_language=preferred_language,
        principal=str(user_id or ""),
        metadata=metadata or {},
    )

    result = await handle_assistant_request(internal_request)
    trace_id = result.get("trace_id")

    # Log inbound event with trace for observability.
    BucketService().log_event(
        trace_id or "trace_missing",
        "inbound_event",
        {
            "platform": platform,
            "user_id": str(user_id or ""),
            "message": message,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        },
    )

    return result
