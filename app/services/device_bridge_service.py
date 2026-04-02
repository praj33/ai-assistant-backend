"""
Device Bridge Service - Universal Device Bridge Foundation

Thin service wrapper around the gateway-enforced DeviceGatewayExecutor.
This is the "device_bridge_service.py" requested in the task spec.

All real command execution still goes through:
Safety -> Enforcement -> ExecutionService -> DeviceGatewayExecutor
"""

import json
from typing import Any, Dict

from app.services.execution_service import ExecutionService
from app.services.mitra_control_plane_service import MitraAuthorityInput, MitraControlPlaneService


class DeviceBridgeService:
    """Facade for sending device commands through the universal execution gateway."""

    def __init__(self) -> None:
        self.control_plane = MitraControlPlaneService()
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
        auth_context = authenticated_user_context or {
            "session_id": device_id,
            "platform": "device_gateway",
            "device": device_type,
            "auth_method": "device_bridge_service",
            "principal": device_id or "device_gateway",
        }
        authority_result = self.control_plane.evaluate(
            MitraAuthorityInput(
                input_text=f"device_gateway:{command_summary}",
                raw_input=action_data,
                category="device_gateway_command",
                user_id=str(auth_context.get("principal") or device_id or "device_gateway"),
                session_id=device_id or None,
                platform="device_gateway",
                device=device_type or "device",
                authenticated_user_context=auth_context,
                trace_id=trace_id,
                source="device_bridge_service",
            )
        )
        enforcement_result = authority_result["enforcement_result"]
        trace_id = authority_result["trace_id"]
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
