import json
import os
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional, Iterable

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

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): BucketService._normalize_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [BucketService._normalize_value(item) for item in value]
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    @classmethod
    def _integrity_hash(cls, trace_id: str, stage: str, data: Dict[str, Any]) -> str:
        canonical = {
            "trace_id": str(trace_id),
            "stage": str(stage),
            "data": cls._normalize_value(data),
        }
        blob = json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    @staticmethod
    def _field_present(data: Dict[str, Any], field_path: str) -> bool:
        current: Any = data
        for segment in field_path.split("."):
            if not isinstance(current, dict) or segment not in current:
                return False
            current = current[segment]
        return True

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
            normalized_data = self._normalize_value(data)
            log_entry = {
                "trace_id": trace_id,
                "stage": stage,
                "data": normalized_data,
                "integrity_hash": self._integrity_hash(trace_id, stage, normalized_data),
                "integrity_version": "sha256-v1",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "bucket_service",
            }
            BucketService._memory_logs.append(log_entry)
            if self.audit_middleware is not None and self.audit_middleware.audit_collection is not None:
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

    def get_artifact(self, trace_id: str, *, stage: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not trace_id:
            return None

        for entry in reversed(BucketService._memory_logs):
            if entry.get("trace_id") != trace_id:
                continue
            if stage is not None and entry.get("stage") != stage:
                continue
            return dict(entry)

        try:
            if self.audit_middleware is not None and self.audit_middleware.audit_collection is not None:
                query: Dict[str, Any] = {"artifact_id": trace_id}
                if stage is not None:
                    query["stage"] = stage
                doc = self.audit_middleware.audit_collection.find_one(
                    query,
                    sort=[("timestamp", -1)],
                )
                if doc:
                    payload = doc.get("data_after")
                    if isinstance(payload, dict):
                        return dict(payload)
        except Exception as exc:
            self.logger.error("Failed to retrieve artifact for %s: %s", trace_id, exc)

        return None

    def artifact_exists(self, trace_id: str, *, stage: Optional[str] = None) -> bool:
        return self.get_artifact(trace_id, stage=stage) is not None

    def validate_artifact(
        self,
        trace_id: str,
        *,
        stage: str,
        required_fields: Optional[Iterable[str]] = None,
        expected_trace_id: Optional[str] = None,
    ) -> bool:
        artifact = self.get_artifact(trace_id, stage=stage)
        if not artifact:
            return False

        data = artifact.get("data")
        if not isinstance(data, dict):
            return False

        integrity_hash = artifact.get("integrity_hash")
        if not integrity_hash:
            return False

        expected_hash = self._integrity_hash(
            str(artifact.get("trace_id", trace_id)),
            str(artifact.get("stage", stage)),
            data,
        )
        if integrity_hash != expected_hash:
            return False

        if expected_trace_id is not None:
            embedded_trace_id = data.get("trace_id")
            if str(embedded_trace_id or "") != str(expected_trace_id):
                return False

        if required_fields:
            for field_path in required_fields:
                if not self._field_present(data, field_path):
                    return False

        return True

    def get_trace_logs(self, trace_id: str) -> Optional[list]:
        try:
            if self.audit_middleware is not None and self.audit_middleware.audit_collection is not None:
                logs = list(
                    self.audit_middleware.audit_collection.find({"artifact_id": trace_id}).sort("timestamp", -1)
                )
                if logs:
                    return logs

            return [entry for entry in BucketService._memory_logs if entry.get("trace_id") == trace_id]
        except Exception as exc:
            self.logger.error("Failed to retrieve trace logs for %s: %s", trace_id, exc)
            return None

    def find_recent_stage_events(
        self,
        stage: str,
        *,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        exclude_trace_id: Optional[str] = None,
        limit: int = 10,
    ) -> list[Dict[str, Any]]:
        matches: list[Dict[str, Any]] = []
        normalized_user_id = str(user_id) if user_id is not None else None
        normalized_session_id = str(session_id) if session_id is not None else None

        for entry in reversed(BucketService._memory_logs):
            if entry.get("stage") != stage:
                continue
            if exclude_trace_id and entry.get("trace_id") == exclude_trace_id:
                continue

            data = entry.get("data") or {}
            if normalized_user_id is not None and str(data.get("user_id")) != normalized_user_id:
                continue
            if normalized_session_id is not None and str(data.get("session_id")) != normalized_session_id:
                continue

            matches.append(dict(entry))
            if len(matches) >= limit:
                return matches

        try:
            if self.audit_middleware is not None and self.audit_middleware.audit_collection is not None:
                query: Dict[str, Any] = {"stage": stage}
                if normalized_user_id is not None:
                    query["data_after.data.user_id"] = normalized_user_id
                if normalized_session_id is not None:
                    query["data_after.data.session_id"] = normalized_session_id
                if exclude_trace_id:
                    query["artifact_id"] = {"$ne": exclude_trace_id}

                docs = list(
                    self.audit_middleware.audit_collection.find(query).sort("timestamp", -1).limit(limit)
                )
                for doc in docs:
                    payload = doc.get("data_after")
                    if isinstance(payload, dict):
                        matches.append(dict(payload))
                        if len(matches) >= limit:
                            break
        except Exception as exc:
            self.logger.error("Failed to query recent stage events for %s: %s", stage, exc)

        return matches[:limit]

    def get_status(self) -> Dict[str, Any]:
        return {
            "service": "bucket_service",
            "status": "active",
            "mongo_connected": self.mongo_client.db is not None if self.mongo_client else False,
            "audit_active": self.audit_middleware.audit_collection is not None if self.audit_middleware else False,
            "fallback_mode": self.mongo_client.db is None if self.mongo_client else True,
            "mongo_error": self.mongo_client.connection_error() if self.mongo_client else "mongo_client_unavailable",
        }
