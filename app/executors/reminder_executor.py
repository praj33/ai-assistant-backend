"""
Reminder Executor — Chandresh Integration
Creates and manages scheduled reminders stored in MongoDB.
Supports: create_reminder, list_reminders, cancel_reminder.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import uuid

from app.core.gateway_auth import GatewayAuthError, require_gateway_invocation

logger = logging.getLogger(__name__)


class ReminderExecutor:
    # Shared in-memory store so scheduler + gateway instances see same reminders.
    reminders_store: Dict[str, Dict[str, Any]] = {}

    def __init__(self):
        # In-memory store; production uses MongoDB. Shared across instances.
        self.reminders_store = ReminderExecutor.reminders_store

    def create_reminder(self, message: str, remind_at: str = None,
                        user_id: str = "", trace_id: str = "", gateway_auth: str = None) -> Dict[str, Any]:
        """Create a scheduled reminder."""
        try:
            try:
                require_gateway_invocation(
                    gateway_auth=gateway_auth,
                    trace_id=trace_id,
                    platform="reminder",
                    action="create_reminder",
                )
            except GatewayAuthError as e:
                return {
                    "status": "error",
                    "error": f"unauthorized: {str(e)}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "reminder",
                }

            reminder_id = f"rem_{uuid.uuid4().hex[:12]}"

            # Parse remind_at or default to 1 hour from now
            if remind_at:
                try:
                    remind_dt = datetime.fromisoformat(remind_at.replace("Z", "+00:00"))
                except Exception:
                    remind_dt = datetime.utcnow() + timedelta(hours=1)
            else:
                remind_dt = datetime.utcnow() + timedelta(hours=1)

            reminder = {
                "reminder_id": reminder_id,
                "message": message,
                "remind_at": remind_dt.isoformat(),
                "user_id": user_id,
                "status": "scheduled",
                "created_at": datetime.utcnow().isoformat()
            }

            # Store in memory (production: save to MongoDB)
            self.reminders_store[reminder_id] = reminder

            logger.info(f"[{trace_id}] Reminder created: {reminder_id} at {remind_dt.isoformat()}")
            return {
                "status": "success",
                "action": "create_reminder",
                "reminder_id": reminder_id,
                "message": message,
                "remind_at": remind_dt.isoformat(),
                "method": "reminder_service",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "reminder"
            }

        except Exception as e:
            logger.error(f"[{trace_id}] Reminder creation failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}

    def list_reminders(self, user_id: str = "", trace_id: str = "", gateway_auth: str = None) -> Dict[str, Any]:
        """List all active reminders for a user."""
        try:
            try:
                require_gateway_invocation(
                    gateway_auth=gateway_auth,
                    trace_id=trace_id,
                    platform="reminder",
                    action="list_reminders",
                )
            except GatewayAuthError as e:
                return {
                    "status": "error",
                    "error": f"unauthorized: {str(e)}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "reminder",
                }

            reminders = [r for r in self.reminders_store.values()
                        if r.get("user_id") == user_id or not user_id]

            logger.info(f"[{trace_id}] Listed {len(reminders)} reminders")
            return {
                "status": "success",
                "action": "list_reminders",
                "reminders": reminders,
                "count": len(reminders),
                "method": "reminder_service",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "reminder"
            }

        except Exception as e:
            logger.error(f"[{trace_id}] List reminders failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}

    def cancel_reminder(self, reminder_id: str, trace_id: str = "", gateway_auth: str = None) -> Dict[str, Any]:
        """Cancel a scheduled reminder."""
        try:
            try:
                require_gateway_invocation(
                    gateway_auth=gateway_auth,
                    trace_id=trace_id,
                    platform="reminder",
                    action="cancel_reminder",
                )
            except GatewayAuthError as e:
                return {
                    "status": "error",
                    "error": f"unauthorized: {str(e)}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "reminder",
                }

            if reminder_id in self.reminders_store:
                self.reminders_store[reminder_id]["status"] = "cancelled"
                logger.info(f"[{trace_id}] Reminder cancelled: {reminder_id}")
                return {
                    "status": "success",
                    "action": "cancel_reminder",
                    "reminder_id": reminder_id,
                    "method": "reminder_service",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "reminder"
                }
            else:
                return {
                    "status": "error",
                    "error": f"Reminder {reminder_id} not found",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"[{trace_id}] Cancel reminder failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}

    def pop_due_reminders(self, now: Optional[datetime] = None) -> list[Dict[str, Any]]:
        """
        Pop due reminders for delivery (scheduler use).
        This is not an outbound action; it does not require gateway_auth.
        """
        now_dt = now or datetime.utcnow()
        due: list[Dict[str, Any]] = []

        for rid, r in list(self.reminders_store.items()):
            try:
                if r.get("status") != "scheduled":
                    continue
                remind_at = r.get("remind_at")
                if not remind_at:
                    continue
                try:
                    remind_dt = datetime.fromisoformat(str(remind_at).replace("Z", "+00:00"))
                except Exception:
                    continue
                if remind_dt <= now_dt:
                    # Mark as firing so we don't pick it up twice.
                    self.reminders_store[rid]["status"] = "firing"
                    due.append(self.reminders_store[rid])
            except Exception:
                continue

        return due

    def deliver_reminder(self, reminder_id: str, trace_id: str = "", gateway_auth: str = None) -> Dict[str, Any]:
        """Mark reminder as delivered (gateway-only)."""
        try:
            try:
                require_gateway_invocation(
                    gateway_auth=gateway_auth,
                    trace_id=trace_id,
                    platform="reminder",
                    action="deliver_reminder",
                )
            except GatewayAuthError as e:
                return {
                    "status": "error",
                    "error": f"unauthorized: {str(e)}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "reminder",
                }

            reminder = self.reminders_store.get(reminder_id)
            if not reminder:
                return {
                    "status": "error",
                    "error": f"Reminder {reminder_id} not found",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "reminder",
                }

            reminder["status"] = "delivered"
            reminder["delivered_at"] = datetime.utcnow().isoformat()

            logger.info(f"[{trace_id}] Reminder delivered: {reminder_id}")
            return {
                "status": "success",
                "action": "deliver_reminder",
                "reminder_id": reminder_id,
                "message": reminder.get("message", ""),
                "remind_at": reminder.get("remind_at"),
                "user_id": reminder.get("user_id", ""),
                "method": "reminder_scheduler",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "reminder",
            }
        except Exception as e:
            logger.error(f"[{trace_id}] Deliver reminder failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}
