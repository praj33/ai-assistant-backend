"""
Reminder Scheduler Service — Day 2B Integration

Runs scheduled reminders automatically through the Universal Execution Gateway:
Safety -> Enforcement -> ExecutionService (adapter-token enforced)

This is gateway-only: it does not control devices directly; it records an audit trace
and marks reminders as delivered.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.assistant_orchestrator import generate_trace_id
from app.executors.reminder_executor import ReminderExecutor
from app.services.bucket_service import BucketService
from app.services.enforcement_service import EnforcementService
from app.services.execution_service import ExecutionService
from app.services.safety_service import SafetyService


@dataclass
class SchedulerConfig:
    poll_interval_seconds: float = 1.0
    max_batch: int = 25


class ReminderScheduler:
    def __init__(self, config: Optional[SchedulerConfig] = None):
        self.config = config or SchedulerConfig()
        self.bucket = BucketService()
        self.safety = SafetyService()
        self.enforcement = EnforcementService()
        self.gateway = ExecutionService()
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
        - validate via safety + enforcement
        - deliver via gateway
        """
        due = self.reminders.pop_due_reminders(now=datetime.utcnow())
        due = due[: self.config.max_batch]

        deliveries = []
        for reminder in due:
            reminder_id = reminder.get("reminder_id", "")
            message = reminder.get("message", "")

            trace_id = generate_trace_id()
            self.bucket.log_event(trace_id, "reminder_due", {"reminder": reminder})

            safety_result = self.safety.validate_content(content=message, trace_id=trace_id)
            self.bucket.log_event(trace_id, "safety_validation", safety_result)

            enforcement_payload = {
                "safety": safety_result,
                "intelligence": {"source": "reminder_scheduler"},
                "user_input": message,
                "intent": "reminder_delivery",
                "trace_id": trace_id,
            }
            enforcement_result = self.enforcement.enforce_policy(payload=enforcement_payload, trace_id=trace_id)
            self.bucket.log_event(trace_id, "enforcement_decision", enforcement_result)

            decision = enforcement_result.get("decision", "BLOCK")
            delivery = self.gateway.execute_action(
                action_type="reminder",
                action_data={"action": "deliver_reminder", "reminder_id": reminder_id},
                trace_id=trace_id,
                enforcement_decision=decision,
            )
            self.bucket.log_event(trace_id, "reminder_delivery", delivery)
            deliveries.append(
                {
                    "trace_id": trace_id,
                    "reminder_id": reminder_id,
                    "decision": decision,
                    "delivery": delivery,
                }
            )

        return {"status": "ok", "due": len(due), "deliveries": deliveries, "timestamp": datetime.utcnow().isoformat()}

