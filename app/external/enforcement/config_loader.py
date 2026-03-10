"""
Environment-driven runtime config for Raj's enforcement engine.
"""

from __future__ import annotations

import os


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


RUNTIME_CONFIG = {
    "kill_switch": _env_bool("ENFORCEMENT_KILL_SWITCH", False),
}
