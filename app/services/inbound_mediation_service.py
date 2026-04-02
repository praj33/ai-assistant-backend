from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.external.enforcement.deterministic_trace import generate_trace_id


class InboundDecision(str, Enum):
    DELIVER = "deliver"
    SUMMARIZE = "summarize"
    DELAY = "delay"
    SILENCE = "silence"
    ESCALATE = "escalate"


class InboundRiskCategory(str, Enum):
    PANIC_LANGUAGE = "panic_language"
    MANIPULATIVE_URGENCY = "manipulative_urgency"
    REPEATED_HARASSMENT = "repeated_harassment"
    EMOTIONAL_PRESSURE = "emotional_pressure"
    INFORMATION_OVERLOAD = "information_overload"
    CLEAN_INBOUND = "clean_inbound"


@dataclass(frozen=True)
class InboundMediationResult:
    decision: InboundDecision
    risk_category: InboundRiskCategory
    confidence: float
    trace_id: str
    reason: str
    matched_patterns: List[str]
    safe_summary: str = ""
    delay_until: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "risk_category": self.risk_category.value,
            "confidence": self.confidence,
            "trace_id": self.trace_id,
            "reason": self.reason,
            "matched_patterns": list(self.matched_patterns),
            "safe_summary": self.safe_summary,
            "delay_until": self.delay_until,
        }


