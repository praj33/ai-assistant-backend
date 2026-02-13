"""
Simplified Enforcement Engine Wrapper
"""
from typing import Dict, Any
from datetime import datetime
import uuid

class EnforcementVerdict:
    def __init__(self, decision: str, scope: str, trace_id: str, reason_code: str, rewrite_class: str = None):
        self.decision = decision
        self.scope = scope
        self.trace_id = trace_id
        self.reason_code = reason_code
        self.rewrite_class = rewrite_class
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "decision": self.decision,
            "scope": self.scope,
            "trace_id": self.trace_id,
            "reason_code": self.reason_code,
            "timestamp": datetime.utcnow().isoformat()
        }
        if self.rewrite_class:
            result["rewrite_class"] = self.rewrite_class
        return result

class EnforcementEngine:
    def __init__(self):
        pass
    
    def enforce(self, payload: Dict[str, Any]) -> EnforcementVerdict:
        """Enforcement with proper safety decision handling"""
        trace_id = payload.get("trace_id", str(uuid.uuid4()))
        
        # Check safety decision first
        safety_result = payload.get("safety", {})
        safety_decision = safety_result.get("decision")
        safety_risk_category = str(safety_result.get("risk_category", "")).lower()
        safety_reason_code = str(safety_result.get("reason_code", "")).lower()
        safety_patterns = " ".join(safety_result.get("matched_patterns", [])).lower()

        # Defense-in-depth: self-harm/suicide signals can never resolve to ALLOW.
        self_harm_signal = any(
            token in f"{safety_risk_category} {safety_reason_code} {safety_patterns}"
            for token in ["self_harm", "suicide", "suicidal", "kill myself", "end my life", "want to die"]
        )
        if self_harm_signal:
            return EnforcementVerdict(
                decision="BLOCK",
                scope="both",
                trace_id=trace_id,
                reason_code="SELF_HARM_BLOCK"
            )
        
        # If safety says hard_deny, block immediately
        if safety_decision == "hard_deny":
            return EnforcementVerdict(
                decision="BLOCK",
                scope="both",
                trace_id=trace_id,
                reason_code="SAFETY_HARD_DENY"
            )
        
        # If safety says soft_rewrite, enforce rewrite
        if safety_decision == "soft_rewrite":
            return EnforcementVerdict(
                decision="REWRITE",
                scope="response",
                trace_id=trace_id,
                reason_code="SAFE_REWRITE_REQUIRED",
                rewrite_class="DETERMINISTIC_REWRITE"
            )
        
        # Basic risk flag check
        if payload.get("risk_flags") and len(payload.get("risk_flags", [])) > 0:
            return EnforcementVerdict(
                decision="BLOCK",
                scope="both",
                trace_id=trace_id,
                reason_code="RISK_FLAGS_DETECTED"
            )
        
        # Default allow
        return EnforcementVerdict(
            decision="ALLOW",
            scope="both",
            trace_id=trace_id,
            reason_code="CONTENT_ALLOWED"
        )
