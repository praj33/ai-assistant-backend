"""
Akanksha validator adapter for Raj's deterministic enforcement engine.

The deterministic engine requires an adapter that returns:
- decision: EXECUTE | REWRITE | BLOCK
- risk_category
- confidence

This adapter bridges to the existing SafetyService (behavior validator).
If validation fails for any reason, it raises to force TERMINATE (fail-closed).
"""

from __future__ import annotations

import os
from typing import Any, Dict


class EnforcementAdapter:
    def validate(self, input_payload: Any) -> Dict[str, Any]:
        # Optional failure injection for tests
        if os.getenv("AKANKSHA_VALIDATOR_FAIL", "").strip().lower() in {"1", "true", "yes"}:
            raise RuntimeError("Injected Akanksha validator failure")

        prevalidated = getattr(input_payload, "akanksha_validation", None)
        if isinstance(prevalidated, dict):
            result = prevalidated
        else:
            from app.services.safety_service import SafetyService

            text = getattr(input_payload, "emotional_output", None) or ""
            trace_id = getattr(input_payload, "trace_id", None) or "trace_unknown"
            result = SafetyService().validate_content(content=text, trace_id=trace_id)

        safety_decision = result.get("decision")
        if safety_decision == "hard_deny":
            decision = "BLOCK"
        elif safety_decision == "soft_rewrite":
            decision = "REWRITE"
        else:
            decision = "EXECUTE"

        return {
            "decision": decision,
            "risk_category": result.get("risk_category"),
            "confidence": result.get("confidence"),
            "safe_output": result.get("safe_output"),
        }
