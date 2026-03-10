from datetime import datetime
from types import SimpleNamespace
from typing import Any, Dict

from app.external.enforcement import enforcement_engine


class EnforcementService:
    def __init__(self):
        # Deterministic runtime authority (Raj) - single source of truth
        self.enforcement_engine = enforcement_engine

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
    def _extract_risk_flags(payload: Dict[str, Any]) -> list[Any]:
        risk_flags = payload.get("risk_flags") or []
        if isinstance(risk_flags, str):
            return [risk_flags]
        if isinstance(risk_flags, list):
            return risk_flags
        return [risk_flags]

    def enforce_policy(self, payload: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        """
        Runtime enforcement entrypoint.
        Converts the runtime payload dict into the deterministic engine's expected input shape,
        calls Raj's `enforcement_engine.enforce()`, then adapts the verdict to the dict
        surface consumed by the orchestrator.
        """
        safety = payload.get("safety") or {}
        intelligence = payload.get("intelligence") or {}

        input_payload = SimpleNamespace(
            intent=payload.get("intent") or intelligence.get("intent") or "general",
            emotional_output=payload.get("user_input") or payload.get("text") or "",
            age_gate_status=bool(payload.get("age_gate_status", False)),
            region_policy=payload.get("region_policy"),
            platform_policy=self._compose_platform_policy(payload),
            karma_score=intelligence.get("karma_score") or payload.get("karma_score") or 0,
            risk_flags=self._extract_risk_flags(payload),
            trace_id=trace_id,
            akanksha_validation=safety if isinstance(safety, dict) else None,
            authenticated_user_context=payload.get("authenticated_user_context") or payload.get("user_context"),
        )

        verdict = self.enforcement_engine.enforce(input_payload)

        result: Dict[str, Any] = {
            "decision": getattr(verdict, "decision", "BLOCK"),
            "scope": getattr(verdict, "scope", "both"),
            "trace_id": getattr(verdict, "trace_id", trace_id),
            "reason_code": getattr(verdict, "reason_code", "UNKNOWN"),
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
