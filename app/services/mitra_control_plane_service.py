from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any, Dict, Literal, Optional

from app.core.mitra_entry_guard import mitra_enforcement_scope
from app.external.enforcement.deterministic_trace import generate_trace_id
from app.karma_adapter import fetch_user_karma, karma_bias_from_points
from app.mitra_system_registry import mitra_registry


SignalType = Literal[
    "correction",
    "intent_refinement",
    "implicit_positive",
    "implicit_negative",
]


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

_CORRECTION_MARKERS = (
    "actually",
    "correction",
    "i meant",
    "i mean",
    "instead",
    "not that",
    "that's wrong",
    "that is wrong",
    "to correct",
)
_REFINEMENT_MARKERS = (
    "for example",
    "in other words",
    "let me rephrase",
    "more specifically",
    "to clarify",
)


def _normalize_text(value: Optional[str]) -> str:
    return (value or "").strip()


def _normalize_identity(value: Optional[str], fallback: str) -> str:
    normalized = _normalize_text(value)
    return normalized or fallback


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


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _text_similarity(left: str, right: str) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left.lower(), right.lower()).ratio()


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


@dataclass(frozen=True)
class MitraAuthorityInput:
    input_text: str
    raw_input: Dict[str, Any]
    category: str = ""
    request_confidence: Optional[float] = None
    user_id: str = "anonymous"
    session_id: Optional[str] = None
    platform: str = "samachar"
    device: str = "api"
    voice_input: bool = False
    preferred_language: Optional[str] = None
    authenticated_user_context: Optional[Dict[str, Any]] = None
    system_context: Optional[Dict[str, Any]] = None
    trace_seed_payload: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    source: str = "/api/mitra/evaluate"
    age_gate_status: bool = False
    region_policy: Optional[Dict[str, Any]] = None


