from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional


def _iso_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _normalize_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_timestamp(value: Optional[str]) -> str:
    timestamp = _normalize_str(value)
    return timestamp or _iso_now()


def resolve_outbound_action_type(platform: str) -> str:
    mapping = {
        "whatsapp": "whatsapp_send",
        "email": "email_send",
        "instagram": "instagram_dm_send",
        "sms": "sms_send",
        "telegram": "telegram_send",
        "notification": "notification_send",
    }
    platform_key = _normalize_str(platform).lower()
    if not platform_key:
        return "message_send"
    return mapping.get(platform_key, f"{platform_key}_send")


def build_inbound_payload(
    *,
    content: str,
    source: str,
    user_id: str,
    channel: str,
    metadata: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,
    message_id: Optional[str] = None,
    thread_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "direction": "inbound",
        "content": _normalize_str(content),
        "source": _normalize_str(source),
        "user_id": _normalize_str(user_id),
        "channel": _normalize_str(channel),
        "metadata": {
            "timestamp": _normalize_timestamp(timestamp),
            "message_id": _normalize_str(message_id) or None,
            "thread_context": thread_context or None,
            "raw_metadata": metadata or {},
        },
    }


def build_outbound_payload(
    *,
    content: str,
    user_id: str,
    recipient: str,
    channel: str,
    action_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    platform = _normalize_str(channel)
    resolved_action_type = _normalize_str(action_type) or resolve_outbound_action_type(platform)
    return {
        "direction": "outbound",
        "action_type": resolved_action_type,
        "user_id": _normalize_str(user_id),
        "recipient": _normalize_str(recipient),
        "content": _normalize_str(content),
        "metadata": {
            "timestamp": _normalize_timestamp(timestamp),
            "channel_context": metadata or {},
        },
    }
