"""
Execution Service Adapter — Universal Execution Gateway
Routes all platform actions through enforcement-gated execution.
Supports: WhatsApp, Email, Instagram, Telegram, Calendar, Reminder, EMS, Device Gateway.
Nothing executes without enforcement ALLOW.
"""

from typing import Dict, Any
from datetime import datetime

# Import all platform executors
from app.executors.whatsapp_executor import WhatsAppExecutor
from app.executors.email_executor import EmailExecutor
from app.executors.instagram_executor import InstagramExecutor
from app.executors.telegram_executor import TelegramExecutor
from app.executors.calendar_executor import CalendarExecutor
from app.executors.reminder_executor import ReminderExecutor
from app.executors.ems_executor import EMSExecutor
from app.executors.device_gateway_executor import DeviceGatewayExecutor
from app.core.gateway_auth import GatewayAuth
from app.external.enforcement.enforcement_verdict import EnforcementVerdict
from app.services.telegram_contact_service import TelegramContactService


class ExecutionService:
    """Universal execution gateway for all platform actions.
    Every action must pass through enforcement before reaching any executor."""
    
    SUPPORTED_PLATFORMS = [
        "whatsapp", "email", "instagram", "telegram",
        "calendar", "reminder", "ems", "device_gateway"
    ]
    
    def __init__(self):
        self.whatsapp = WhatsAppExecutor()
        self.email = EmailExecutor()
        self.instagram = InstagramExecutor()
        self.telegram = TelegramExecutor()
        self.calendar = CalendarExecutor()
        self.reminder = ReminderExecutor()
        self.ems = EMSExecutor()
        self.device_gateway = DeviceGatewayExecutor()

    def _coerce_enforcement_verdict(self, enforcement_input: Any, trace_id: str) -> EnforcementVerdict:
        if isinstance(enforcement_input, EnforcementVerdict):
            return enforcement_input

        if isinstance(enforcement_input, dict):
            decision = str(enforcement_input.get("decision", "BLOCK")).upper()
            scope = enforcement_input.get("scope")
            if not scope:
                scope = "response" if decision == "REWRITE" else "both"
            return EnforcementVerdict(
                decision=decision if decision in {"ALLOW", "REWRITE", "BLOCK", "TERMINATE"} else "BLOCK",
                scope=scope if scope in {"response", "action", "both"} else "both",
                trace_id=str(enforcement_input.get("trace_id") or trace_id),
                reason_code=str(enforcement_input.get("reason_code") or "RUNTIME_VERDICT_DICT"),
                rewrite_class=enforcement_input.get("rewrite_class"),
                safe_output=enforcement_input.get("safe_output"),
            )

        decision = str(enforcement_input or "BLOCK").upper()
        scope = "response" if decision == "REWRITE" else "both"
        return EnforcementVerdict(
            decision=decision if decision in {"ALLOW", "REWRITE", "BLOCK", "TERMINATE"} else "BLOCK",
            scope=scope,
            trace_id=trace_id,
            reason_code="LEGACY_RUNTIME_DECISION",
        )
        
    def execute_action(self, action_type: str, action_data: Dict[str, Any],
                       trace_id: str, enforcement_decision: Any) -> Dict[str, Any]:
        """
        Execute action based on enforcement decision using real platform APIs.
        
        CRITICAL: Nothing executes without enforcement ALLOW.
        Safety → Enforcement → Orchestration → Execution
        """
        try:
            # ─── ENFORCEMENT GATE ───
            # Harden execution boundary — never trust caller blindly
            verdict = self._coerce_enforcement_verdict(enforcement_decision, trace_id)
            # Phase 5: execution authority gate — ONLY ALLOW may execute real-world actions
            if not verdict.allows_action():
                return {
                    "status": "blocked",
                    "action_type": action_type,
                    "reason": f"Action blocked by enforcement policy: {verdict.decision}",
                    "enforcement": {
                        "decision": verdict.decision,
                        "scope": verdict.scope,
                        "trace_id": verdict.trace_id,
                        "reason_code": verdict.reason_code,
                    },
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": "execution_service"
                }
            # Note: REWRITE affects responses, not actions; do not execute on REWRITE.
            
            platform = action_type.lower()
            decision = verdict.decision
            gateway_action = "execute"
            
            # ─── PLATFORM ROUTING ───
            
            if platform == "whatsapp":
                gateway_action = "send_message"
                gateway_auth = GatewayAuth.issue(
                    trace_id=trace_id,
                    platform=platform,
                    action=gateway_action,
                    decision=decision,
                )
                return self.whatsapp.send_message(
                    to_number=action_data.get("recipient", action_data.get("to", "")),
                    message=action_data.get("message", ""),
                    trace_id=trace_id,
                    gateway_auth=gateway_auth,
                )
            
            elif platform == "email":
                gateway_action = "send_message"
                gateway_auth = GatewayAuth.issue(
                    trace_id=trace_id,
                    platform=platform,
                    action=gateway_action,
                    decision=decision,
                )
                return self.email.send_message(
                    to_email=action_data.get("recipient", action_data.get("to", "")),
                    subject=action_data.get("subject", "Message from AI Assistant"),
                    message=action_data.get("body", action_data.get("message", "")),
                    trace_id=trace_id,
                    gateway_auth=gateway_auth,
                )
            
            elif platform == "instagram":
                gateway_action = "send_message"
                gateway_auth = GatewayAuth.issue(
                    trace_id=trace_id,
                    platform=platform,
                    action=gateway_action,
                    decision=decision,
                )
                return self.instagram.send_message(
                    recipient_id=action_data.get("recipient", action_data.get("to", "")),
                    message=action_data.get("message", ""),
                    trace_id=trace_id,
                    gateway_auth=gateway_auth,
                )
            
            elif platform == "telegram":
                gateway_action = "send_message"
                gateway_auth = GatewayAuth.issue(
                    trace_id=trace_id,
                    platform=platform,
                    action=gateway_action,
                    decision=decision,
                )
                recipient = action_data.get("recipient", action_data.get("to", action_data.get("chat_id", "")))
                recipient_str = str(recipient) if recipient is not None else ""
                # If recipient is not a numeric chat_id, try to resolve via username mapping.
                if recipient_str and not recipient_str.lstrip("-").isdigit():
                    resolved = TelegramContactService().resolve_chat_id(recipient_str)
                    if resolved is not None:
                        recipient_str = str(resolved)
                return self.telegram.send_message(
                    to_chat_id=recipient_str,
                    message=action_data.get("message", ""),
                    trace_id=trace_id,
                    gateway_auth=gateway_auth,
                )
            
            elif platform == "calendar":
                action = action_data.get("action", "create_event")
                if action == "create_event":
                    gateway_action = "create_event"
                    gateway_auth = GatewayAuth.issue(
                        trace_id=trace_id,
                        platform=platform,
                        action=gateway_action,
                        decision=decision,
                    )
                    return self.calendar.create_event(
                        title=action_data.get("title", action_data.get("summary", "")),
                        start_time=action_data.get("start_time", ""),
                        end_time=action_data.get("end_time"),
                        description=action_data.get("description", ""),
                        location=action_data.get("location", ""),
                        trace_id=trace_id,
                        gateway_auth=gateway_auth,
                    )
                elif action == "update_event":
                    gateway_action = "update_event"
                    gateway_auth = GatewayAuth.issue(
                        trace_id=trace_id,
                        platform=platform,
                        action=gateway_action,
                        decision=decision,
                    )
                    return self.calendar.update_event(
                        event_id=action_data.get("event_id", ""),
                        updates=action_data.get("updates", {}),
                        trace_id=trace_id,
                        gateway_auth=gateway_auth,
                    )
                elif action == "delete_event":
                    gateway_action = "delete_event"
                    gateway_auth = GatewayAuth.issue(
                        trace_id=trace_id,
                        platform=platform,
                        action=gateway_action,
                        decision=decision,
                    )
                    return self.calendar.delete_event(
                        event_id=action_data.get("event_id", ""),
                        trace_id=trace_id,
                        gateway_auth=gateway_auth,
                    )
                elif action == "list_events":
                    gateway_action = "list_events"
                    gateway_auth = GatewayAuth.issue(
                        trace_id=trace_id,
                        platform=platform,
                        action=gateway_action,
                        decision=decision,
                    )
                    return self.calendar.list_events(trace_id=trace_id, gateway_auth=gateway_auth)
                else:
                    return {"status": "error", "error": f"Unknown calendar action: {action}",
                            "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}
            
            elif platform == "reminder":
                action = action_data.get("action", "create_reminder")
                if action == "create_reminder":
                    gateway_action = "create_reminder"
                    gateway_auth = GatewayAuth.issue(
                        trace_id=trace_id,
                        platform=platform,
                        action=gateway_action,
                        decision=decision,
                    )
                    return self.reminder.create_reminder(
                        message=action_data.get("message", ""),
                        remind_at=action_data.get("remind_at"),
                        user_id=action_data.get("user_id", ""),
                        trace_id=trace_id,
                        gateway_auth=gateway_auth,
                    )
                elif action == "list_reminders":
                    gateway_action = "list_reminders"
                    gateway_auth = GatewayAuth.issue(
                        trace_id=trace_id,
                        platform=platform,
                        action=gateway_action,
                        decision=decision,
                    )
                    return self.reminder.list_reminders(
                        user_id=action_data.get("user_id", ""),
                        trace_id=trace_id,
                        gateway_auth=gateway_auth,
                    )
                elif action == "cancel_reminder":
                    gateway_action = "cancel_reminder"
                    gateway_auth = GatewayAuth.issue(
                        trace_id=trace_id,
                        platform=platform,
                        action=gateway_action,
                        decision=decision,
                    )
                    return self.reminder.cancel_reminder(
                        reminder_id=action_data.get("reminder_id", ""),
                        trace_id=trace_id,
                        gateway_auth=gateway_auth,
                    )
                elif action == "deliver_reminder":
                    gateway_action = "deliver_reminder"
                    gateway_auth = GatewayAuth.issue(
                        trace_id=trace_id,
                        platform=platform,
                        action=gateway_action,
                        decision=decision,
                    )
                    return self.reminder.deliver_reminder(
                        reminder_id=action_data.get("reminder_id", ""),
                        trace_id=trace_id,
                        gateway_auth=gateway_auth,
                    )
                else:
                    return {"status": "error", "error": f"Unknown reminder action: {action}",
                            "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}
            
            elif platform == "ems":
                action = action_data.get("action", "create_task")
                if action == "create_task":
                    gateway_action = "create_task"
                    gateway_auth = GatewayAuth.issue(
                        trace_id=trace_id,
                        platform=platform,
                        action=gateway_action,
                        decision=decision,
                    )
                    return self.ems.create_task(
                        title=action_data.get("title", ""),
                        description=action_data.get("description", ""),
                        priority=action_data.get("priority", "medium"),
                        assignee=action_data.get("assignee", ""),
                        trace_id=trace_id,
                        gateway_auth=gateway_auth,
                    )
                elif action == "assign_task":
                    gateway_action = "assign_task"
                    gateway_auth = GatewayAuth.issue(
                        trace_id=trace_id,
                        platform=platform,
                        action=gateway_action,
                        decision=decision,
                    )
                    return self.ems.assign_task(
                        task_id=action_data.get("task_id", ""),
                        assignee=action_data.get("assignee", ""),
                        trace_id=trace_id,
                        gateway_auth=gateway_auth,
                    )
                elif action == "update_task":
                    gateway_action = "update_task"
                    gateway_auth = GatewayAuth.issue(
                        trace_id=trace_id,
                        platform=platform,
                        action=gateway_action,
                        decision=decision,
                    )
                    return self.ems.update_task(
                        task_id=action_data.get("task_id", ""),
                        updates=action_data.get("updates", {}),
                        trace_id=trace_id,
                        gateway_auth=gateway_auth,
                    )
                else:
                    return {"status": "error", "error": f"Unknown EMS action: {action}",
                            "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}
            
            elif platform == "device_gateway":
                action = action_data.get("action", "send_command")
                if action == "send_command":
                    gateway_action = "send_command"
                    gateway_auth = GatewayAuth.issue(
                        trace_id=trace_id,
                        platform=platform,
                        action=gateway_action,
                        decision=decision,
                    )
                    return self.device_gateway.send_command(
                        device_id=action_data.get("device_id", ""),
                        device_type=action_data.get("device_type", "desktop"),
                        command=action_data.get("command", ""),
                        payload=action_data.get("payload"),
                        trace_id=trace_id,
                        gateway_auth=gateway_auth,
                    )
                elif action == "register_device":
                    gateway_action = "register_device"
                    gateway_auth = GatewayAuth.issue(
                        trace_id=trace_id,
                        platform=platform,
                        action=gateway_action,
                        decision=decision,
                    )
                    return self.device_gateway.register_device(
                        device_id=action_data.get("device_id", ""),
                        device_type=action_data.get("device_type", ""),
                        device_name=action_data.get("device_name", ""),
                        trace_id=trace_id,
                        gateway_auth=gateway_auth,
                    )
                elif action == "list_devices":
                    gateway_action = "list_devices"
                    gateway_auth = GatewayAuth.issue(
                        trace_id=trace_id,
                        platform=platform,
                        action=gateway_action,
                        decision=decision,
                    )
                    return self.device_gateway.list_devices(trace_id=trace_id, gateway_auth=gateway_auth)
                else:
                    return {"status": "error", "error": f"Unknown device action: {action}",
                            "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}
            
            else:
                return {
                    "status": "failed",
                    "action_type": action_type,
                    "error": f"Unsupported platform: {action_type}. Supported: {self.SUPPORTED_PLATFORMS}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": "execution_service"
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "action_type": action_type,
                "error": str(e),
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "execution_service"
            }
    
    def _apply_rewrite(self, action_data: Dict[str, Any], action_type: str) -> Dict[str, Any]:
        """Apply enforcement rewrite to action data."""
        rewritten_data = action_data.copy()
        platform = action_type.lower()
        
        if platform in ["whatsapp", "telegram", "instagram"]:
            rewritten_data["message"] = "This message has been rewritten for safety compliance."
        elif platform == "email":
            rewritten_data["body"] = "This email content has been rewritten for safety compliance."
            rewritten_data["subject"] = "[REWRITTEN] " + action_data.get("subject", "AI Assistant Message")
        elif platform == "calendar":
            rewritten_data["description"] = "Event details rewritten for safety compliance."
        elif platform == "ems":
            rewritten_data["description"] = "Task details rewritten for safety compliance."
        
        return rewritten_data
    
    def get_status(self) -> Dict[str, Any]:
        """Get universal gateway status."""
        return {
            "service": "universal_execution_gateway",
            "status": "active",
            "platforms": self.SUPPORTED_PLATFORMS,
            "real_execution": True,
            "enforcement_required": True,
            "device_gateway": self.device_gateway.get_status(),
            "timestamp": datetime.utcnow().isoformat()
        }
