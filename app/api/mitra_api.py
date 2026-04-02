from __future__ import annotations

from typing import Literal, Optional, Union

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.logging import get_logger
from app.services.mitra_control_plane_service import MitraAuthorityInput, MitraControlPlaneService


router = APIRouter()
logger = get_logger(__name__)
control_plane_service = MitraControlPlaneService()


class MitraEvent(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[float] = None


class MitraEvaluateContext(BaseModel):
    platform: str = "samachar"
    device: str = "api"
    session_id: Optional[str] = None
    voice_input: bool = False
    preferred_language: Optional[str] = "auto"
    age_gate_status: bool = False
    region_policy: Optional[dict] = None
    authenticated_user_context: Optional[dict] = None
    system_context: Optional[dict] = None


class MitraEvaluateRequest(BaseModel):
    event: Optional[MitraEvent] = None
    user_id: Optional[str] = None
    context: Optional[MitraEvaluateContext] = None


class MitraEvaluateResponse(BaseModel):
    status: Literal["ALLOW", "FLAG", "BLOCK"]
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    reason: str
    confidence: float
    trace_id: str
    signal_type: Optional[
        Literal["correction", "intent_refinement", "implicit_positive", "implicit_negative"]
    ] = None
    system_context: Optional[dict] = None


class MitraEvaluateError(BaseModel):
    error: str


def _normalize_text(value: Optional[str]) -> str:
    return (value or "").strip()


def _build_event_text(event: MitraEvent) -> str:
    title = _normalize_text(event.title)
    content = _normalize_text(event.content)
    if title and content:
        return f"{title}\n\n{content}"
    return title or content


def _build_error(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message})


@router.post(
    "/api/mitra/evaluate",
    response_model=Union[MitraEvaluateResponse, MitraEvaluateError],
)
async def evaluate_mitra_event(
    request: MitraEvaluateRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    _ = x_api_key
    event = request.event
    if event is None:
        return _build_error("Missing event payload.", 400)

    event_text = _build_event_text(event)
    if not event_text:
        return _build_error("Event title or content is required.", 400)

    category = _normalize_text(event.category)
    request_context = request.context or MitraEvaluateContext()
    authenticated_user_context = dict(request_context.authenticated_user_context or {})
    resolved_user_id = _normalize_text(request.user_id) or _normalize_text(x_user_id) or "api_key_user"
    authenticated_user_context.setdefault("principal", resolved_user_id)
    authenticated_user_context.setdefault("auth_method", "api_key")
    authenticated_user_context.setdefault("platform", request_context.platform)
    authenticated_user_context.setdefault("device", request_context.device)
    if request_context.session_id:
        authenticated_user_context.setdefault("session_id", request_context.session_id)

    try:
        authority_result = control_plane_service.evaluate(
            MitraAuthorityInput(
                input_text=event_text,
                raw_input=request.model_dump(),
                category=category,
                request_confidence=event.confidence,
                user_id=resolved_user_id,
                session_id=request_context.session_id,
                platform=request_context.platform,
                device=request_context.device,
                voice_input=request_context.voice_input,
                preferred_language=request_context.preferred_language,
                authenticated_user_context=authenticated_user_context,
                system_context=request_context.system_context,
                trace_seed_payload=request.model_dump(),
                source="/api/mitra/evaluate",
                age_gate_status=request_context.age_gate_status,
                region_policy=request_context.region_policy,
            )
        )
        return authority_result["response_contract"]
    except Exception as exc:
        logger.exception("Mitra evaluation failed for user_id=%s", resolved_user_id)
        return _build_error(f"Mitra pipeline failed: {exc}", 500)
