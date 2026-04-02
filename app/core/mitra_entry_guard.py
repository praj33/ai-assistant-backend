from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Iterator, Optional


_mitra_entry_scope: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "mitra_entry_scope",
    default=None,
)


@contextmanager
def mitra_enforcement_scope(trace_id: str, source: str) -> Iterator[None]:
    token = _mitra_entry_scope.set(
        {
            "trace_id": str(trace_id or "").strip(),
            "source": str(source or "mitra_control_plane"),
        }
    )
    try:
        yield
    finally:
        _mitra_entry_scope.reset(token)


def get_mitra_entry_scope() -> Optional[Dict[str, Any]]:
    scope = _mitra_entry_scope.get()
    if not scope:
        return None
    return dict(scope)


def has_mitra_enforcement_scope(trace_id: str | None = None) -> bool:
    scope = get_mitra_entry_scope()
    if not scope:
        return False
    if trace_id is None:
        return True
    return str(scope.get("trace_id") or "") == str(trace_id or "")
