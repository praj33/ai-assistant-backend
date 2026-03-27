from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional, Union

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.logging import get_logger
from app.external.enforcement.deterministic_trace import generate_trace_id
from app.karma_adapter import fetch_user_karma, karma_bias_from_points
from app.mitra_system_registry import mitra_registry


router = APIRouter()
logger = get_logger(__name__)

safety_service = mitra_registry.safety_service
intelligence_service = mitra_registry.intelligence_service
enforcement_service = mitra_registry.enforcement_service
bucket_service = mitra_registry.bucket_service


class MitraEvent(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[float] = None


class MitraEvaluateRequest(BaseModel):
    event: Optional[MitraEvent] = None


class MitraEvaluateResponse(BaseModel):
    status: Literal["ALLOW", "FLAG", "BLOCK"]
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    reason: str
    confidence: float


class MitraEvaluateError(BaseModel):
    error: str


_REASON_BY_CODE = {
    "CONTENT_AND_ACTION_ALLOWED": "Content passed existing safety validation and enforcement checks.",
    "SAFE_REWRITE_REQUIRED": "Content triggered existing rewrite safeguards.",
    "POLICY_VIOLATION": "Content violated existing safety policies.",
    "MISSING_MEDIATION": "Pipeline failed closed because required safety mediation was missing.",
    "TRACE_MISMATCH": "Pipeline failed closed because the safety and enforcement traces did not match.",
    "MISSING_BUCKET_ARTIFACT": "Pipeline failed closed because the safety artifact was missing.",
    "GLOBAL_KILL_SWITCH": "Pipeline terminated because the global kill switch is active.",
    "AKANKSHA_VALIDATION_FAILED": "Pipeline terminated because safety validation failed inside enforcement.",
    "SYSTEM_TERMINATION": "Pipeline terminated by the enforcement runtime.",
}


def _normalize_text(value: Optional[str]) -> str:
    return (value or "").strip()


def _coerce_float(value: object) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp_confidence(value: Optional[float]) -> float:
    if value is None:
        return 0.0
    normalized = value / 100.0 if value > 1.0 else value
    return round(max(0.0, min(1.0, normalized)), 4)


def _build_event_text(event: MitraEvent) -> str:
    title = _normalize_text(event.title)
    content = _normalize_text(event.content)
    if title and content:
        return f"{title}\n\n{content}"
    return title or content


def _build_trace_payload(event: MitraEvent) -> dict:
    return {
        "event": {
            "title": _normalize_text(event.title),
            "content": _normalize_text(event.content),
            "category": _normalize_text(event.category),
            "confidence": _clamp_confidence(_coerce_float(event.confidence)),
        }
    }


def _build_platform_policy(category: str) -> dict:
    policy = {
        "platform": "samachar",
        "device": "api",
        "source": "samachar",
    }
    if category:
        policy["event_category"] = category
    return policy


def _map_status(enforcement_decision: str) -> Literal["ALLOW", "FLAG", "BLOCK"]:
    if enforcement_decision in {"BLOCK", "TERMINATE"}:
        return "BLOCK"
    if enforcement_decision == "REWRITE":
        return "FLAG"
    return "ALLOW"


def _map_risk_level(
    *,
    enforcement_decision: str,
    safety_decision: str,
) -> Literal["LOW", "MEDIUM", "HIGH"]:
    if enforcement_decision in {"BLOCK", "TERMINATE"} or safety_decision == "hard_deny":
        return "HIGH"
    if enforcement_decision == "REWRITE" or safety_decision == "soft_rewrite":
        return "MEDIUM"
    return "LOW"


def _build_reason(status: str, safety_result: dict, enforcement_result: dict) -> str:
    explanation = str(safety_result.get("explanation") or "").strip()
    if status in {"FLAG", "BLOCK"} and explanation:
        return explanation

    reason_code = str(enforcement_result.get("reason_code") or "").strip()
    if reason_code in _REASON_BY_CODE:
        return _REASON_BY_CODE[reason_code]

    if explanation:
        return explanation

    if status == "ALLOW":
        return _REASON_BY_CODE["CONTENT_AND_ACTION_ALLOWED"]
    if status == "FLAG":
        return _REASON_BY_CODE["SAFE_REWRITE_REQUIRED"]
    return _REASON_BY_CODE["POLICY_VIOLATION"]


def _build_error(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message})


