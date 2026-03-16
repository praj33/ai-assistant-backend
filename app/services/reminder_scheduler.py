"""
Reminder Scheduler Service — Day 2B Integration

Runs scheduled reminders through the unified inbound gateway:
Safety -> Intelligence -> Enforcement -> Orchestrator -> ExecutionService

This remains gateway-only: it does not control devices directly; it records an audit trace
and marks reminders as delivered through the orchestrated execution path.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from app.executors.reminder_executor import ReminderExecutor
from app.services.bucket_service import BucketService
from app.inbound.reminder_event_handler import handle_reminder_event


@dataclass
class SchedulerConfig:
    poll_interval_seconds: float = 1.0
    max_batch: int = 25


class ReminderScheduler:
    def __init__(self, config: Optional[SchedulerConfig] = None):
        self.config = config or SchedulerConfig()
        self.bucket = BucketService()
        self.reminders = ReminderExecutor()

        self._stop = asyncio.Event()

    async def start(self):
        self._stop.clear()
        while not self._stop.is_set():
            try:
                await self.tick()
            except Exception:
                # Fail-soft for scheduler loop; enforcement still gates execution.
                pass
            await asyncio.sleep(self.config.poll_interval_seconds)

    def stop(self):
        self._stop.set()

    async def tick(self) -> Dict[str, Any]:
        """
        Execute one scheduler tick:
        - pop due reminders
        - route through inbound gateway
        """
        due = self.reminders.pop_due_reminders(now=datetime.utcnow())
        due = due[: self.config.max_batch]

        deliveries = []
        for reminder in due:
            reminder_id = reminder.get("reminder_id", "")
            message = reminder.get("message", "")
            self.bucket.log_event(reminder_id or "reminder_unknown", "reminder_due", {"reminder": reminder})

            delivery = await handle_reminder_event(reminder)
            deliveries.append(
                {
                    "trace_id": delivery.get("trace_id"),
                    "reminder_id": reminder_id,
                    "decision": (
                        delivery.get("result", {})
                        .get("enforcement", {})
                        .get("decision", "BLOCK")
                    ),
                    "delivery": delivery,
                }
            )

        return {"status": "ok", "due": len(due), "deliveries": deliveries, "timestamp": datetime.utcnow().isoformat()}
