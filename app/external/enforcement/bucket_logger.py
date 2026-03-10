"""
Tracked Bucket logger bridge for Raj's enforcement engine.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def log_enforcement(
    *,
    trace_id: str,
    input_snapshot: dict[str, Any],
    akanksha_verdict: dict[str, Any] | None,
    evaluator_results: list[Any],
    final_decision: str,
) -> None:
    payload = {
        "input_snapshot": input_snapshot,
        "akanksha_verdict": akanksha_verdict,
        "evaluator_results": [
            getattr(result, "__dict__", str(result))
            for result in (evaluator_results or [])
        ],
        "final_decision": final_decision,
    }

    use_bucket = os.getenv("BUCKET_LOGGER_USE_BUCKETSERVICE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    if use_bucket:
        try:
            from app.services.bucket_service import BucketService

            BucketService().log_event(
                trace_id,
                "raj_enforcement_engine",
                payload,
            )
            return
        except Exception:
            pass

    logger.info(
        "RAJ_ENFORCEMENT_LOG [%s] %s",
        trace_id,
        json.dumps(payload, default=str),
    )
