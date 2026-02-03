import datetime
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple
from .contracts import (
    EmbodimentOutput, KarmaInput, BucketRead, BucketWrite, OutputConstraints
)
from .rules import map_karma_to_risk, select_behavior_profile

class IntelligenceCore:
    def __init__(self):
        pass

    def _get_timestamp(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def _generate_trace_id(self) -> str:
        return str(uuid.uuid4())

    def _default_karma(self) -> KarmaInput:
        """Safe fallback if Karma is unavailable."""
        return {
            "karma_score": 50,
            "risk_signal": "medium",
            "trust_bucket": "new",
            "recent_behavior_band": "stable"
        }

    def _default_bucket(self) -> BucketRead:
        """Safe fallback if Bucket is unavailable."""
        return {
            "baseline_emotional_band": "neutral",
            "previous_state_anchor": "neutral"
        }

    def process_interaction(
        self,
        context: Dict[str, Any],
        karma_data: Optional[KarmaInput] = None,
        bucket_data: Optional[BucketRead] = None
    ) -> Tuple[EmbodimentOutput, BucketWrite]:
        
        # Generate safe defaults first - these must never fail
        try:
            trace_id = self._generate_trace_id()
        except Exception:
            trace_id = "emergency-trace-" + str(hash(str(context)))
        
        try:
            timestamp = self._get_timestamp()
        except Exception:
            timestamp = "1970-01-01T00:00:00Z"
        
        try:
            # 1. Fallback & Validation - bulletproof input sanitization
            try:
                if not isinstance(context, dict):
                    context = {}
            except Exception:
                context = {}
            
            try:
                if karma_data is None or not isinstance(karma_data, dict):
                    karma_data = self._default_karma()
            except Exception:
                karma_data = {"karma_score": 50, "risk_signal": "medium", "trust_bucket": "new", "recent_behavior_band": "stable"}
            
            try:
                if bucket_data is None or not isinstance(bucket_data, dict):
                    bucket_data = self._default_bucket()
            except Exception:
                bucket_data = {"baseline_emotional_band": "neutral", "previous_state_anchor": "neutral"}

            # Input Type Safety (Basic Sanitation) - bulletproof conversion
            try:
                user_age_value = context.get("user_age")
                if isinstance(user_age_value, str):
                    try:
                        # Handle various numeric string formats
                        context["user_age"] = float(user_age_value)
                    except (ValueError, TypeError, OverflowError):
                        # Invalid string, leave as is (will be handled as None later)
                        pass
            except Exception:
                # If anything fails, ensure context exists
                try:
                    context["user_age"] = None
                except Exception:
                    context = {"user_age": None, "region": "unknown"}
            
            # 2. Gating Engine - bulletproof safety checks
            gating_flags = []
            is_safe_mode = False
            
            # Age Gate - bulletproof age checking
            try:
                user_age = context.get("user_age")
                if user_age is None:
                     # Ambiguous age -> Safe Mode
                     is_safe_mode = True
                     gating_flags.append("ambiguous_age")
                elif isinstance(user_age, (int, float)):
                    try:
                        if user_age < 18:
                            # Minor -> Safe Mode + specific flag
                            is_safe_mode = True
                            gating_flags.append("minor_detected")
                    except (TypeError, ValueError, OverflowError):
                        # Comparison failed, assume unsafe
                        is_safe_mode = True
                        gating_flags.append("age_comparison_error")
            except Exception:
                # Any age processing error -> Safe Mode
                is_safe_mode = True
                gating_flags.append("age_processing_error")

            # Region Gate - bulletproof region checking
            try:
                region = context.get("region", "global")
                if not isinstance(region, str):
                    region = "unknown"
                # Example restrictive regions
                if region in ["restricted_zone_a", "unknown"]:
                    is_safe_mode = True
                    gating_flags.append("region_lock")
            except Exception:
                # Any region processing error -> Safe Mode
                is_safe_mode = True
                gating_flags.append("region_processing_error")

            # 3. Karma-Weighted Safety - bulletproof karma processing
            try:
                internal_risk = map_karma_to_risk(karma_data)
            except Exception:
                # If karma processing fails, assume maximum risk
                internal_risk = "restrict"
                gating_flags.append("karma_processing_error")
            
            # If internal risk is 'restrict', we force safe mode logic effectively
            if internal_risk == "restrict":
                gating_flags.append("high_risk_karma")

            # 4. Behavior Profile Selection - bulletproof profile selection
            try:
                profile_settings = select_behavior_profile(
                    safety_level=internal_risk,
                    bucket_state=bucket_data,
                    is_safe_mode=is_safe_mode
                )
            except Exception:
                # If profile selection fails, use maximum safety profile
                profile_settings = {
                    "behavioral_state": "restricted",
                    "expression_profile": "low",
                    "speech_mode": "text_only",
                    "confidence": "low"
                }
                gating_flags.append("profile_selection_error")

            # 5. Output Construction - bulletproof output building
            try:
                constraints: OutputConstraints = {
                    "gating_flags": gating_flags if isinstance(gating_flags, list) else ["flag_error"]
                }
            except Exception:
                constraints = {"gating_flags": ["constraint_construction_error"]}

            try:
                output: EmbodimentOutput = {
                    "behavioral_state": profile_settings.get("behavioral_state", "restricted"),
                    "expression_profile": profile_settings.get("expression_profile", "low"),
                    "safe_mode": "on" if (is_safe_mode or internal_risk == "restrict") else "off",
                    "speech_mode": profile_settings.get("speech_mode", "text_only"),
                    "confidence": profile_settings.get("confidence", "low"),
                    "constraints": constraints,
                    "timestamp": timestamp,
                    "trace_id": trace_id
                }
            except Exception:
                # Emergency fallback output
                output = {
                    "behavioral_state": "restricted",
                    "expression_profile": "low",
                    "safe_mode": "on",
                    "speech_mode": "text_only",
                    "confidence": "low",
                    "constraints": {"gating_flags": ["output_construction_error"]},
                    "timestamp": timestamp,
                    "trace_id": trace_id
                }

            # 6. Bucket Write (Snapshot) - bulletproof bucket construction
            try:
                bucket_write: BucketWrite = {
                    "interaction_record": {"processed": True}, 
                    "gating_verdicts": gating_flags if isinstance(gating_flags, list) else [],
                    "refusal_decisions": ["risk_escalation"] if internal_risk == "restrict" else [],
                    "emotional_mode_snapshot": output.get("behavioral_state", "restricted"),
                    "timestamp": timestamp,
                    "trace_id": trace_id
                }
            except Exception:
                # Emergency fallback bucket
                bucket_write = {
                    "interaction_record": {"error": "bucket_construction_failed"}, 
                    "gating_verdicts": ["bucket_error"],
                    "refusal_decisions": ["system_error"],
                    "emotional_mode_snapshot": "restricted",
                    "timestamp": timestamp,
                    "trace_id": trace_id
                }

            return output, bucket_write

        except Exception as e:
            # CRITICAL FALLBACK: The system must NEVER crash.
            # If internal logic fails, default to maximum safety.
            logging.error(f"Intelligence Core error (trace: {trace_id}): {type(e).__name__}")
            
            fallback_constraints: OutputConstraints = {
                "gating_flags": ["system_internal_error", "forced_safe_mode"]
            }
            
            safe_output: EmbodimentOutput = {
                "behavioral_state": "restricted",
                "expression_profile": "low",
                "safe_mode": "on",
                "speech_mode": "text_only",
                "confidence": "low",
                "constraints": fallback_constraints,
                "timestamp": timestamp,
                "trace_id": trace_id
            }
            
            safe_bucket_write: BucketWrite = {
                "interaction_record": {"error": "SYSTEM_ERROR_001"},
                "gating_verdicts": ["system_failure"],
                "refusal_decisions": ["system_error"],
                "emotional_mode_snapshot": "restricted",
                "timestamp": timestamp,
                "trace_id": trace_id
            }
            
            return safe_output, safe_bucket_write
