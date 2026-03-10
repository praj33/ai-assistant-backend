"""
Device Bridge Service - Universal Device Bridge Foundation

Thin service wrapper around the gateway-enforced DeviceGatewayExecutor.
This is the "device_bridge_service.py" requested in the task spec.

All real command execution still goes through:
Safety -> Enforcement -> ExecutionService -> DeviceGatewayExecutor
"""

import json
from typing import Any, Dict

from app.services.enforcement_service import EnforcementService
from app.services.execution_service import ExecutionService


class DeviceBridgeService:
    """Facade for sending device commands through the universal execution gateway."""

    def __init__(self) -> None:
        self.enforcement = EnforcementService()
        self.gateway = ExecutionService()

    def send_command(
        self,
        device_id: str,
        device_type: str,
        command: str,
        payload: Dict[str, Any] | None = None,
        authenticated_user_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Public API for device command requests from Mitra.
        Every command request is re-validated by Raj's runtime before execution.
        """
        trace_id = f"trace_device_bridge_{device_id or 'anon'}"
        action_data: Dict[str, Any] = {
            "action": "send_command",
            "device_id": device_id,
            "device_type": device_type,
            "command": command,
            "payload": payload or {},
        }
        command_summary = json.dumps(action_data, sort_keys=True, default=str)
        enforcement_payload = {
            "user_input": f"device_gateway:{command_summary}",
            "intent": "device_gateway_command",
            "trace_id": trace_id,
            "platform_policy": {
                "platform": "device_gateway",
                "device_type": device_type,
            },
            "authenticated_user_context": authenticated_user_context or {
                "session_id": device_id,
                "platform": "device_gateway",
                "device": device_type,
                "auth_method": "device_bridge_service",
            },
        }
        enforcement_result = self.enforcement.enforce_policy(payload=enforcement_payload, trace_id=trace_id)
        return self.gateway.execute_action(
            "device_gateway",
            action_data,
            trace_id,
            enforcement_decision=enforcement_result,
        )

    def get_status(self) -> Dict[str, Any]:
        """Return current gateway/device bridge status."""
        status = self.gateway.get_status()
        return {
            "service": "device_bridge_service",
            "gateway": status.get("service"),
            "platforms": status.get("platforms"),
            "device_gateway": status.get("device_gateway"),
            "enforcement_required": status.get("enforcement_required"),
        }
