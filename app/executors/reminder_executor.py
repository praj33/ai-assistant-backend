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

logger = logging.getLogger(__name__)


class ReminderExecutor:
    def __init__(self):
        self.reminders_store = {}  # In-memory store; production uses MongoDB

    def create_reminder(self, message: str, remind_at: str = None,
                        user_id: str = "", trace_id: str = "") -> Dict[str, Any]:
        """Create a scheduled reminder."""
        try:
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

    def list_reminders(self, user_id: str = "", trace_id: str = "") -> Dict[str, Any]:
        """List all active reminders for a user."""
        try:
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

    def cancel_reminder(self, reminder_id: str, trace_id: str = "") -> Dict[str, Any]:
        """Cancel a scheduled reminder."""
        try:
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
