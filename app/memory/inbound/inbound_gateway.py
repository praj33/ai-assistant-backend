from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from app.core.assistant_orchestrator import handle_assistant_request
from app.services.bucket_service import BucketService
from app.services.inbound_mediation_service import InboundMediationService, InboundDecision
from app.services.unified_schema_service import build_inbound_payload


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

    metadata = metadata or {}
    original_message = message

    mediation_service = InboundMediationService()
    mediation_result: Dict[str, Any] | None = None
    if mediation_service.is_enabled_for_platform(platform):
        mediation = mediation_service.evaluate(
            content=original_message,
            sender_id=str(metadata.get("sender_id") or user_id or ""),
            recipient_id=str(metadata.get("recipient_id") or "assistant"),
            platform=platform,
            timestamp=timestamp,
        )
        mediation_result = mediation.to_dict()
        BucketService().log_event(
            mediation.trace_id,
            "inbound_mediation",
            {
                "platform": platform,
                "user_id": str(user_id or ""),
                "decision": mediation_result.get("decision"),
                "risk_category": mediation_result.get("risk_category"),
                "reason": mediation_result.get("reason"),
                "timestamp": timestamp or datetime.utcnow().isoformat(),
            },
        )

        if mediation.decision in {InboundDecision.SILENCE, InboundDecision.DELAY, InboundDecision.ESCALATE}:
            unified_payload = build_inbound_payload(
                content=original_message,
                source=str(metadata.get("source") or metadata.get("sender") or user_id or ""),
                user_id=str(user_id or ""),
                channel=platform,
                metadata=metadata,
                timestamp=timestamp,
                message_id=metadata.get("message_id"),
            )
            BucketService().log_event(
                mediation.trace_id,
                "inbound_event",
                {
                    "platform": platform,
                    "user_id": str(user_id or ""),
                    "message": original_message,
                    "timestamp": timestamp or datetime.utcnow().isoformat(),
                    "metadata": metadata,
                    "mediation": mediation_result,
                    "unified_payload": unified_payload,
                },
            )
            return {
                "status": mediation.decision.value,
                "reason": mediation_result.get("reason"),
                "trace_id": mediation.trace_id,
                "mediation": mediation_result,
            }

        if mediation.decision == InboundDecision.SUMMARIZE and mediation.safe_summary:
            message = mediation.safe_summary
            metadata = dict(metadata)
            metadata["original_message"] = original_message
            metadata["inbound_mediation"] = mediation_result

    internal_request = _build_internal_request(
        message=message,
        platform=platform,
        device=device,
        session_id=str(user_id or ""),
        voice_input=voice_input,
        preferred_language=preferred_language,
        principal=str(user_id or ""),
        metadata=metadata,
    )

    result = await handle_assistant_request(internal_request)
    trace_id = result.get("trace_id")

    # Log inbound event with trace for observability.
    unified_payload = build_inbound_payload(
        content=original_message,
        source=str(metadata.get("source") or metadata.get("sender") or user_id or ""),
        user_id=str(user_id or ""),
        channel=platform,
        metadata=metadata,
        timestamp=timestamp,
        message_id=metadata.get("message_id"),
    )
    BucketService().log_event(
        trace_id or "trace_missing",
        "inbound_event",
        {
            "platform": platform,
            "user_id": str(user_id or ""),
            "message": message,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "metadata": metadata,
            "mediation": mediation_result,
            "unified_payload": unified_payload,
        },
    )

    return result
