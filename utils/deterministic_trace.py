"""
Minimal deterministic trace id generator.

Raj's enforcement engine requires deterministic, replayable trace ids derived from:
- a canonical input snapshot
- the final enforcement category
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional


def generate_trace_id(*, input_payload: Dict[str, Any], enforcement_category: str, salt: Optional[str] = None) -> str:
    canonical = {
        "input_payload": input_payload,
        "enforcement_category": str(enforcement_category),
        "salt": salt or "",
    }
    blob = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    digest = hashlib.sha256(blob).hexdigest()[:16]
    return f"enf_{digest}"

