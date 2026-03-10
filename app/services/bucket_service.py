import json
from datetime import datetime
from typing import Any, Dict, Optional

from app.external.bucket.database.mongo_db import MongoDBClient
from app.external.bucket.middleware.audit_middleware import AuditMiddleware
from app.external.bucket.utils.logger import get_logger


class BucketService:
    _memory_logs: list[Dict[str, Any]] = []

    def __init__(self):
        self.logger = get_logger(__name__)
        self.mongo_client = MongoDBClient()
        self.audit_middleware = AuditMiddleware(
            self.mongo_client.db if self.mongo_client and self.mongo_client.db is not None else None
        )

    def log_event(self, trace_id: str, stage: str, data: Dict[str, Any]) -> bool:
        try:
            log_entry = {
                "trace_id": trace_id,
                "stage": stage,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "bucket_service",
            }
            BucketService._memory_logs.append(log_entry)
            self.logger.info("BUCKET_LOG [%s] %s: %s", trace_id, stage, json.dumps(log_entry, default=str))
            return True
        except Exception as exc:
            self.logger.error("Bucket logging failed for %s: %s", trace_id, exc)
            return False

    def get_trace_logs(self, trace_id: str) -> Optional[list]:
        try:
            if self.audit_middleware and self.audit_middleware.audit_collection:
                logs = list(
                    self.audit_middleware.audit_collection.find({"artifact_id": trace_id}).sort("timestamp", -1)
                )
                return logs

            return [entry for entry in BucketService._memory_logs if entry.get("trace_id") == trace_id]
        except Exception as exc:
            self.logger.error("Failed to retrieve trace logs for %s: %s", trace_id, exc)
            return None

    def get_status(self) -> Dict[str, Any]:
        return {
            "service": "bucket_service",
            "status": "active",
            "mongo_connected": self.mongo_client.db is not None if self.mongo_client else False,
            "audit_active": self.audit_middleware.audit_collection is not None if self.audit_middleware else False,
            "fallback_mode": self.mongo_client.db is None if self.mongo_client else True,
            "mongo_error": self.mongo_client.connection_error() if self.mongo_client else "mongo_client_unavailable",
        }
