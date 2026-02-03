"""
BHIV Core Boundary Enforcer
Constitutional middleware that validates all Core requests against defined boundaries
Ensures Core respects Bucket sovereignty and cannot exceed authorized capabilities
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from utils.logger import get_logger

logger = get_logger(__name__)

class BoundaryViolationType(Enum):
    """Types of boundary violations"""
    UNAUTHORIZED_OPERATION = "unauthorized_operation"
    SCHEMA_MUTATION = "schema_mutation"
    DELETION_ATTEMPT = "deletion_attempt"
    AUDIT_HIDING = "audit_hiding"
    GOVERNANCE_BYPASS = "governance_bypass"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

class CoreCapability(Enum):
    """Allowed Core capabilities"""
    READ_ARTIFACTS = "read_artifacts"
    WRITE_ARTIFACTS = "write_artifacts"
    QUERY_METADATA = "query_metadata"
    APPEND_AUDIT = "append_audit"
    REQUEST_RETENTION = "request_retention"
    VERIFY_PROVENANCE = "verify_provenance"

class ProhibitedAction(Enum):
    """Prohibited Core actions"""
    MUTATE_SCHEMA = "mutate_schema"
    DELETE_ARTIFACTS = "delete_artifacts"
    HIDE_OPERATIONS = "hide_operations"
    BYPASS_GOVERNANCE = "bypass_governance"
    MODIFY_AUDIT = "modify_audit"
    CROSS_PRODUCT_ACCESS = "cross_product_access"
    DIRECT_DB_ACCESS = "direct_db_access"
    OVERRIDE_RETENTION = "override_retention"

class CoreBoundaryEnforcer:
    """Enforces constitutional boundaries between Core and Bucket"""
    
    def __init__(self):
        self.violation_log = []
        self.allowed_capabilities = set(cap.value for cap in CoreCapability)
        self.prohibited_actions = set(action.value for action in ProhibitedAction)
        logger.info("Core Boundary Enforcer initialized")
    
    def validate_request(
        self,
        requester_id: str,
        operation_type: str,
        target_resource: str,
        request_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate Core request against constitutional boundaries
        
        Args:
            requester_id: ID of requesting system (must be 'bhiv_core')
            operation_type: Type of operation (READ, WRITE, QUERY, etc.)
            target_resource: Resource being accessed
            request_data: Request payload
            context: Additional context
            
        Returns:
            Validation result with allowed/denied status
        """
        context = context or {}
        
        validation_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "requester_id": requester_id,
            "operation_type": operation_type,
            "target_resource": target_resource,
            "allowed": False,
            "violations": [],
            "warnings": []
        }
        
        # Check 1: Verify requester is Core
        if not self._is_core_requester(requester_id):
            validation_result["violations"].append({
                "type": BoundaryViolationType.UNAUTHORIZED_ACCESS.value,
                "message": f"Requester {requester_id} is not authorized Core system",
                "severity": "CRITICAL"
            })
            logger.warning(f"Non-Core requester attempted access: {requester_id}")
            return validation_result
        
        # Check 2: Validate operation is within allowed capabilities
        capability_check = self._validate_capability(operation_type, target_resource)
        if not capability_check["allowed"]:
            validation_result["violations"].append({
                "type": BoundaryViolationType.UNAUTHORIZED_OPERATION.value,
                "message": capability_check["reason"],
                "severity": "HIGH"
            })
            logger.warning(f"Core attempted unauthorized operation: {operation_type} on {target_resource}")
            return validation_result
        
        # Check 3: Detect prohibited actions
        prohibited_check = self._detect_prohibited_actions(operation_type, request_data, context)
        if prohibited_check["violations"]:
            validation_result["violations"].extend(prohibited_check["violations"])
            logger.error(f"Core attempted prohibited action: {prohibited_check['violations']}")
            return validation_result
        
        # Check 4: Validate schema integrity
        if operation_type in ["WRITE", "UPDATE"]:
            schema_check = self._validate_schema_integrity(request_data)
            if not schema_check["valid"]:
                validation_result["violations"].append({
                    "type": BoundaryViolationType.SCHEMA_MUTATION.value,
                    "message": schema_check["reason"],
                    "severity": "CRITICAL"
                })
                logger.error(f"Core attempted schema mutation: {schema_check['reason']}")
                return validation_result
        
        # Check 5: Validate audit trail integrity
        audit_check = self._validate_audit_integrity(operation_type, target_resource)
        if not audit_check["valid"]:
            validation_result["violations"].append({
                "type": BoundaryViolationType.AUDIT_HIDING.value,
                "message": audit_check["reason"],
                "severity": "CRITICAL"
            })
            logger.error(f"Core attempted audit violation: {audit_check['reason']}")
            return validation_result
        
        # Check 6: Validate product isolation
        if "product_id" in request_data:
            isolation_check = self._validate_product_isolation(
                requester_id, 
                request_data.get("product_id"),
                context.get("requesting_product_id")
            )
            if not isolation_check["valid"]:
                validation_result["violations"].append({
                    "type": BoundaryViolationType.CROSS_PRODUCT_ACCESS.value,
                    "message": isolation_check["reason"],
                    "severity": "HIGH"
                })
                logger.warning(f"Core attempted cross-product access: {isolation_check['reason']}")
                return validation_result
        
        # All checks passed
        validation_result["allowed"] = True
        logger.info(f"Core request validated: {operation_type} on {target_resource}")
        
        return validation_result
    
    def _is_core_requester(self, requester_id: str) -> bool:
        """Verify requester is authorized Core system"""
        # Core must identify itself with specific prefix
        return requester_id.startswith("bhiv_core") or requester_id == "core_system"
    
    def _validate_capability(self, operation_type: str, target_resource: str) -> Dict[str, Any]:
        """Validate operation is within allowed Core capabilities"""
        
        # Map operations to capabilities
        operation_capability_map = {
            "READ": CoreCapability.READ_ARTIFACTS.value,
            "WRITE": CoreCapability.WRITE_ARTIFACTS.value,
            "QUERY": CoreCapability.QUERY_METADATA.value,
            "AUDIT_APPEND": CoreCapability.APPEND_AUDIT.value,
            "RETENTION_REQUEST": CoreCapability.REQUEST_RETENTION.value,
            "VERIFY": CoreCapability.VERIFY_PROVENANCE.value
        }
        
        required_capability = operation_capability_map.get(operation_type)
        
        if not required_capability:
            return {
                "allowed": False,
                "reason": f"Unknown operation type: {operation_type}"
            }
        
        if required_capability not in self.allowed_capabilities:
            return {
                "allowed": False,
                "reason": f"Operation {operation_type} requires capability {required_capability} which is not allowed"
            }
        
        return {"allowed": True}
    
    def _detect_prohibited_actions(
        self, 
        operation_type: str, 
        request_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect if request contains prohibited actions"""
        violations = []
        
        # Check for deletion attempts
        if operation_type == "DELETE":
            violations.append({
                "type": BoundaryViolationType.DELETION_ATTEMPT.value,
                "message": "Core is not allowed to delete artifacts",
                "severity": "CRITICAL"
            })
        
        # Check for schema mutation
        if "schema_change" in request_data or "_schema" in request_data:
            violations.append({
                "type": BoundaryViolationType.SCHEMA_MUTATION.value,
                "message": "Core cannot mutate schema",
                "severity": "CRITICAL"
            })
        
        # Check for audit hiding
        if request_data.get("skip_audit") or request_data.get("hide_operation"):
            violations.append({
                "type": BoundaryViolationType.AUDIT_HIDING.value,
                "message": "Core cannot hide operations from audit trail",
                "severity": "CRITICAL"
            })
        
        # Check for governance bypass
        if context.get("bypass_governance") or request_data.get("emergency_override"):
            violations.append({
                "type": BoundaryViolationType.GOVERNANCE_BYPASS.value,
                "message": "Core cannot bypass governance gate",
                "severity": "CRITICAL"
            })
        
        # Check for direct database access
        if context.get("direct_db_access") or "raw_query" in request_data:
            violations.append({
                "type": BoundaryViolationType.UNAUTHORIZED_ACCESS.value,
                "message": "Core cannot access database directly",
                "severity": "CRITICAL"
            })
        
        return {"violations": violations}
    
    def _validate_schema_integrity(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that request doesn't mutate schema"""
        
        # Check for schema-related fields
        prohibited_fields = [
            "_schema", "schema_version", "schema_change",
            "add_field", "remove_field", "modify_field"
        ]
        
        for field in prohibited_fields:
            if field in request_data:
                return {
                    "valid": False,
                    "reason": f"Request contains prohibited schema field: {field}"
                }
        
        return {"valid": True}
    
    def _validate_audit_integrity(self, operation_type: str, target_resource: str) -> Dict[str, Any]:
        """Validate that operation doesn't compromise audit trail"""
        
        # Core cannot modify or delete audit logs
        if target_resource.startswith("audit_") or "audit" in target_resource.lower():
            if operation_type in ["UPDATE", "DELETE"]:
                return {
                    "valid": False,
                    "reason": f"Core cannot {operation_type} audit logs"
                }
        
        return {"valid": True}
    
    def _validate_product_isolation(
        self, 
        requester_id: str, 
        target_product_id: str,
        requesting_product_id: Optional[str]
    ) -> Dict[str, Any]:
        """Validate product isolation boundaries"""
        
        # If Core is requesting on behalf of a product, verify match
        if requesting_product_id and target_product_id != requesting_product_id:
            return {
                "valid": False,
                "reason": f"Core cannot access product {target_product_id} on behalf of {requesting_product_id}"
            }
        
        return {"valid": True}
    
    def log_violation(self, violation: Dict[str, Any]):
        """Log boundary violation for audit and escalation"""
        violation["logged_at"] = datetime.utcnow().isoformat()
        self.violation_log.append(violation)
        logger.error(f"Boundary violation logged: {violation}")
    
    def get_violation_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of violations in last N hours"""
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_violations = [
            v for v in self.violation_log
            if datetime.fromisoformat(v["logged_at"]) > cutoff
        ]
        
        return {
            "total_violations": len(recent_violations),
            "by_type": self._group_by_type(recent_violations),
            "critical_count": len([v for v in recent_violations if v.get("severity") == "CRITICAL"]),
            "violations": recent_violations
        }
    
    def _group_by_type(self, violations: List[Dict]) -> Dict[str, int]:
        """Group violations by type"""
        grouped = {}
        for v in violations:
            vtype = v.get("type", "unknown")
            grouped[vtype] = grouped.get(vtype, 0) + 1
        return grouped

# Global enforcer instance
core_boundary_enforcer = CoreBoundaryEnforcer()
