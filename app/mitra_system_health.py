from __future__ import annotations

"""
Mitra System Health

Provides a single function that returns a complete health snapshot
for the Mitra runtime, suitable for the `/health/system` endpoint
and BHIV Core integrations.
"""

from typing import Any, Dict
from datetime import datetime

from app.mitra_system_registry import mitra_registry
from app.services.bucket_service import BucketService


def get_system_health_snapshot() -> Dict[str, Any]:
    registry_snapshot = mitra_registry.snapshot()

    # Bucket deep status (if available)
    bucket = BucketService()
    bucket_status = (
        bucket.get_status() if hasattr(bucket, "get_status") else {"service": "bucket_service", "status": "unknown"}
    )

    return {
        "system": "mitra_runtime",
        "version": "3.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "modules": registry_snapshot,
        "bucket": bucket_status,
    }

