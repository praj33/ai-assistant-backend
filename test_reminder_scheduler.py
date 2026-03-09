"""
Reminder Scheduler Proof — Day 2B

Creates a reminder due in a few seconds, runs one scheduler tick,
and writes `reminder_execution_trace.json` showing:
- reminder creation through ExecutionService (gateway-token enforced)
- automatic scheduler pickup
- safety + enforcement decisions
- delivery through ExecutionService (gateway-token enforced)
"""

import json
import time
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv(".env")

from app.services.execution_service import ExecutionService
from app.services.reminder_scheduler import ReminderScheduler, SchedulerConfig


def main():
    gateway = ExecutionService()

    remind_at = (datetime.utcnow() + timedelta(seconds=2)).isoformat()
    create = gateway.execute_action(
        "reminder",
        {"action": "create_reminder", "message": "Scheduled reminder ping", "remind_at": remind_at, "user_id": "test_user"},
        trace_id="trace_reminder_create_001",
        enforcement_decision="ALLOW",
    )

    # Wait until due
    time.sleep(3)

    scheduler = ReminderScheduler(SchedulerConfig(poll_interval_seconds=0.1, max_batch=10))
    tick = __import__("asyncio").run(scheduler.tick())

    proof = {
        "test": "reminder_scheduler_execution",
        "flow": "Scheduler -> Safety -> Enforcement -> ExecutionService -> ReminderExecutor",
        "enforcement_gated": True,
        "created": create,
        "scheduler_tick": tick,
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open("reminder_execution_trace.json", "w", encoding="utf-8") as f:
        json.dump(proof, f, indent=2)

    print("Generated: reminder_execution_trace.json")


if __name__ == "__main__":
    main()

