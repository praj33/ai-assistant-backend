import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime
import json

# Add Primary_Bucket_Owner path for imports
bucket_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'Primary_Bucket_Owner')
if bucket_path not in sys.path:
    sys.path.append(bucket_path)

from utils.logger import get_logger
from database.mongo_db import MongoDBClient
from middleware.audit_middleware import AuditMiddleware

class BucketService:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.mongo_client = MongoDBClient()
        self.audit_middleware = AuditMiddleware(self.mongo_client.db if self.mongo_client and self.mongo_client.db is not None else None)
        
    def log_event(self, trace_id: str, stage: str, data: Dict[str, Any]) -> bool:
        """Log event to bucket for audit trail"""
        try:
            # Simple synchronous logging for now
            log_entry = {
                "trace_id": trace_id,
                "stage": stage,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "bucket_service"
            }
            self.logger.info(f"BUCKET_LOG [{trace_id}] {stage}: {json.dumps(log_entry, default=str)}")
            return True
        except Exception as e:
            self.logger.error(f"Bucket logging failed for {trace_id}: {e}")
            return False
    
    def get_trace_logs(self, trace_id: str) -> Optional[list]:
        """Retrieve all logs for a specific trace ID"""
        try:
            if self.audit_middleware.audit_collection:
                logs = list(self.audit_middleware.audit_collection.find(
                    {"artifact_id": trace_id}
                ).sort("timestamp", -1))
                return logs
            return None
        except Exception as e:
            self.logger.error(f"Failed to retrieve trace logs for {trace_id}: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "service": "bucket_service", 
            "status": "active",
            "mongo_connected": self.mongo_client.db is not None,
            "audit_active": self.audit_middleware.audit_collection is not None
        }