"""
Tracked Bucket logger bridge for Raj's enforcement engine.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def log_enforcement_event(
    trace_id: str,
    input_snapshot: dict[str, Any],
    akanksha_verdict: dict[str, Any] | None,
    evaluator_results: list[Any],
    final_decision: str,
) -> None:
    payload = {
        "event_type": "raj_enforcement_audit",
        "audit_version": "1.0",
        "input_snapshot": input_snapshot,
        "akanksha_verdict": akanksha_verdict,
        "evaluator_results": [
            getattr(result, "__dict__", str(result))
            for result in (evaluator_results or [])
        ],
        "final_decision": final_decision,
    }

    try:
        from app.services.bucket_service import BucketService

        persisted = BucketService().log_event(
            trace_id,
            "raj_enforcement_engine",
            payload,
        )
        if persisted:
            return
    except Exception as exc:
        logger.warning("Bucket persistence failed for %s: %s", trace_id, exc)

    logger.info(
        "RAJ_ENFORCEMENT_LOG [%s] %s",
        trace_id,
        json.dumps(payload, default=str),
    )


def log_enforcement(
    *,
    trace_id: str,
    input_snapshot: dict[str, Any],
    akanksha_verdict: dict[str, Any] | None,
    evaluator_results: list[Any],
    final_decision: str,
) -> None:
    log_enforcement_event(
        trace_id=trace_id,
        input_snapshot=input_snapshot,
        akanksha_verdict=akanksha_verdict,
        evaluator_results=evaluator_results,
        final_decision=final_decision,
    )
