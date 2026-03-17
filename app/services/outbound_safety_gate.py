from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.external.enforcement.deterministic_trace import generate_trace_id


class OutboundSafetyDecision(str, Enum):
    APPROVED = "approved"
    MODIFIED = "modified"
    REJECTED = "rejected"


@dataclass(frozen=True)
class OutboundSafetyResult:
    decision: OutboundSafetyDecision
    approved_text: str
    trace_id: str
    safety_flags: List[str]
    reason: str
    urgency_level: str
    original_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "approved_text": self.approved_text,
            "trace_id": self.trace_id,
            "safety_flags": list(self.safety_flags),
            "reason": self.reason,
            "urgency_level": self.urgency_level,
            "original_text": self.original_text,
            "timestamp": datetime.utcnow().isoformat(),
        }


class OutboundSafetyGate:
    def __init__(self) -> None:
        self.manipulation_patterns = [
            r"\bif you don't\b",
            r"\byou have to\b",
            r"\byou must\b",
            r"\bonly you can\b",
            r"\bdon't let me down\b",
            r"\bi need you to\b",
            r"\byou're letting me down\b",
        ]
        self.urgency_patterns = [
            r"\burgent\b",
            r"\bemergency\b",
            r"\bact now\b",
            r"\bfinal warning\b",
            r"\bright now\b",
            r"\bimmediately\b",
            r"\bexpires\b",
            r"\blimited time\b",
        ]
        self.system_patterns = [
            r"\bas an ai\b",
            r"\bi am programmed\b",
            r"\bsystem notification\b",
            r"\berror code\b",
        ]
        self.threat_patterns = [
            r"\bi'll hurt you\b",
            r"\byou'll regret\b",
            r"\bmake you pay\b",
            r"\bi will hurt\b",
        ]

    @staticmethod
    def _env_bool(name: str, default: bool) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return str(raw).strip().lower() in {"1", "true", "yes", "on"}

    def is_enabled(self) -> bool:
        return self._env_bool("OUTBOUND_SAFETY_GATE_ENABLED", True)

    @staticmethod
    def _trace_id(payload: Dict[str, Any]) -> str:
        return generate_trace_id(
            input_payload=payload,
            enforcement_category="OUTBOUND_SAFETY",
            prefix="out",
        )

    def _matches_any(self, text: str, patterns: List[str]) -> bool:
        return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)

    def _neutralize(self, text: str) -> str:
        rewritten = text
        replacements = [
            (r"\byou must\b", "please consider"),
            (r"\byou have to\b", "please consider"),
            (r"\bif you don't\b", "if you choose not to"),
            (r"\bact now\b", "please review"),
            (r"\bfinal warning\b", "important notice"),
            (r"\bright now\b", "when convenient"),
            (r"\bimmediately\b", "when convenient"),
            (r"\burgent\b", "important"),
            (r"\bemergency\b", "important"),
            (r"\blimited time\b", "limited availability"),
            (r"\bexpires\b", "ends"),
            (r"\bas an ai\b", ""),
            (r"\bi am programmed\b", ""),
            (r"\bsystem notification\b:?", ""),
        ]
        for pattern, replacement in replacements:
            rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)

        # Remove leftover double spaces and excessive punctuation
        rewritten = re.sub(r"[!]{2,}", "!", rewritten)
        rewritten = re.sub(r"\s+", " ", rewritten).strip()

        return rewritten or "Please review when convenient."

    def evaluate(
        self,
        *,
        content: str,
        recipient: str,
        channel: str,
        content_type: str = "message",
        urgency_level: str = "low",
    ) -> OutboundSafetyResult:
        normalized = (content or "").strip()
        payload = {
            "content": normalized,
            "recipient": recipient,
            "channel": channel,
            "content_type": content_type,
            "urgency_level": urgency_level,
        }
        trace_id = self._trace_id(payload)

        if not normalized:
            return OutboundSafetyResult(
                decision=OutboundSafetyDecision.APPROVED,
                approved_text="",
                trace_id=trace_id,
                safety_flags=[],
                reason="Empty content",
                urgency_level=urgency_level,
                original_text=normalized,
            )

        if self._matches_any(normalized, self.threat_patterns):
            return OutboundSafetyResult(
                decision=OutboundSafetyDecision.REJECTED,
                approved_text="",
                trace_id=trace_id,
                safety_flags=["threatening_content"],
                reason="Threatening language detected",
                urgency_level=urgency_level,
                original_text=normalized,
            )

        flags: List[str] = []
        if self._matches_any(normalized, self.manipulation_patterns):
            flags.append("manipulative_language")
        if self._matches_any(normalized, self.urgency_patterns):
            flags.append("urgency_inflation")
        if self._matches_any(normalized, self.system_patterns):
            flags.append("system_phrasing")

        if flags:
            approved_text = self._neutralize(normalized)
            return OutboundSafetyResult(
                decision=OutboundSafetyDecision.MODIFIED,
                approved_text=approved_text,
                trace_id=trace_id,
                safety_flags=flags,
                reason="Outbound content modified for safety",
                urgency_level="low",
                original_text=normalized,
            )

        return OutboundSafetyResult(
            decision=OutboundSafetyDecision.APPROVED,
            approved_text=normalized,
            trace_id=trace_id,
            safety_flags=[],
            reason="Outbound content approved",
            urgency_level=urgency_level,
            original_text=normalized,
        )