@router.post(
    "/api/mitra/evaluate",
    response_model=Union[MitraEvaluateResponse, MitraEvaluateError],
)
async def evaluate_mitra_event(
    request: MitraEvaluateRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    _ = x_api_key
    event = request.event
    if event is None:
        return _build_error("Missing event payload.", 400)

    event_text = _build_event_text(event)
    if not event_text:
        return _build_error("Event title or content is required.", 400)

    category = _normalize_text(event.category)
    trace_id = generate_trace_id(
        input_payload=_build_trace_payload(event),
        enforcement_category="REQUEST",
    )

    try:
        bucket_service.log_event(
            trace_id,
            "request_received",
            {
                "trace_id": trace_id,
                "event": event.model_dump(),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )

        karma_data = fetch_user_karma(None)
        karma_points = int(karma_data.get("karma_points", 50))
        platform_policy = _build_platform_policy(category)

        safety_result = safety_service.validate_content(
            content=event_text,
            trace_id=trace_id,
            context={
                "age_gate_status": False,
                "region_rule_status": None,
                "platform_policy_state": platform_policy,
                "karma_bias_input": karma_bias_from_points(karma_points),
            },
        )
        bucket_service.log_event(trace_id, "safety_validation", safety_result)

        intelligence_result = intelligence_service.process_interaction(
            context={
                "user_input": event_text,
                "platform": "samachar",
                "device": "api",
                "session_id": trace_id,
                "category": category,
                "samachar_confidence": _clamp_confidence(_coerce_float(event.confidence)),
                "karma_data": karma_data,
            },
            trace_id=trace_id,
        )
        intelligence_result.setdefault("karma_score", karma_points)
        bucket_service.log_event(trace_id, "intelligence_processing", intelligence_result)

        raw_risk_flags = intelligence_result.get("risk_flags", [])
        if isinstance(raw_risk_flags, str):
            risk_flags = [raw_risk_flags]
        elif isinstance(raw_risk_flags, list):
            risk_flags = raw_risk_flags
        else:
            risk_flags = [raw_risk_flags] if raw_risk_flags else []

        enforcement_result = enforcement_service.enforce_policy(
            payload={
                "safety": safety_result,
                "intelligence": intelligence_result,
                "user_input": event_text,
                "emotional_output": event_text,
                "intent": category or intelligence_result.get("intent") or "general",
                "trace_id": trace_id,
                "age_gate_status": False,
                "region_policy": None,
                "platform_policy": platform_policy,
                "karma_score": intelligence_result.get("karma_score", karma_points),
                "risk_flags": risk_flags,
                "authenticated_user_context": {
                    "platform": "samachar",
                    "device": "api",
                    "session_id": trace_id,
                },
                "user_context": {
                    "platform": "samachar",
                    "device": "api",
                    "session_id": trace_id,
                },
            },
            trace_id=trace_id,
        )
        bucket_service.log_event(trace_id, "enforcement_decision", enforcement_result)

        status = _map_status(str(enforcement_result.get("decision") or "BLOCK").upper())
        return {
            "status": status,
            "risk_level": _map_risk_level(
                enforcement_decision=str(enforcement_result.get("decision") or "BLOCK").upper(),
                safety_decision=str(safety_result.get("decision") or ""),
            ),
            "reason": _build_reason(status, safety_result, enforcement_result),
            "confidence": _clamp_confidence(
                _coerce_float(safety_result.get("confidence"))
                if safety_result.get("confidence") is not None
                else _coerce_float(event.confidence)
            ),
        }
    except Exception as exc:
        logger.exception("Mitra evaluation failed for trace_id=%s", trace_id)
        return _build_error(f"Mitra pipeline failed: {exc}", 500)
