"""
Gateway Invocation Auth — Universal Execution Gateway

Purpose:
- Prevent direct executor invocation bypass by requiring a gateway-signed token
  for any outbound platform action (send message / create event / etc).

This is "Sovereign Chain preparation only":
- No chain logic is modified.
- A lightweight signing/verification primitive is provided (HMAC) so that
  adapters can verify calls came through the gateway enforcement boundary.
"""

from __future__ import annotations

import base64
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Dict, Optional


class GatewayAuthError(Exception):
    pass


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("utf-8"))


def _canonical_json(obj: Dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _secret() -> bytes:
    # If not provided, generate an ephemeral secret per-process (good for local dev/tests).
    # In production, set GATEWAY_SIGNING_SECRET to keep verification stable across instances.
    value = os.getenv("GATEWAY_SIGNING_SECRET")
    if value:
        return value.encode("utf-8")
    # Ephemeral but stable within process
    if not hasattr(_secret, "_ephemeral"):
        setattr(_secret, "_ephemeral", uuid.uuid4().hex.encode("utf-8"))
    return getattr(_secret, "_ephemeral")


@dataclass(frozen=True)
class GatewayInvocationClaims:
    trace_id: str
    platform: str
    action: str
    decision: str
    iat: int
    exp: int
    nonce: str
    issuer: str = "universal_execution_gateway"
    version: str = "1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "v": self.version,
            "iss": self.issuer,
            "trace_id": self.trace_id,
            "platform": self.platform,
            "action": self.action,
            "decision": self.decision,
            "iat": self.iat,
            "exp": self.exp,
            "nonce": self.nonce,
        }


class GatewayAuth:
    @staticmethod
    def issue(
        *,
        trace_id: str,
        platform: str,
        action: str,
        decision: str,
        ttl_seconds: int = 300,
    ) -> str:
        now = int(time.time())
        claims = GatewayInvocationClaims(
            trace_id=trace_id,
            platform=platform,
            action=action,
            decision=decision,
            iat=now,
            exp=now + int(ttl_seconds),
            nonce=uuid.uuid4().hex,
        ).to_dict()

        payload = _canonical_json(claims)
        sig = hmac.new(_secret(), payload, sha256).digest()
        return f"{_b64url_encode(payload)}.{_b64url_encode(sig)}"

    @staticmethod
    def verify(
        token: str,
        *,
        expected_trace_id: Optional[str] = None,
        expected_platform: Optional[str] = None,
        expected_action: Optional[str] = None,
        now: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not token or "." not in token:
            raise GatewayAuthError("missing_or_malformed_gateway_token")

        payload_b64, sig_b64 = token.split(".", 1)
        payload = _b64url_decode(payload_b64)
        sig = _b64url_decode(sig_b64)

        expected_sig = hmac.new(_secret(), payload, sha256).digest()
        if not hmac.compare_digest(sig, expected_sig):
            raise GatewayAuthError("invalid_gateway_token_signature")

        try:
            claims = json.loads(payload.decode("utf-8"))
        except Exception as e:
            raise GatewayAuthError(f"invalid_gateway_token_payload:{e}") from e

        now_ts = int(time.time()) if now is None else int(now)
        exp = int(claims.get("exp", 0))
        if exp and now_ts > exp:
            raise GatewayAuthError("expired_gateway_token")

        if expected_trace_id and claims.get("trace_id") != expected_trace_id:
            raise GatewayAuthError("gateway_token_trace_mismatch")
        if expected_platform and str(claims.get("platform", "")).lower() != str(expected_platform).lower():
            raise GatewayAuthError("gateway_token_platform_mismatch")
        if expected_action and str(claims.get("action", "")).lower() != str(expected_action).lower():
            raise GatewayAuthError("gateway_token_action_mismatch")

        return claims


def require_gateway_invocation(
    *,
    gateway_auth: Optional[str],
    trace_id: str,
    platform: str,
    action: str,
) -> Dict[str, Any]:
    """
    Enforced adapter-side guard:
    - Any outbound action must present a valid gateway invocation token.
    """
    if not gateway_auth:
        raise GatewayAuthError("unauthorized_direct_executor_call")
    return GatewayAuth.verify(
        gateway_auth,
        expected_trace_id=trace_id,
        expected_platform=platform,
        expected_action=action,
    )

