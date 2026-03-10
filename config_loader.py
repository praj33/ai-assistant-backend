"""
Minimal runtime config loader for Raj's enforcement engine.

The deterministic enforcement engine imports `RUNTIME_CONFIG` directly.
This module provides a small, environment-driven config surface.
"""

from __future__ import annotations

import os


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


RUNTIME_CONFIG = {
    # Absolute kill switch for enforcement runtime.
    # When enabled, enforcement_engine returns TERMINATE fail-closed.
    "kill_switch": _env_bool("ENFORCEMENT_KILL_SWITCH", False),
}

