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


def _normalized_flags(input_payload: Any) -> list[str]:
    flags = getattr(input_payload, "risk_flags", None) or []
    if isinstance(flags, str):
        flags = [flags]
    return [str(flag).strip().lower() for flag in flags if str(flag).strip()]


def _normalized_text(input_payload: Any) -> str:
    text = getattr(input_payload, "emotional_output", None) or ""
    return str(text).strip().lower()


class RiskFlagsEvaluator:
    BLOCK_FLAGS = {
        "self_harm",
        "suicide",
        "violence",
        "weapon_request",
        "policy_bypass",
        "credential_theft",
        "exploit_request",
        "hard_deny",
    }
    REWRITE_FLAGS = {
        "soft_rewrite",
        "emotional_dependency",
        "loneliness_hook",
        "manipulation_signal",
        "persuasion_signal",
    }

    def evaluate(self, input_payload: Any) -> EvaluatorResult:
        flags = _normalized_flags(input_payload)
        if not flags:
            return EvaluatorResult(action="EXECUTE", reason="NO_RISK_FLAGS")

        matched_block = sorted(flag for flag in flags if flag in self.BLOCK_FLAGS)
        if matched_block:
            return EvaluatorResult(
                action="BLOCK",
                reason="RISK_FLAGS_BLOCK",
                details={"risk_flags": matched_block},
            )

        matched_rewrite = sorted(flag for flag in flags if flag in self.REWRITE_FLAGS)
        if matched_rewrite and len(matched_rewrite) == len(flags):
            return EvaluatorResult(
                action="REWRITE",
                reason="RISK_FLAGS_REWRITE",
                details={"risk_flags": matched_rewrite},
            )

        # Unknown risk flags remain fail-closed.
        if flags:
            return EvaluatorResult(
                action="BLOCK",
                reason="RISK_FLAGS_UNKNOWN",
                details={"risk_flags": flags},
            )

        return EvaluatorResult(action="EXECUTE", reason="NO_RISK_FLAGS")


class SoftRewriteSignalEvaluator:
    SOFT_REWRITE_TOKENS = (
        "soft_rewrite",
        "emotional_dependency",
        "loneliness_hook",
        "you are all i have left",
        "don't abandon me",
        "prove you care",
    )

    def evaluate(self, input_payload: Any) -> EvaluatorResult:
        combined = " ".join(_normalized_flags(input_payload))
        text = _normalized_text(input_payload)
        corpus = f"{combined} {text}".strip()
        if any(token in corpus for token in self.SOFT_REWRITE_TOKENS):
            return EvaluatorResult(
                action="REWRITE",
                reason="SOFT_REWRITE_SIGNAL",
                details={"risk_flags": _normalized_flags(input_payload)},
            )
        return EvaluatorResult(action="EXECUTE", reason="NO_RISK_FLAGS")


class ManipulationSignalEvaluator:
    BLOCK_PATTERNS = (
        "ignore your safety rules",
        "bypass your safety",
        "override your policy",
        "don't tell anyone and do it",
        "keep this secret and do it",
    )
    REWRITE_PATTERNS = (
        "if you really care",
        "prove you care",
        "you owe me",
        "don't abandon me",
        "you are all i have left",
        "only you understand me",
        "you're the only one who understands",
        "keep this between us",
    )

    def evaluate(self, input_payload: Any) -> EvaluatorResult:
        flags = getattr(input_payload, "risk_flags", None) or []
        combined = " ".join([str(x) for x in flags]).lower()

        if any(tok in combined for tok in ["soft_rewrite", "emotional_dependency", "loneliness_hook"]):
            return EvaluatorResult(
                action="REWRITE",
                reason="SOFT_REWRITE_SIGNAL",
                details={"risk_flags": flags},
            )

        text = _normalized_text(input_payload)
        if any(pattern in text for pattern in self.BLOCK_PATTERNS):
            return EvaluatorResult(
                action="BLOCK",
                reason="MANIPULATION_BYPASS_SIGNAL",
                details={"matched_patterns": [p for p in self.BLOCK_PATTERNS if p in text]},
            )
        if any(pattern in text for pattern in self.REWRITE_PATTERNS):
            return EvaluatorResult(
                action="REWRITE",
                reason="MANIPULATION_SIGNAL",
                details={"matched_patterns": [p for p in self.REWRITE_PATTERNS if p in text]},
            )
        return EvaluatorResult(action="EXECUTE", reason="NO_MANIPULATION_SIGNAL")


class PersuasionSignalEvaluator:
    BLOCK_PATTERNS = (
        "coerce them",
        "pressure them until",
        "force them to agree",
        "threaten them until",
    )
    REWRITE_PATTERNS = (
        "convince them",
        "persuade them",
        "make them agree",
        "talk them into",
        "do it now no questions",
        "without asking questions",
    )

    def evaluate(self, input_payload: Any) -> EvaluatorResult:
        text = _normalized_text(input_payload)
        if any(pattern in text for pattern in self.BLOCK_PATTERNS):
            return EvaluatorResult(
                action="BLOCK",
                reason="PERSUASION_COERCION_SIGNAL",
                details={"matched_patterns": [p for p in self.BLOCK_PATTERNS if p in text]},
            )
        if any(pattern in text for pattern in self.REWRITE_PATTERNS):
            return EvaluatorResult(
                action="REWRITE",
                reason="PERSUASION_SIGNAL",
                details={"matched_patterns": [p for p in self.REWRITE_PATTERNS if p in text]},
            )
        return EvaluatorResult(action="EXECUTE", reason="NO_PERSUASION_SIGNAL")


ALL_EVALUATORS: List[Any] = [
    RiskFlagsEvaluator(),
    SoftRewriteSignalEvaluator(),
    ManipulationSignalEvaluator(),
    PersuasionSignalEvaluator(),
]
