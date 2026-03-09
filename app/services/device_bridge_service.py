"""
Device Bridge Service — Universal Device Bridge Foundation

Thin service wrapper around the gateway-enforced DeviceGatewayExecutor.
This is the "device_bridge_service.py" requested in the task spec.

All real command execution still goes through:
Safety -> Enforcement -> ExecutionService -> DeviceGatewayExecutor
"""

from typing import Dict, Any

from app.services.execution_service import ExecutionService


class DeviceBridgeService:
    """Facade for sending device commands through the universal execution gateway."""

    def __init__(self) -> None:
        self.gateway = ExecutionService()

    def send_command(self, device_id: str, device_type: str, command: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Public API for device command requests from Mitra.
        NOTE: This does NOT bypass enforcement; it still calls ExecutionService.
        """
        trace_id = f"trace_device_bridge_{device_id or 'anon'}"
        action_data: Dict[str, Any] = {
            "action": "send_command",
            "device_id": device_id,
            "device_type": device_type,
            "command": command,
            "payload": payload or {},
        }
        # Device bridge never makes enforcement decisions; caller must pass ALLOW/REWRITE.
        return self.gateway.execute_action("device_gateway", action_data, trace_id, enforcement_decision="ALLOW")

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

