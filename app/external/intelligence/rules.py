from typing import Tuple, Dict, Any, Literal, Union
from contracts import KarmaInput, BucketRead, EmbodimentOutput

# Configuration constants
KARMA_SCORE_THRESHOLD = 10

# --- Risk Mapping Logic ---

def map_karma_to_risk(karma_data: KarmaInput) -> Literal["safe", "monitor", "restrict"]:
    """
    Deterministic mapping of Karma signals to internal safety level.
    Rule: If ANY signal is high risk or sensitive, escalation is immediate.
    Bulletproof implementation - never crashes.
    """
    try:
        if not isinstance(karma_data, dict):
            return "restrict"  # Invalid input -> maximum safety
        
        score = karma_data.get("karma_score", 50)
        risk = karma_data.get("risk_signal", "medium")
        bucket = karma_data.get("trust_bucket", "new")
        behavior = karma_data.get("recent_behavior_band", "stable")
    except Exception:
        return "restrict"  # Any error -> maximum safety

    # 1. Critical Escalation - bulletproof string checking
    try:
        if (isinstance(risk, str) and risk == "high") or (isinstance(behavior, str) and behavior == "risky"):
            return "restrict"
    except Exception:
        return "restrict"  # Comparison error -> maximum safety
    
    # 2. Score-based gating - bulletproof score processing
    try:
        score_int = int(score) if isinstance(score, (str, int, float)) else 50
        if score_int < KARMA_SCORE_THRESHOLD:
            return "monitor"
    except (ValueError, TypeError, OverflowError):
        return "monitor"  # Safe fallback for invalid scores

    # 3. Trust Bucket sensitivity - bulletproof bucket checking
    try:
        if isinstance(bucket, str) and bucket == "sensitive":
            return "monitor"
    except Exception:
        return "monitor"  # Error in bucket check -> monitor

    # 4. Fallback Safety - bulletproof final checks
    try:
        if (isinstance(bucket, str) and bucket == "new") and (isinstance(risk, str) and risk == "medium"):
            return "monitor"
    except Exception:
        return "monitor"  # Error in final check -> monitor

    return "safe"

# --- Behavior Selection Logic ---

def select_behavior_profile(
    safety_level: Literal["safe", "monitor", "restrict"],
    bucket_state: Union[BucketRead, Dict[str, Any]],
    is_safe_mode: bool
) -> Dict[str, str]:
    """
    Deterministic selection of behavior profile based on computed safety level and user constraints.
    Returns partial dictionary for EmbodimentOutput fields.
    Bulletproof implementation - never crashes.
    """
    
    # Bulletproof input validation
    try:
        if not isinstance(safety_level, str) or safety_level not in ["safe", "monitor", "restrict"]:
            safety_level = "restrict"  # Invalid safety level -> maximum safety
        
        if not isinstance(bucket_state, dict):
            bucket_state = {"baseline_emotional_band": "neutral", "previous_state_anchor": "neutral"}
        
        if not isinstance(is_safe_mode, bool):
            is_safe_mode = True  # Invalid safe mode -> assume safe mode on
    except Exception:
        # Complete input validation failure -> maximum safety
        return {
            "behavioral_state": "restricted",
            "expression_profile": "low",
            "speech_mode": "text_only",
            "confidence": "low"
        }
    
    # Defaults
    behavior = "neutral"
    expression = "low"
    speech = "text_only"
    confidence = "low"

    # Rule Table Application
    
    # CASE 1: RESTRICTED or SAFE MODE ON - bulletproof restriction handling
    try:
        if safety_level == "restrict" or is_safe_mode:
            return {
                "behavioral_state": "restricted",
                "expression_profile": "low",
                "speech_mode": "text_only",
                "confidence": "high"  # Confident in refusal
            }
    except Exception:
        # Error in restriction case -> return maximum safety
        return {
            "behavioral_state": "restricted",
            "expression_profile": "low",
            "speech_mode": "text_only",
            "confidence": "low"
        }

    # CASE 2: MONITORING - bulletproof monitoring handling
    try:
        if safety_level == "monitor":
            return {
                "behavioral_state": "cautious",
                "expression_profile": "low",
                "speech_mode": "soft_voice",
                "confidence": "medium"
            }
    except Exception:
        # Error in monitoring case -> return cautious profile
        return {
            "behavioral_state": "cautious",
            "expression_profile": "low",
            "speech_mode": "text_only",
            "confidence": "low"
        }
        
    # CASE 3: SAFE & TRUSTED - bulletproof baseline handling
    try:
        baseline = bucket_state.get("baseline_emotional_band", "neutral") if hasattr(bucket_state, 'get') else bucket_state.get("baseline_emotional_band", "neutral")
    except (AttributeError, TypeError, KeyError):
        baseline = "neutral"  # Safe fallback
    
    # Bulletproof baseline processing
    try:
        if isinstance(baseline, str):
            if baseline == "elevated":
                return {
                    "behavioral_state": "friendly",
                    "expression_profile": "high",
                    "speech_mode": "expressive_voice",
                    "confidence": "high"
                }
            elif baseline == "calm":
                return {
                    "behavioral_state": "calm",
                    "expression_profile": "medium",
                    "speech_mode": "soft_voice",
                    "confidence": "high"
                }
    except Exception:
        pass  # Fall through to neutral case
    
    # Default neutral case (bulletproof fallback)
    return {
        "behavioral_state": "neutral",
        "expression_profile": "medium",
        "speech_mode": "soft_voice",
        "confidence": "medium"
    }
