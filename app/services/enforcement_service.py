from datetime import datetime
from types import SimpleNamespace
from typing import Any, Dict

from app.external.enforcement import enforcement_engine


class EnforcementService:
    def __init__(self):
        # Deterministic runtime authority (Raj) - single source of truth
        self.enforcement_engine = enforcement_engine

    @staticmethod
    def _normalize_trace_id(value: Any) -> str | None:
        if value is None:
            return None
        trace_id = str(value).strip()
        return trace_id or None

    @staticmethod
    def _compose_platform_policy(payload: Dict[str, Any]) -> Any:
        platform_policy = payload.get("platform_policy")
        authenticated_user_context = (
            payload.get("authenticated_user_context")
            or payload.get("user_context")
        )

        if platform_policy and authenticated_user_context:
            if isinstance(platform_policy, dict):
                merged_policy = dict(platform_policy)
            else:
                merged_policy = {"platform_policy": platform_policy}
            merged_policy["authenticated_user_context"] = authenticated_user_context
            return merged_policy

        return platform_policy or authenticated_user_context

    @staticmethod
    def _extract_risk_flags(payload: Dict[str, Any], intelligence: Dict[str, Any]) -> list[Any]:
        risk_flags = payload.get("risk_flags")
        if risk_flags is None:
            risk_flags = intelligence.get("risk_flags") or []
        if isinstance(risk_flags, str):
            return [risk_flags]
        if isinstance(risk_flags, list):
            return risk_flags
        return [risk_flags]

    @staticmethod
    def _normalize_karma_score(payload: Dict[str, Any], intelligence: Dict[str, Any]) -> int:
        raw_value = payload.get("karma_score")
        if raw_value is None:
            raw_value = intelligence.get("karma_score")
        if isinstance(raw_value, bool):
            return int(raw_value)
        if isinstance(raw_value, (int, float)):
            return int(raw_value)
        return 50

    def _bucket_preconditions(self, trace_id: str | None) -> Dict[str, Any]:
        from app.services.bucket_service import BucketService

        bucket = BucketService()
        bucket_active = bucket.enforcement_artifact_required()
        artifact_present = bool(trace_id) and bucket.artifact_exists(trace_id, stage="safety_validation")
        return {
            "bucket_active": bucket_active,
            "mediation_artifact_present": artifact_present,
        }

    def enforce_policy(self, payload: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        """
        Runtime enforcement entrypoint.
        Converts the runtime payload dict into the deterministic engine's expected input shape,
        calls Raj's `enforcement_engine.enforce()`, then adapts the verdict to the dict
        surface consumed by the orchestrator.
        """
        safety = payload.get("safety") or {}
        intelligence = payload.get("intelligence") or {}
        request_trace_id = self._normalize_trace_id(trace_id)
        mediation_trace_id = self._normalize_trace_id(
            safety.get("trace_id") if isinstance(safety, dict) else None
        )
        bucket_preconditions = self._bucket_preconditions(request_trace_id)

        input_payload = SimpleNamespace(
            intent=payload.get("intent") or intelligence.get("intent") or "general",
            emotional_output=(
                payload.get("emotional_output")
                or payload.get("user_input")
                or payload.get("text")
                or ""
            ),
            age_gate_status=bool(payload.get("age_gate_status", False)),
            region_policy=payload.get("region_policy"),
            platform_policy=self._compose_platform_policy(payload),
            karma_score=self._normalize_karma_score(payload, intelligence),
            risk_flags=self._extract_risk_flags(payload, intelligence),
            trace_id=request_trace_id,
            akanksha_validation=safety if isinstance(safety, dict) else None,
            mediation_decision=safety.get("decision") if isinstance(safety, dict) else None,
            mediation_trace_id=mediation_trace_id,
            authenticated_user_context=payload.get("authenticated_user_context") or payload.get("user_context"),
            bucket_active=bucket_preconditions["bucket_active"],
            mediation_artifact_present=bucket_preconditions["mediation_artifact_present"],
        )

        verdict = self.enforcement_engine.enforce(input_payload)

        result: Dict[str, Any] = {
            "decision": getattr(verdict, "decision", "BLOCK"),
            "scope": getattr(verdict, "scope", "both"),
            "trace_id": getattr(verdict, "trace_id", request_trace_id or trace_id),
            "reason_code": getattr(verdict, "reason_code", "UNKNOWN"),
            "request_trace_id": getattr(verdict, "request_trace_id", request_trace_id),
            "timestamp": datetime.utcnow().isoformat(),
        }

        rewrite_class = getattr(verdict, "rewrite_class", None)
        if rewrite_class:
            result["rewrite_class"] = rewrite_class

        safe_output = getattr(verdict, "safe_output", None)
        if safe_output:
            result["safe_output"] = safe_output
            result["rewritten_output"] = safe_output

        return result

    def get_status(self) -> Dict[str, Any]:
        return {"service": "enforcement_service", "status": "active"}
