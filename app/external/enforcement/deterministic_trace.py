"""
Deterministic trace id generation for Raj's enforcement engine.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def generate_trace_id(
    *,
    input_payload: dict[str, Any],
    enforcement_category: str,
    salt: str | None = None,
) -> str:
    canonical = {
        "input_payload": input_payload,
        "enforcement_category": str(enforcement_category),
        "salt": salt or "",
    }
    blob = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    digest = hashlib.sha256(blob).hexdigest()[:16]
    return f"enf_{digest}"
