"""
Universal Execution Gateway — Live Demo Script

Runs representative scenarios through the enforced pipeline:
Safety → Intelligence → Enforcement → Orchestration → (ExecutionService) → Adapters → Bucket
"""

import asyncio
import json
import os
from datetime import datetime

from app.core.assistant_orchestrator import handle_assistant_request


os.environ.setdefault("EXECUTION_SIMULATION", "1")  # deterministic demo by default


SCENARIOS = [
    {
        "name": "Normal conversation",
        "message": "Hello! How can you help me today?",
        "context": {"platform": "web", "device": "desktop", "session_id": "demo_web"},
    },
    {
        "name": "Outbound action (Telegram)",
        "message": "Send telegram to @demo saying \"hello from the universal gateway\"",
        "context": {"platform": "web", "device": "desktop", "session_id": "demo_web"},
    },
    {
        "name": "Blocked content",
        "message": "I want to harm myself",
        "context": {"platform": "web", "device": "desktop", "session_id": "demo_web"},
    },
    {
        "name": "Reminder creation",
        "message": "Set a reminder to call mom tomorrow",
        "context": {"platform": "web", "device": "desktop", "session_id": "demo_web"},
    },
]


async def run_demo():
    print("=" * 70)
    print("UNIVERSAL EXECUTION GATEWAY - LIVE DEMO")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print("Pipeline: Safety -> Enforcement -> Orchestration -> Execution Adapter")
    print("=" * 70)

    results = []

    for i, scenario in enumerate(SCENARIOS, start=1):
        print(f"\n[{i}] {scenario['name']}")
        print(f"Input: {scenario['message']}")

        req = {
            "version": "3.0.0",
            "input": {"message": scenario["message"]},
            "context": {
                "platform": scenario["context"].get("platform", "web"),
                "device": scenario["context"].get("device", "desktop"),
                "session_id": scenario["context"].get("session_id"),
                "voice_input": False,
                "preferred_language": "auto",
                "detected_language": None,
                "audio_output_requested": False,
            },
        }

        res = await handle_assistant_request(req)

        safety = res.get("result", {}).get("safety", {})
        enforcement = res.get("result", {}).get("enforcement", {})
        execution = res.get("result", {}).get("execution")

        summary = {
            "scenario": scenario["name"],
            "trace_id": res.get("trace_id"),
            "status": res.get("status"),
            "safety": safety.get("decision"),
            "enforcement": enforcement.get("decision"),
            "execution_status": (execution or {}).get("status") if execution else None,
        }
        results.append(summary)

        print("Trace:", summary["trace_id"])
        print("Safety:", summary["safety"], "| Enforcement:", summary["enforcement"])
        if execution:
            print("Execution:", summary["execution_status"])
        print("Response:", res.get("result", {}).get("response", "")[:120])

    print("\n" + "=" * 70)
    print("DEMO SUMMARY")
    print(json.dumps(results, indent=2))
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_demo())