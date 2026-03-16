from __future__ import annotations

"""
Karma Adapter

Responsibilities:
- Fetch user karma / behavior score from the BHIV Karma hook.
- Provide a stable interface for Mitra runtime modules.
- Allow intelligence + enforcement layers to consume karma data deterministically.
"""

from typing import Any, Dict, Optional

from hooks.karma import karma_hook


def fetch_user_karma(principal: Optional[str]) -> Dict[str, Any]:
    """
    Resolve karma information for a given principal (user identifier).
    If principal is missing or karma cannot be resolved, returns a neutral score.
    """
    if not principal:
        return {
            "user_id": None,
            "karma_points": 50,
            "source": "karma_adapter",
        }

    try:
        raw = karma_hook(principal, action="interaction")
    except Exception:
        raw = {}

    points = raw.get("karma_points", 50) if isinstance(raw, dict) else 50
    return {
        "user_id": principal,
        "karma_points": points,
        "raw": raw,
        "source": "karma_adapter",
    }


def karma_bias_from_points(points: Any) -> float:
    """
    Convert a karma score (0–100 style) into a [0,1] bias input
    suitable for safety/intelligence context.
    """
    try:
        value = float(points)
    except Exception:
        value = 50.0
    # Clamp to [0,100] then normalize to [0,1]
    value = max(0.0, min(100.0, value))
    return value / 100.0

