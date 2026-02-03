"""
UNIFIED ENFORCEMENT VERDICT
---------------------------
Single authoritative decision surface.

NO component may override this.
NO execution may occur without this verdict.
"""

from dataclasses import dataclass
from typing import Optional, Literal


DecisionType = Literal[
    "ALLOW",
    "REWRITE",
    "BLOCK",
    "TERMINATE",
]

ScopeType = Literal[
    "response",
    "action",
    "both",
]


@dataclass(frozen=True)
class EnforcementVerdict:
    """
    FINAL enforcement output.

    This object governs:
    - user-facing responses
    - real-world actions
    - execution termination
    """

    decision: DecisionType
    scope: ScopeType

    trace_id: str                # enforcement-owned, deterministic
    reason_code: str             # machine-readable justification

    # Optional fields (only when relevant)
    rewrite_class: Optional[str] = None
    safe_output: Optional[str] = None

    def is_allow(self) -> bool:
        return self.decision == "ALLOW"

    def is_block(self) -> bool:
        return self.decision in ("BLOCK", "TERMINATE")

    def allows_response(self) -> bool:
        return self.decision in ("ALLOW", "REWRITE") and self.scope in ("response", "both")

    def allows_action(self) -> bool:
        return self.decision == "ALLOW" and self.scope in ("action", "both")
