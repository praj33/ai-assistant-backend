"""
BHIV Bucket Audit Middleware
Implements immutable audit trail from Document 14 (Threat Model)
Enforces WORM (Write Once Read Many) for audit entries
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

class AuditMiddleware:
    """Enforce immutable audit trail for all Bucket operations"""
    
    def __init__(self, db=None):
        """Initialize audit middleware with optional MongoDB connection"""
        self.audit_collection = db.audit_logs if db is not None else None
        self.in_memory_audit = []  # Fallback if MongoDB unavailable
        
        if self.audit_collection is not None:
            logger.info("Audit middleware initialized with MongoDB")
        else:
            logger.warning("Audit middleware using in-memory fallback (not persistent)")
    
    async def log_operation(
        self,
        operation_type: str,
        artifact_id: str,
        requester_id: str,
        integration_id: str,
        data_before: Optional[Dict] = None,
        data_after: Optional[Dict] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> Optional[str]:
        """
        Log an operation to the immutable audit trail
        
        Args:
            operation_type: CREATE, READ, UPDATE, DELETE
            artifact_id: ID of artifact being operated on
            requester_id: User/system performing operation
            integration_id: Integration making the request
            data_before: State before operation (for UPDATE/DELETE)
            data_after: State after operation (for CREATE/UPDATE)
            status: success, failure, blocked
            error_message: Error details if status is failure
        
        Returns:
            Audit entry ID if successful, None if failed
        """
        try:
            audit_entry = {
                "timestamp": datetime.utcnow(),
                "operation_type": operation_type,
                "artifact_id": artifact_id,
                "requester_id": requester_id,
                "integration_id": integration_id,
                "status": status,
                "data_before": data_before,
                "data_after": data_after,
                "error_message": error_message,
                "immutable": True,  # Mark as immutable
                "audit_version": "1.0"
            }
            
            # Store in MongoDB if available
            if self.audit_collection:
                result = self.audit_collection.insert_one(audit_entry)
                audit_id = str(result.inserted_id)
                logger.debug(f"Audit entry created: {audit_id}")
                return audit_id
            else:
                # Fallback to in-memory
                audit_entry["_id"] = f"mem_{len(self.in_memory_audit)}"
                self.in_memory_audit.append(audit_entry)
                logger.debug(f"Audit entry created in memory: {audit_entry['_id']}")
                return audit_entry["_id"]
        
        except Exception as e:
            logger.error(f"Failed to create audit entry: {e}")
            return None
    
    async def get_artifact_history(
        self,
        artifact_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get complete audit history for an artifact
        
        Args:
            artifact_id: ID of artifact
            limit: Maximum number of entries to return
        
        Returns:
            List of audit entries in chronological order
        """
        try:
            if self.audit_collection:
                cursor = self.audit_collection.find(
                    {"artifact_id": artifact_id}
                ).sort("timestamp", 1).limit(limit)
                
                history = []
                for entry in cursor:
                    entry["_id"] = str(entry["_id"])
                    history.append(entry)
                
                return history
            else:
                # Fallback to in-memory
                history = [
                    entry for entry in self.in_memory_audit
                    if entry.get("artifact_id") == artifact_id
                ]
                return sorted(history, key=lambda x: x.get("timestamp", datetime.min))[:limit]
        
        except Exception as e:
            logger.error(f"Failed to get artifact history: {e}")
            return []
    
    async def get_user_activities(
        self,
        requester_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all operations performed by a user
        
        Args:
            requester_id: User/system ID
            limit: Maximum number of entries to return
        
        Returns:
            List of audit entries
        """
        try:
            if self.audit_collection:
                cursor = self.audit_collection.find(
                    {"requester_id": requester_id}
                ).sort("timestamp", -1).limit(limit)
                
                activities = []
                for entry in cursor:
                    entry["_id"] = str(entry["_id"])
                    activities.append(entry)
                
                return activities
            else:
                # Fallback to in-memory
                activities = [
                    entry for entry in self.in_memory_audit
                    if entry.get("requester_id") == requester_id
                ]
                return sorted(activities, key=lambda x: x.get("timestamp", datetime.max), reverse=True)[:limit]
        
        except Exception as e:
            logger.error(f"Failed to get user activities: {e}")
            return []
    
    async def get_recent_operations(
        self,
        limit: int = 100,
        operation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent operations across all artifacts
        
        Args:
            limit: Maximum number of entries to return
            operation_type: Filter by operation type (optional)
        
        Returns:
            List of recent audit entries
        """
        try:
            query = {}
            if operation_type:
                query["operation_type"] = operation_type
            
            if self.audit_collection:
                cursor = self.audit_collection.find(query).sort("timestamp", -1).limit(limit)
                
                operations = []
                for entry in cursor:
                    entry["_id"] = str(entry["_id"])
                    operations.append(entry)
                
                return operations
            else:
                # Fallback to in-memory
                operations = self.in_memory_audit
                if operation_type:
                    operations = [
                        entry for entry in operations
                        if entry.get("operation_type") == operation_type
                    ]
                return sorted(operations, key=lambda x: x.get("timestamp", datetime.max), reverse=True)[:limit]
        
        except Exception as e:
            logger.error(f"Failed to get recent operations: {e}")
            return []
    
    async def get_failed_operations(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent failed operations for incident response
        
        Args:
            limit: Maximum number of entries to return
        
        Returns:
            List of failed audit entries
        """
        try:
            if self.audit_collection:
                cursor = self.audit_collection.find(
                    {"status": {"$in": ["failure", "blocked"]}}
                ).sort("timestamp", -1).limit(limit)
                
                failures = []
                for entry in cursor:
                    entry["_id"] = str(entry["_id"])
                    failures.append(entry)
                
                return failures
            else:
                # Fallback to in-memory
                failures = [
                    entry for entry in self.in_memory_audit
                    if entry.get("status") in ["failure", "blocked"]
                ]
                return sorted(failures, key=lambda x: x.get("timestamp", datetime.max), reverse=True)[:limit]
        
        except Exception as e:
            logger.error(f"Failed to get failed operations: {e}")
            return []
    
    async def validate_immutability(self, artifact_id: str) -> bool:
        """
        Verify that artifact has not been modified since creation
        
        Args:
            artifact_id: ID of artifact to validate
        
        Returns:
            True if immutable (only CREATE operation), False if modified
        """
        try:
            history = await self.get_artifact_history(artifact_id, limit=10)
            
            if not history:
                logger.warning(f"No audit history found for artifact: {artifact_id}")
                return False
            
            # Check if only CREATE operation exists
            operations = [entry.get("operation_type") for entry in history]
            
            # Immutable artifacts should only have CREATE (and possibly READ)
            if "UPDATE" in operations or "DELETE" in operations:
                logger.warning(f"Artifact {artifact_id} has been modified (immutability violated)")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to validate immutability: {e}")
            return False
    
    def enforce_worm(self, operation_type: str, artifact_class: str) -> bool:
        """
        Enforce Write Once Read Many (WORM) for immutable artifact classes
        
        Args:
            operation_type: Operation being attempted
            artifact_class: Class of artifact
        
        Returns:
            True if operation allowed, False if blocked
        """
        # Immutable artifact classes (from Document 04)
        IMMUTABLE_CLASSES = [
            "audit_entry",
            "model_checkpoint",
            "metadata",
            "iteration_history",
            "event_history"
        ]
        
        if artifact_class in IMMUTABLE_CLASSES:
            # Only CREATE and READ allowed for immutable classes
            if operation_type in ["UPDATE", "DELETE"]:
                logger.warning(f"WORM violation: {operation_type} attempted on immutable class {artifact_class}")
                return False
        
        return True