class MitraControlPlaneService:
    def __init__(self) -> None:
        self.safety_service = mitra_registry.safety_service
        self.intelligence_service = mitra_registry.intelligence_service
        self.enforcement_service = mitra_registry.enforcement_service
        self.bucket_service = mitra_registry.bucket_service

    @staticmethod
    def _build_platform_policy(authority_input: MitraAuthorityInput) -> Dict[str, Any]:
        platform_policy = {
            "platform": authority_input.platform,
            "device": authority_input.device,
            "source": authority_input.source,
        }
        if authority_input.category:
            platform_policy["event_category"] = authority_input.category
        if authority_input.authenticated_user_context:
            platform_policy["authenticated_user_context"] = authority_input.authenticated_user_context
        return platform_policy

    @staticmethod
    def _build_trace_seed_payload(authority_input: MitraAuthorityInput) -> Dict[str, Any]:
        return {
            "input": authority_input.raw_input,
            "user_id": authority_input.user_id,
            "session_id": authority_input.session_id or "",
            "platform": authority_input.platform,
            "device": authority_input.device,
            "voice_input": bool(authority_input.voice_input),
            "source": authority_input.source,
        }

    @staticmethod
    def _build_system_context(
        authority_input: MitraAuthorityInput,
        *,
        enforcement_trace_id: Optional[str],
    ) -> Dict[str, Any]:
        context: Dict[str, Any] = {
            "platform": authority_input.platform,
            "device": authority_input.device,
            "session_id": authority_input.session_id or authority_input.user_id,
            "user_id": authority_input.user_id,
            "voice_input": bool(authority_input.voice_input),
            "preferred_language": authority_input.preferred_language or "auto",
            "source": authority_input.source,
        }
        if authority_input.category:
            context["category"] = authority_input.category
        if enforcement_trace_id:
            context["enforcement_trace_id"] = enforcement_trace_id
        if authority_input.system_context:
            for key, value in authority_input.system_context.items():
                if key not in context and value is not None:
                    context[key] = value
        return context

    @staticmethod
    def _extract_prior_text(prior_request: Optional[Dict[str, Any]]) -> str:
        if not prior_request:
            return ""
        data = prior_request.get("data") or {}
        prior_input = data.get("input")
        if isinstance(prior_input, dict):
            return _normalize_text(prior_input.get("text"))
        return _normalize_text(str(prior_input or ""))

    @staticmethod
    def _extract_prior_category(prior_request: Optional[Dict[str, Any]]) -> str:
        if not prior_request:
            return ""
        data = prior_request.get("data") or {}
        prior_input = data.get("input")
        if isinstance(prior_input, dict):
            return _normalize_text(prior_input.get("category"))
        return ""

    def _resolve_signal(
        self,
        *,
        trace_id: str,
        authority_input: MitraAuthorityInput,
    ) -> Dict[str, Any]:
        prior_requests = self.bucket_service.find_recent_stage_events(
            "mitra_request_log",
            user_id=authority_input.user_id,
            session_id=authority_input.session_id,
            exclude_trace_id=trace_id,
            limit=1,
        )
        prior_request = prior_requests[0] if prior_requests else None
        current_text = authority_input.input_text
        current_lower = current_text.lower()
        previous_text = self._extract_prior_text(prior_request)
        previous_category = self._extract_prior_category(prior_request)
        similarity = _text_similarity(current_text, previous_text)
        token_overlap = len(_tokenize(current_text) & _tokenize(previous_text))

        signal_type: SignalType
        confidence: float

        correction_starts = current_lower.startswith(("no ", "no,", "actually ", "i meant ", "instead "))
        correction_contains = any(marker in current_lower for marker in _CORRECTION_MARKERS)
        if previous_text and (correction_starts or correction_contains):
            signal_type = "correction"
            confidence = 0.97 if correction_starts else 0.93
        elif previous_text and (
            any(marker in current_lower for marker in _REFINEMENT_MARKERS)
            or (0.35 <= similarity <= 0.9 and token_overlap >= 2)
        ):
            signal_type = "intent_refinement"
            confidence = 0.88
        elif previous_text and (
            similarity < 0.45
            and token_overlap <= 1
            and authority_input.category != previous_category
        ):
            signal_type = "implicit_negative"
            confidence = 0.84
        else:
            signal_type = "implicit_positive"
            confidence = 0.72 if previous_text else 0.65

        return {
            "signal_type": signal_type,
            "confidence": confidence,
            "trace_id": trace_id,
            "session_id": authority_input.session_id or authority_input.user_id,
            "user_id": authority_input.user_id,
            "basis": {
                "previous_trace_id": (prior_request or {}).get("trace_id"),
                "similarity": round(similarity, 4),
                "token_overlap": token_overlap,
                "previous_category": previous_category or None,
                "current_category": authority_input.category or None,
            },
        }

    def evaluate(self, authority_input: MitraAuthorityInput) -> Dict[str, Any]:
        input_text = _normalize_text(authority_input.input_text)
        if not input_text:
            raise ValueError("Input text is required for Mitra control plane evaluation.")

        user_id = _normalize_identity(authority_input.user_id, "anonymous")
        session_id = _normalize_identity(authority_input.session_id, user_id)

        resolved_input = MitraAuthorityInput(
            input_text=input_text,
            raw_input=authority_input.raw_input,
            category=_normalize_text(authority_input.category),
            request_confidence=authority_input.request_confidence,
            user_id=user_id,
            session_id=session_id,
            platform=_normalize_identity(authority_input.platform, "samachar"),
            device=_normalize_identity(authority_input.device, "api"),
            voice_input=bool(authority_input.voice_input),
            preferred_language=authority_input.preferred_language,
            authenticated_user_context=authority_input.authenticated_user_context or {},
            system_context=authority_input.system_context or {},
            trace_seed_payload=authority_input.trace_seed_payload,
            trace_id=_normalize_text(authority_input.trace_id) or None,
            source=_normalize_identity(authority_input.source, "/api/mitra/evaluate"),
            age_gate_status=bool(authority_input.age_gate_status),
            region_policy=authority_input.region_policy,
        )

        trace_id = resolved_input.trace_id or generate_trace_id(
            input_payload=resolved_input.trace_seed_payload or self._build_trace_seed_payload(resolved_input),
            enforcement_category="REQUEST",
        )
        timestamp = datetime.utcnow().isoformat() + "Z"
        platform_policy = self._build_platform_policy(resolved_input)
        karma_data = fetch_user_karma(
            resolved_input.authenticated_user_context.get("principal")
            if isinstance(resolved_input.authenticated_user_context, dict)
            else None
        )
        karma_points = int(karma_data.get("karma_points", 50))

        request_received = {
            "trace_id": trace_id,
            "user_id": resolved_input.user_id,
            "session_id": resolved_input.session_id,
            "input": resolved_input.raw_input,
            "input_text": resolved_input.input_text,
            "platform": resolved_input.platform,
            "device": resolved_input.device,
            "voice_input": resolved_input.voice_input,
            "timestamp": timestamp,
        }
        self.bucket_service.log_event(trace_id, "request_received", request_received)

        safety_result = self.safety_service.validate_content(
            content=resolved_input.input_text,
            trace_id=trace_id,
            context={
                "age_gate_status": resolved_input.age_gate_status,
                "region_rule_status": resolved_input.region_policy,
                "platform_policy_state": platform_policy,
                "karma_bias_input": karma_bias_from_points(karma_points),
            },
        )
        self.bucket_service.log_event(trace_id, "safety_validation", safety_result)

        intelligence_result = self.intelligence_service.process_interaction(
            context={
                "user_input": resolved_input.input_text,
                "platform": resolved_input.platform,
                "device": resolved_input.device,
                "session_id": resolved_input.session_id,
                "category": resolved_input.category,
                "voice_input": resolved_input.voice_input,
                "preferred_language": resolved_input.preferred_language,
                "karma_data": karma_data,
            },
            trace_id=trace_id,
        )
        intelligence_result.setdefault("karma_score", karma_points)
        self.bucket_service.log_event(trace_id, "intelligence_processing", intelligence_result)

        raw_risk_flags = intelligence_result.get("risk_flags", [])
        if isinstance(raw_risk_flags, str):
            risk_flags = [raw_risk_flags]
        elif isinstance(raw_risk_flags, list):
            risk_flags = raw_risk_flags
        else:
            risk_flags = [raw_risk_flags] if raw_risk_flags else []

        with mitra_enforcement_scope(trace_id=trace_id, source=resolved_input.source):
            enforcement_result = self.enforcement_service.enforce_policy(
                payload={
                    "safety": safety_result,
                    "intelligence": intelligence_result,
                    "user_input": resolved_input.input_text,
                    "emotional_output": resolved_input.input_text,
                    "intent": resolved_input.category or intelligence_result.get("intent") or "general",
                    "trace_id": trace_id,
                    "age_gate_status": resolved_input.age_gate_status,
                    "region_policy": resolved_input.region_policy,
                    "platform_policy": platform_policy,
                    "karma_score": intelligence_result.get("karma_score", karma_points),
                    "risk_flags": risk_flags,
                    "authenticated_user_context": resolved_input.authenticated_user_context,
                    "user_context": resolved_input.authenticated_user_context,
                },
                trace_id=trace_id,
            )
        self.bucket_service.log_event(trace_id, "enforcement_decision", enforcement_result)

        status = _map_status(str(enforcement_result.get("decision") or "BLOCK").upper())
        risk_level = _map_risk_level(
            enforcement_decision=str(enforcement_result.get("decision") or "BLOCK").upper(),
            safety_decision=str(safety_result.get("decision") or ""),
        )
        signal_record = self._resolve_signal(trace_id=trace_id, authority_input=resolved_input)
        self.bucket_service.log_event(trace_id, "rl_signal_capture", signal_record)

        system_context = self._build_system_context(
            resolved_input,
            enforcement_trace_id=str(enforcement_result.get("trace_id") or "").strip() or None,
        )
        response_contract: Dict[str, Any] = {
            "status": status,
            "risk_level": risk_level,
            "reason": _build_reason(status, safety_result, enforcement_result),
            "confidence": _clamp_confidence(
                _coerce_float(safety_result.get("confidence"))
                if safety_result.get("confidence") is not None
                else _coerce_float(resolved_input.request_confidence)
            ),
            "trace_id": trace_id,
            "signal_type": signal_record["signal_type"],
            "system_context": system_context,
        }

        request_log = {
            "user_id": resolved_input.user_id,
            "session_id": resolved_input.session_id,
            "input": {
                "text": resolved_input.input_text,
                "category": resolved_input.category,
                "raw_input": resolved_input.raw_input,
            },
            "mitra_output": response_contract,
            "trace_id": trace_id,
            "timestamp": timestamp,
        }
        self.bucket_service.log_event(trace_id, "mitra_request_log", request_log)
        self.bucket_service.log_event(trace_id, "mitra_response_contract", response_contract)

        return {
            "trace_id": trace_id,
            "response_contract": response_contract,
            "signal_record": signal_record,
            "safety_result": safety_result,
            "intelligence_result": intelligence_result,
            "enforcement_result": enforcement_result,
            "system_context": system_context,
        }
