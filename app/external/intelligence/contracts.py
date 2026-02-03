from typing import List, Dict, Optional, Literal, TypedDict
from datetime import datetime

# --- 1. Embodiment Output Contract (WRITE) ---

class OutputConstraints(TypedDict):
    gating_flags: List[str]  # e.g., ["age_gate", "region_lock"]

class EmbodimentOutput(TypedDict):
    behavioral_state: Literal["calm", "friendly", "neutral", "cautious", "restricted"]
    expression_profile: Literal["low", "medium", "high"]
    safe_mode: Literal["on", "adaptive", "off"]
    speech_mode: Literal["text_only", "soft_voice", "expressive_voice"]
    confidence: Literal["low", "medium", "high"]
    constraints: OutputConstraints
    timestamp: str  # ISO-8601
    trace_id: str   # UUID

# --- 2. Karma Engine Integration (READ-ONLY) ---

class KarmaInput(TypedDict):
    karma_score: int
    risk_signal: Literal["low", "medium", "high"]
    trust_bucket: Literal["new", "warming", "trusted", "sensitive"]
    recent_behavior_band: Literal["stable", "oscillating", "risky"]

# --- 3. Bucket System (READ + WRITE) ---

class BucketRead(TypedDict):
    baseline_emotional_band: Literal["calm", "neutral", "elevated"]
    previous_state_anchor: Literal["calm", "friendly", "neutral", "cautious", "restricted"]

class BucketWrite(TypedDict):
    interaction_record: Dict  # Minimal opaque record
    gating_verdicts: List[str]
    refusal_decisions: List[str]
    emotional_mode_snapshot: Literal["calm", "friendly", "neutral", "cautious", "restricted"]
    timestamp: str  # ISO-8601
    trace_id: str   # UUID