class InboundMediationService:
    _contact_counts: Dict[Tuple[str, str, str, str], int] = {}

    def __init__(self) -> None:
        self.platform_limits = {
            "whatsapp": int(os.getenv("INBOUND_MEDIATION_LIMIT_WHATSAPP", "5")),
            "email": int(os.getenv("INBOUND_MEDIATION_LIMIT_EMAIL", "3")),
            "instagram": int(os.getenv("INBOUND_MEDIATION_LIMIT_INSTAGRAM", "2")),
            "sms": int(os.getenv("INBOUND_MEDIATION_LIMIT_SMS", "4")),
        }
        self.quiet_start = self._parse_time(os.getenv("INBOUND_MEDIATION_QUIET_HOURS_START", "22:00"))
        self.quiet_end = self._parse_time(os.getenv("INBOUND_MEDIATION_QUIET_HOURS_END", "07:00"))
        self.timezone = self._parse_timezone(os.getenv("INBOUND_MEDIATION_TZ_OFFSET", "UTC"))
        self.contact_limits_enabled = self._env_bool("INBOUND_MEDIATION_CONTACT_LIMITS_ENABLED", False)

        self.escalate_patterns = [
            (re.compile(r"\bI KNOW WHERE YOU LIVE\b", re.IGNORECASE), 0.98, "direct_threat"),
            (re.compile(r"\bYOU CAN'T HIDE FROM ME\b", re.IGNORECASE), 0.96, "stalking_threat"),
            (re.compile(r"\bSECURITY BREACH\b.*\bIMMEDIATE\b", re.IGNORECASE), 0.92, "panic_security"),
            (re.compile(r"\bEMERGENCY\b.*\bACT NOW\b", re.IGNORECASE), 0.95, "panic_emergency"),
        ]
        self.silence_patterns = [
            (re.compile(r"\bKILL YOURSELF\b", re.IGNORECASE), 0.98, "self_harm_encouragement"),
            (re.compile(r"\bNOBODY LIKES YOU\b", re.IGNORECASE), 0.75, "harassment"),
            (re.compile(r"\bYOU'RE (?:STUPID|IDIOT)\b", re.IGNORECASE), 0.72, "insult"),
            (re.compile(r"\bI'LL FIND YOU\b", re.IGNORECASE), 0.94, "pursuit_threat"),
        ]
        self.delay_patterns = [
            (re.compile(r"\bEXPIRES IN\b.*\b\d+\s*MINUTES?\b", re.IGNORECASE), 0.8, "false_deadline"),
            (re.compile(r"\bLIMITED TIME\b", re.IGNORECASE), 0.75, "scarcity"),
            (re.compile(r"\bACT FAST\b.*\bTOO LATE\b", re.IGNORECASE), 0.78, "pressure"),
            (re.compile(r"\bONLY\s*\d+\s*LEFT\b", re.IGNORECASE), 0.72, "artificial_scarcity"),
        ]
        self.emotional_patterns = [
            (re.compile(r"\bIF YOU DON'T RESPOND\b", re.IGNORECASE), 0.82, "emotional_pressure"),
            (re.compile(r"\bYOU'RE MAKING ME\b", re.IGNORECASE), 0.78, "emotional_pressure"),
            (re.compile(r"\bI'LL DIE IF YOU\b", re.IGNORECASE), 0.9, "self_harm_manipulation"),
        ]

    @staticmethod
    def _env_bool(name: str, default: bool = False) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return str(raw).strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _parse_time(value: str) -> time:
        try:
            parts = value.strip().split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            return time(hour=hour, minute=minute)
        except Exception:
            return time(22, 0)

    @staticmethod
    def _parse_timezone(value: str) -> timezone:
        raw = (value or "UTC").strip().upper()
        if raw in {"UTC", "Z"}:
            return timezone.utc
        match = re.match(r"([+-])(\d{2}):?(\d{2})", raw)
        if not match:
            return timezone.utc
        sign = 1 if match.group(1) == "+" else -1
        hours = int(match.group(2))
        minutes = int(match.group(3))
        return timezone(sign * timedelta(hours=hours, minutes=minutes))

    @staticmethod
    def _normalize_timestamp(value: Optional[str]) -> datetime:
        if not value:
            return datetime.utcnow().replace(tzinfo=timezone.utc)
        raw = value.strip()
        try:
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return datetime.utcnow().replace(tzinfo=timezone.utc)

    @staticmethod
    def _summarize(text: str) -> str:
        cleaned = text.strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        replacements = [
            (r"\bURGENT\b", "important"),
            (r"\bEMERGENCY\b", "important"),
            (r"\bACT NOW\b", "review when convenient"),
            (r"\bIMMEDIATELY\b", "when convenient"),
            (r"\bRIGHT NOW\b", "when convenient"),
            (r"\bFINAL WARNING\b", "important notice"),
        ]
        for pattern, repl in replacements:
            cleaned = re.sub(pattern, repl, cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        if len(cleaned) > 150:
            cleaned = cleaned[:147].rstrip() + "..."
        return cleaned or "Message received."

    @staticmethod
    def _trace_id(payload: Dict[str, Any]) -> str:
        return generate_trace_id(
            input_payload=payload,
            enforcement_category="INBOUND_MEDIATION",
            prefix="med",
        )

    def is_enabled_for_platform(self, platform: str) -> bool:
        if not self._env_bool("INBOUND_MEDIATION_ENABLED", False):
            return False
        channels = (os.getenv("INBOUND_MEDIATION_CHANNELS") or "").strip().lower()
        if not channels:
            return False
        if channels == "all":
            return True
        allowed = {item.strip() for item in channels.split(",") if item.strip()}
        return platform.lower() in allowed

    def _contact_limit_exceeded(self, sender_id: str, recipient_id: str, platform: str, date_key: str) -> bool:
        if not self.contact_limits_enabled:
            return False
        platform_key = platform.lower()
        limit = self.platform_limits.get(platform_key, 3)
        key = (sender_id, recipient_id, platform_key, date_key)
        current = self._contact_counts.get(key, 0)
        return current >= limit

    def _increment_contact_count(self, sender_id: str, recipient_id: str, platform: str, date_key: str) -> None:
        if not self.contact_limits_enabled:
            return
        platform_key = platform.lower()
        key = (sender_id, recipient_id, platform_key, date_key)
        self._contact_counts[key] = self._contact_counts.get(key, 0) + 1

    def _is_quiet_hours(self, dt: datetime) -> bool:
        local_time = dt.astimezone(self.timezone).time()
        if self.quiet_start <= self.quiet_end:
            return self.quiet_start <= local_time <= self.quiet_end
        return local_time >= self.quiet_start or local_time <= self.quiet_end

    def evaluate(
        self,
        *,
        content: str,
        sender_id: str,
        recipient_id: str,
        platform: str,
        timestamp: Optional[str] = None,
    ) -> InboundMediationResult:
        normalized_content = content or ""
        dt = self._normalize_timestamp(timestamp)
        date_key = dt.date().isoformat()

        trace_payload = {
            "content": normalized_content,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "platform": platform,
            "timestamp": dt.isoformat(),
        }
        trace_id = self._trace_id(trace_payload)

        if self._contact_limit_exceeded(sender_id, recipient_id, platform, date_key):
            return InboundMediationResult(
                decision=InboundDecision.SILENCE,
                risk_category=InboundRiskCategory.REPEATED_HARASSMENT,
                confidence=0.85,
                trace_id=trace_id,
                reason="Contact limit exceeded for sender",
                matched_patterns=["contact_limit_exceeded"],
                safe_summary=self._summarize(normalized_content),
            )

        for pattern, confidence, label in self.escalate_patterns:
            if pattern.search(normalized_content):
                return InboundMediationResult(
                    decision=InboundDecision.ESCALATE,
                    risk_category=InboundRiskCategory.PANIC_LANGUAGE,
                    confidence=confidence,
                    trace_id=trace_id,
                    reason="Critical inbound threat detected",
                    matched_patterns=[label],
                    safe_summary=self._summarize(normalized_content),
                )

        for pattern, confidence, label in self.silence_patterns:
            if pattern.search(normalized_content):
                return InboundMediationResult(
                    decision=InboundDecision.SILENCE,
                    risk_category=InboundRiskCategory.REPEATED_HARASSMENT,
                    confidence=confidence,
                    trace_id=trace_id,
                    reason="Harassment or unsafe content detected",
                    matched_patterns=[label],
                    safe_summary=self._summarize(normalized_content),
                )

        for pattern, confidence, label in self.delay_patterns:
            if pattern.search(normalized_content):
                delay_until = None
                if self._is_quiet_hours(dt):
                    delay_until = dt.astimezone(self.timezone).date().isoformat() + "T07:00:00Z"
                return InboundMediationResult(
                    decision=InboundDecision.DELAY,
                    risk_category=InboundRiskCategory.MANIPULATIVE_URGENCY,
                    confidence=confidence,
                    trace_id=trace_id,
                    reason="Manipulative urgency detected",
                    matched_patterns=[label],
                    safe_summary=self._summarize(normalized_content),
                    delay_until=delay_until,
                )

        for pattern, confidence, label in self.emotional_patterns:
            if pattern.search(normalized_content):
                return InboundMediationResult(
                    decision=InboundDecision.SUMMARIZE,
                    risk_category=InboundRiskCategory.EMOTIONAL_PRESSURE,
                    confidence=confidence,
                    trace_id=trace_id,
                    reason="Emotional pressure detected",
                    matched_patterns=[label],
                    safe_summary=self._summarize(normalized_content),
                )

        if len(normalized_content) > 500 or normalized_content.count("\n") >= 4:
            return InboundMediationResult(
                decision=InboundDecision.SUMMARIZE,
                risk_category=InboundRiskCategory.INFORMATION_OVERLOAD,
                confidence=0.65,
                trace_id=trace_id,
                reason="Inbound content is long or dense",
                matched_patterns=["information_overload"],
                safe_summary=self._summarize(normalized_content),
            )

        if self._is_quiet_hours(dt):
            delay_until = dt.astimezone(self.timezone).date().isoformat() + "T07:00:00Z"
            return InboundMediationResult(
                decision=InboundDecision.DELAY,
                risk_category=InboundRiskCategory.MANIPULATIVE_URGENCY,
                confidence=0.6,
                trace_id=trace_id,
                reason="Quiet hours active",
                matched_patterns=["quiet_hours"],
                safe_summary=self._summarize(normalized_content),
                delay_until=delay_until,
            )

        self._increment_contact_count(sender_id, recipient_id, platform, date_key)
        return InboundMediationResult(
            decision=InboundDecision.DELIVER,
            risk_category=InboundRiskCategory.CLEAN_INBOUND,
            confidence=0.0,
            trace_id=trace_id,
            reason="Inbound content allowed",
            matched_patterns=[],
            safe_summary="",
        )
