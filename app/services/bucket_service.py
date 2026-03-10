import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from app.external.bucket.database.mongo_db import MongoDBClient
from app.external.bucket.middleware.audit_middleware import AuditMiddleware
from app.external.bucket.utils.logger import get_logger


class BucketService:
    _memory_logs: list[Dict[str, Any]] = []

    @staticmethod
    def _env_bool(name: str, default: bool) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    @classmethod
    def clear_memory_logs(cls) -> None:
        cls._memory_logs.clear()

    def __init__(self):
        self.logger = get_logger(__name__)
        self.mongo_client = MongoDBClient()
        self.audit_middleware = AuditMiddleware(
            self.mongo_client.db if self.mongo_client and self.mongo_client.db is not None else None
        )

    def enforcement_artifact_required(self) -> bool:
        return self._env_bool("BUCKET_MONGO_ENABLED", True)

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
            if self.audit_middleware and self.audit_middleware.audit_collection:
                self.audit_middleware.audit_collection.insert_one(
                    {
                        "timestamp": datetime.utcnow(),
                        "operation_type": "CREATE",
                        "artifact_id": trace_id,
                        "requester_id": "bucket_service",
                        "integration_id": "mitra_runtime",
                        "status": "success",
                        "stage": stage,
                        "data_after": log_entry,
                        "immutable": True,
                        "audit_version": "1.0",
                    }
                )
            self.logger.info("BUCKET_LOG [%s] %s: %s", trace_id, stage, json.dumps(log_entry, default=str))
            return True
        except Exception as exc:
            self.logger.error("Bucket logging failed for %s: %s", trace_id, exc)
            return False

    def artifact_exists(self, trace_id: str, *, stage: Optional[str] = None) -> bool:
        if not trace_id:
            return False

        if any(
            entry.get("trace_id") == trace_id and (stage is None or entry.get("stage") == stage)
            for entry in BucketService._memory_logs
        ):
            return True

        try:
            if self.audit_middleware and self.audit_middleware.audit_collection:
                query: Dict[str, Any] = {"artifact_id": trace_id}
                if stage is not None:
                    query["stage"] = stage
                return self.audit_middleware.audit_collection.find_one(query) is not None
        except Exception as exc:
            self.logger.error("Failed to validate artifact for %s: %s", trace_id, exc)

        return False

    def get_trace_logs(self, trace_id: str) -> Optional[list]:
        try:
            if self.audit_middleware and self.audit_middleware.audit_collection:
                logs = list(
                    self.audit_middleware.audit_collection.find({"artifact_id": trace_id}).sort("timestamp", -1)
                )
                if logs:
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
