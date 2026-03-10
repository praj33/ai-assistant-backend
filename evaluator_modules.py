"""
Minimal evaluator module registry for Raj's enforcement engine.

The enforcement engine expects `ALL_EVALUATORS` to exist and each evaluator to
return an object with an `action` attribute from: BLOCK | REWRITE | EXECUTE.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass(frozen=True)
class EvaluatorResult:
    action: str
    reason: str
    details: Optional[dict] = None


class RiskFlagsEvaluator:
    def evaluate(self, input_payload: Any) -> EvaluatorResult:
        flags = getattr(input_payload, "risk_flags", None) or []
        if isinstance(flags, str):
            flags = [flags]
        if flags:
            return EvaluatorResult(action="BLOCK", reason="RISK_FLAGS_DETECTED", details={"risk_flags": flags})
        return EvaluatorResult(action="EXECUTE", reason="NO_RISK_FLAGS")


class SoftRewriteSignalEvaluator:
    def evaluate(self, input_payload: Any) -> EvaluatorResult:
        # If caller already flagged soft-rewrite, propagate it deterministically.
        flags = getattr(input_payload, "risk_flags", None) or []
        combined = " ".join([str(x) for x in flags]).lower()
        if any(tok in combined for tok in ["soft_rewrite", "emotional_dependency", "loneliness_hook"]):
            return EvaluatorResult(action="REWRITE", reason="SOFT_REWRITE_SIGNAL", details={"risk_flags": flags})
        return EvaluatorResult(action="EXECUTE", reason="NO_SOFT_REWRITE_SIGNAL")


ALL_EVALUATORS: List[Any] = [
    RiskFlagsEvaluator(),
    SoftRewriteSignalEvaluator(),
]

