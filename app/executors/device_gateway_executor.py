"""
Device Gateway Executor — Universal Device Adapter Interface
Prepares assistant to communicate with user devices.
Supports: desktop, mobile, tablet, XR.
Gateway-only — no OS-level control. Device-side agent comes next phase.
"""

import os
from typing import Dict, Any
from datetime import datetime
import logging
import uuid

from app.core.gateway_auth import GatewayAuthError, require_gateway_invocation

logger = logging.getLogger(__name__)

SUPPORTED_DEVICE_TYPES = ["desktop", "mobile", "tablet", "xr"]


class DeviceGatewayExecutor:
    def __init__(self):
        self.gateway_id = f"gateway_{uuid.uuid4().hex[:8]}"
        self.connected_devices = {}

    def send_command(self, device_id: str, device_type: str, command: str,
                     payload: Dict[str, Any] = None, trace_id: str = "", gateway_auth: str = None) -> Dict[str, Any]:
        """Send a command to a device via the gateway."""
        try:
            try:
                require_gateway_invocation(
                    gateway_auth=gateway_auth,
                    trace_id=trace_id,
                    platform="device_gateway",
                    action="send_command",
                )
            except GatewayAuthError as e:
                return {
                    "status": "error",
                    "error": f"unauthorized: {str(e)}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "device_gateway",
                }

            if device_type.lower() not in SUPPORTED_DEVICE_TYPES:
                return {
                    "status": "error",
                    "error": f"Unsupported device type: {device_type}. Supported: {SUPPORTED_DEVICE_TYPES}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()
                }

            command_id = f"cmd_{uuid.uuid4().hex[:12]}"
            command_data = {
                "command_id": command_id,
                "device_id": device_id,
                "device_type": device_type,
                "command": command,
                "payload": payload or {},
                "command_status": "queued",
                "gateway_id": self.gateway_id
            }

            # Gateway mode — queue the command for device-side agent pickup
            logger.info(f"[{trace_id}] Device gateway: queuing command '{command}' for {device_type}:{device_id}")
            return {
                "status": "success",
                "action": "send_command",
                **command_data,
                "method": "device_gateway",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "device_gateway",
                "note": "Command queued. Device-side agent will pick up in next phase."
            }

        except Exception as e:
            logger.error(f"[{trace_id}] Device gateway send_command failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}

    def register_device(self, device_id: str, device_type: str, device_name: str = "",
                        trace_id: str = "", gateway_auth: str = None) -> Dict[str, Any]:
        """Register a device with the gateway."""
        try:
            try:
                require_gateway_invocation(
                    gateway_auth=gateway_auth,
                    trace_id=trace_id,
                    platform="device_gateway",
                    action="register_device",
                )
            except GatewayAuthError as e:
                return {
                    "status": "error",
                    "error": f"unauthorized: {str(e)}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "device_gateway",
                }

            if device_type.lower() not in SUPPORTED_DEVICE_TYPES:
                return {
                    "status": "error",
                    "error": f"Unsupported device type: {device_type}",
                    "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()
                }

            self.connected_devices[device_id] = {
                "device_id": device_id,
                "device_type": device_type,
                "device_name": device_name or f"{device_type}_{device_id[:6]}",
                "registered_at": datetime.utcnow().isoformat(),
                "status": "connected"
            }

            logger.info(f"[{trace_id}] Device registered: {device_type}:{device_id}")
            return {
                "status": "success", "action": "register_device",
                "device_id": device_id, "device_type": device_type,
                "device_name": device_name,
                "method": "device_gateway", "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(), "platform": "device_gateway"
            }

        except Exception as e:
            logger.error(f"[{trace_id}] Device registration failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}

    def list_devices(self, trace_id: str = "", gateway_auth: str = None) -> Dict[str, Any]:
        """List all registered devices."""
        try:
            require_gateway_invocation(
                gateway_auth=gateway_auth,
                trace_id=trace_id,
                platform="device_gateway",
                action="list_devices",
            )
        except GatewayAuthError as e:
            return {
                "status": "error",
                "error": f"unauthorized: {str(e)}",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "device_gateway",
            }

        return {
            "status": "success", "action": "list_devices",
            "devices": list(self.connected_devices.values()),
            "count": len(self.connected_devices),
            "gateway_id": self.gateway_id,
            "method": "device_gateway", "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(), "platform": "device_gateway"
        }

    def get_status(self) -> Dict[str, Any]:
        """Get gateway status."""
        return {
            "service": "device_gateway",
            "gateway_id": self.gateway_id,
            "status": "active",
            "supported_devices": SUPPORTED_DEVICE_TYPES,
            "connected_devices": len(self.connected_devices),
            "timestamp": datetime.utcnow().isoformat()
        }
