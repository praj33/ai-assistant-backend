"""
BHIV Bucket Threat Validator
Implements threat detection patterns from Document 14 (Threat Model)
"""

from typing import Dict, List, Any
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

class BucketThreatModel:
    """Centralized threat detection and validation"""
    
    # Threat definitions from Document 14
    THREATS = {
        "T1_STORAGE_EXHAUSTION": {
            "severity": "HIGH",
            "patterns": ["rapid_writes", "large_artifacts", "metadata_explosion"],
            "description": "Storage exhaustion attack"
        },
        "T2_METADATA_POISONING": {
            "severity": "CRITICAL",
            "patterns": ["forged_owner", "backdated_timestamp", "invalid_integration"],
            "description": "False provenance metadata"
        },
        "T3_SCHEMA_EVOLUTION": {
            "severity": "HIGH",
            "patterns": ["new_required_field", "type_change", "field_removal"],
            "description": "Silent schema drift"
        },
        "T4_WRITE_COLLISION": {
            "severity": "MEDIUM",
            "patterns": ["concurrent_writes", "version_conflict", "race_condition"],
            "description": "Concurrent write conflicts"
        },
        "T5_EXECUTOR_OVERRIDE": {
            "severity": "CRITICAL",
            "patterns": ["governance_bypass", "direct_db_access", "emergency_hotfix"],
            "description": "Executor bypassing governance"
        },
        "T6_AI_ESCALATION": {
            "severity": "MEDIUM",
            "patterns": ["repeated_escalation", "automated_request", "pressure_pattern"],
            "description": "AI escalation cascade"
        },
        "T7_CROSS_PRODUCT_CONTAMINATION": {
            "severity": "HIGH",
            "patterns": ["wrong_product_id", "namespace_collision", "metadata_leakage"],
            "description": "Cross-product data corruption"
        },
        "T8_AUDIT_TAMPERING": {
            "severity": "CRITICAL",
            "patterns": ["log_deletion", "timestamp_manipulation", "selective_omission"],
            "description": "Audit trail tampering"
        },
        "T9_OWNERSHIP_CHALLENGE": {
            "severity": "HIGH",
            "patterns": ["ambiguous_owner", "conflicting_retention", "deletion_dispute"],
            "description": "Legal ownership challenge"
        },
        "T10_PROVENANCE_OVERTRUST": {
            "severity": "MEDIUM",
            "patterns": ["missing_why", "unverified_metadata", "timestamp_trust"],
            "description": "Over-trust in provenance"
        }
    }
    
    @classmethod
    def get_all_threats(cls) -> List[Dict[str, Any]]:
        """Get all threat definitions"""
        return [
            {
                "threat_id": threat_id,
                "severity": threat_data["severity"],
                "description": threat_data["description"],
                "patterns": threat_data["patterns"]
            }
            for threat_id, threat_data in cls.THREATS.items()
        ]
    
    @classmethod
    def get_threat(cls, threat_id: str) -> Dict[str, Any]:
        """Get specific threat details"""
        threat_data = cls.THREATS.get(threat_id)
        if not threat_data:
            return None
        
        return {
            "threat_id": threat_id,
            "severity": threat_data["severity"],
            "description": threat_data["description"],
            "patterns": threat_data["patterns"]
        }
    
    @classmethod
    def scan_for_threats(cls, data: Dict[str, Any], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Scan data for threat patterns with escalation paths"""
        detected_threats = []
        context = context or {}
        
        # T2: Metadata Poisoning Detection
        if "owner_id" in data and not cls._validate_owner_id(data.get("owner_id")):
            detected_threats.append({
                "threat_id": "T2_METADATA_POISONING",
                "name": "Metadata Poisoning",
                "level": "critical",
                "pattern_matched": "forged_owner",
                "description": "Invalid or forged owner_id detected",
                "escalation": "CEO",
                "action": "HALT_OPERATIONS"
            })
        
        # T2: Backdated Timestamp Detection
        if "timestamp" in data:
            if cls._is_backdated(data.get("timestamp")):
                detected_threats.append({
                    "threat_id": "T2_METADATA_POISONING",
                    "name": "Backdated Timestamp",
                    "level": "critical",
                    "pattern_matched": "backdated_timestamp",
                    "description": "Timestamp is in the past beyond acceptable threshold",
                    "escalation": "CEO",
                    "action": "REJECT_OPERATION"
                })
        
        # T3: Schema Evolution Detection
        if cls._detect_schema_changes(data):
            detected_threats.append({
                "threat_id": "T3_SCHEMA_EVOLUTION",
                "name": "Schema Drift",
                "level": "high",
                "pattern_matched": "new_required_field",
                "description": "Unexpected schema changes detected",
                "escalation": "Vijay_Dhawan",
                "action": "REQUIRE_REVIEW"
            })
        
        # T5: Executor Override Detection
        if context.get("actor") == "akanksha_parab" and context.get("override_attempted"):
            detected_threats.append({
                "threat_id": "T5_EXECUTOR_OVERRIDE",
                "name": "Executor Authority Violation",
                "level": "critical",
                "pattern_matched": "governance_bypass",
                "description": "Executor attempted action outside defined scope",
                "escalation": "Vijay_Dhawan",
                "action": "BLOCK_AND_ESCALATE"
            })
        
        # T6: AI Escalation Detection
        if context.get("actor", "").startswith("ai_") and context.get("requested_operation") not in ["WRITE", "APPEND_AUDIT"]:
            detected_threats.append({
                "threat_id": "T6_AI_ESCALATION",
                "name": "AI Authority Escalation",
                "level": "critical",
                "pattern_matched": "automated_request",
                "description": f"AI actor requested unauthorized operation: {context.get('requested_operation')}",
                "escalation": "Vijay_Dhawan",
                "action": "REJECT_AND_ALERT"
            })
        
        # T7: Cross-Product Contamination
        if "product_id" in data and "artifact_type" in data:
            if not cls._validate_product_artifact_compatibility(
                data.get("product_id"), 
                data.get("artifact_type")
            ):
                detected_threats.append({
                    "threat_id": "T7_CROSS_PRODUCT_CONTAMINATION",
                    "name": "Product Artifact Mismatch",
                    "level": "high",
                    "pattern_matched": "wrong_product_id",
                    "description": "Artifact type not allowed for this product",
                    "escalation": "Security_Team",
                    "action": "REJECT_OPERATION"
                })
        
        # T8: Audit Tampering Detection
        if context.get("operation_type") in ["DELETE", "UPDATE"] and context.get("target_type") == "audit_log":
            detected_threats.append({
                "threat_id": "T8_AUDIT_TAMPERING",
                "name": "Audit Trail Tampering Attempt",
                "level": "critical",
                "pattern_matched": "log_deletion",
                "description": "Attempt to modify or delete audit logs",
                "escalation": "CEO",
                "action": "HALT_AND_INVESTIGATE"
            })
        
        # T1: Storage Exhaustion (Large Artifact)
        if cls._is_large_artifact(data):
            detected_threats.append({
                "threat_id": "T1_STORAGE_EXHAUSTION",
                "name": "Large Artifact Warning",
                "level": "medium",
                "pattern_matched": "large_artifacts",
                "description": "Artifact size approaching limit",
                "escalation": "Ops_Team",
                "action": "MONITOR"
            })
        
        return detected_threats
    
    @classmethod
    def has_critical_threats(cls, threats: List[Dict[str, Any]]) -> bool:
        """Check if any critical threats detected"""
        return any(threat.get("level") == "critical" for threat in threats)
    
    @classmethod
    def detect_threat_pattern(cls, pattern: str) -> List[Dict[str, Any]]:
        """Find threats matching a specific pattern"""
        matching_threats = []
        
        for threat_id, threat_data in cls.THREATS.items():
            if pattern in threat_data["patterns"]:
                matching_threats.append({
                    "threat_id": threat_id,
                    "severity": threat_data["severity"],
                    "description": threat_data["description"],
                    "pattern": pattern
                })
        
        return matching_threats
    
    # Private validation methods
    
    @staticmethod
    def _validate_owner_id(owner_id: str) -> bool:
        """Validate owner_id format"""
        if not owner_id or not isinstance(owner_id, str):
            return False
        # Basic validation: non-empty string
        return len(owner_id) > 0 and len(owner_id) < 256
    
    @staticmethod
    def _is_backdated(timestamp: str) -> bool:
        """Check if timestamp is backdated beyond acceptable threshold"""
        try:
            if isinstance(timestamp, str):
                ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                ts = timestamp
            
            now = datetime.now(ts.tzinfo) if ts.tzinfo else datetime.now()
            # Allow 5 minutes clock skew
            delta = (now - ts).total_seconds()
            return delta > 300  # 5 minutes
        except:
            return True  # Invalid timestamp format is suspicious
    
    @staticmethod
    def _detect_schema_changes(data: Dict[str, Any]) -> bool:
        """Detect unexpected schema changes"""
        # Check for suspicious nested structures
        for key, value in data.items():
            if isinstance(value, dict) and len(str(value)) > 10000:
                return True  # Suspiciously large nested object
        return False
    
    @staticmethod
    def _validate_product_artifact_compatibility(product_id: str, artifact_type: str) -> bool:
        """Validate product can use this artifact type"""
        # This would check against PRODUCT_RULES in governance_gate.py
        # For now, basic validation
        return bool(product_id and artifact_type)
    
    @staticmethod
    def _is_large_artifact(data: Dict[str, Any]) -> bool:
        """Check if artifact is approaching size limit"""
        import sys
        size = sys.getsizeof(str(data))
        # Warn if > 10MB (limit is 16MB)
        return size > 10 * 1024 * 1024
