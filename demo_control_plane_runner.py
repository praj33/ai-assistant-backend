from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi.testclient import TestClient


os.environ.setdefault("API_KEY", "localtest")

from app.main import app
from app.services.bucket_service import BucketService
from app.services.enforcement_service import EnforcementService


ROOT = Path(__file__).resolve().parent
STAMP = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = ROOT / "demo_artifacts" / STAMP

client = TestClient(app)
client.headers.update({"X-API-Key": os.getenv("API_KEY", "localtest")})


def _write_json(name: str, payload: Dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _mitra_post(payload: Dict[str, Any]) -> Dict[str, Any]:
    response = client.post("/api/mitra/evaluate", json=payload)
    return {
        "http_status": response.status_code,
        "input": payload,
        "output": response.json(),
    }


def _telephony_post(payload: Dict[str, Any]) -> Dict[str, Any]:
    response = client.post("/webhook/telephony", json=payload)
    body = response.json()
    trace_id = body.get("trace_id")
    return {
        "http_status": response.status_code,
        "input": payload,
        "output": body,
        "mitra_request_log": BucketService().get_artifact(trace_id, stage="mitra_request_log") if trace_id else None,
    }


def _bypass_proof() -> Dict[str, Any]:
    BucketService.clear_memory_logs()
    trace_id = "trace_demo_direct_bypass"
    safety = {
        "decision": "allow",
        "risk_category": "clean",
        "confidence": 1.0,
        "reason_code": "demo_runner",
        "trace_id": trace_id,
        "matched_patterns": [],
        "timestamp": "1970-01-01T00:00:00Z",
    }
    BucketService().log_event(trace_id, "safety_validation", safety)

    payload = {
        "user_input": "hello",
        "emotional_output": "hello",
        "intent": "general",
        "trace_id": trace_id,
        "safety": safety,
        "risk_flags": [],
        "karma_score": 50,
        "platform_policy": {"platform": "web", "device": "desktop"},
        "authenticated_user_context": {
            "session_id": trace_id,
            "platform": "web",
            "device": "desktop",
        },
    }

    try:
        EnforcementService().enforce_policy(payload, trace_id)
        return {"blocked": False, "trace_id": trace_id}
    except Exception as exc:
        return {
            "blocked": True,
            "trace_id": trace_id,
            "error": type(exc).__name__,
            "message": str(exc),
            "bucket_log": BucketService().get_artifact(trace_id, stage="enforcement_bypass_blocked"),
        }


def main() -> int:
    print(f"Writing demo artifacts to: {OUTPUT_DIR}")

    BucketService.clear_memory_logs()
    clean = _mitra_post(
        {
            "user_id": "demo_clean_user",
            "context": {"platform": "samachar", "device": "api", "session_id": "demo_clean_session"},
            "event": {
                "title": "Weather update",
                "content": "Tomorrow will be sunny with light winds.",
                "category": "weather",
                "confidence": 0.93,
            },
        }
    )
    _write_json("01_clean_allow.json", clean)

    BucketService.clear_memory_logs()
    flag = _mitra_post(
        {
            "user_id": "demo_flag_user",
            "context": {"platform": "samachar", "device": "api", "session_id": "demo_flag_session"},
            "event": {
                "title": "Emotional dependency signal",
                "content": "You're the only one who gets me. Don't ever leave me.",
                "category": "conversation",
                "confidence": 0.91,
            },
        }
    )
    _write_json("02_flag_rewrite.json", flag)

    BucketService.clear_memory_logs()
    block = _mitra_post(
        {
            "user_id": "demo_block_user",
            "context": {"platform": "samachar", "device": "api", "session_id": "demo_block_session"},
            "event": {
                "title": "Explicit request",
                "content": "I want nude photo.",
                "category": "content_request",
                "confidence": 0.98,
            },
        }
    )
    _write_json("03_block_harmful.json", block)

    BucketService.clear_memory_logs()
    _mitra_post(
        {
            "user_id": "demo_signal_user",
            "context": {"platform": "samachar", "device": "api", "session_id": "demo_signal_session"},
            "event": {
                "title": "Outbound action",
                "content": "Send the school update on WhatsApp.",
                "category": "messaging",
                "confidence": 0.92,
            },
        }
    )
    correction = _mitra_post(
        {
            "user_id": "demo_signal_user",
            "context": {"platform": "samachar", "device": "api", "session_id": "demo_signal_session"},
            "event": {
                "title": "Outbound action correction",
                "content": "Actually, send the school update by email instead.",
                "category": "messaging",
                "confidence": 0.92,
            },
        }
    )
    _write_json("04_correction_signal.json", correction)

    BucketService.clear_memory_logs()
    _mitra_post(
        {
            "user_id": "demo_refine_user",
            "context": {"platform": "samachar", "device": "api", "session_id": "demo_refine_session"},
            "event": {
                "title": "Weather brief",
                "content": "Share the school weather update.",
                "category": "weather",
                "confidence": 0.92,
            },
        }
    )
    refinement = _mitra_post(
        {
            "user_id": "demo_refine_user",
            "context": {"platform": "samachar", "device": "api", "session_id": "demo_refine_session"},
            "event": {
                "title": "Weather brief refinement",
                "content": "Let me rephrase: share the same school weather update for tomorrow morning only.",
                "category": "weather",
                "confidence": 0.92,
            },
        }
    )
    _write_json("05_refinement_signal.json", refinement)

    BucketService.clear_memory_logs()
    voice = _telephony_post(
        {
            "caller_id": "demo_voice_user",
            "transcription": "Please remind me to call the school tomorrow morning.",
        }
    )
    _write_json("06_voice_telephony.json", voice)

    bypass = _bypass_proof()
    _write_json("07_bypass_block.json", bypass)

    summary = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "artifacts_dir": str(OUTPUT_DIR),
        "cases": {
            "clean": clean["output"],
            "flag": flag["output"],
            "block": block["output"],
            "correction": correction["output"],
            "refinement": refinement["output"],
            "voice": voice["output"],
            "bypass": bypass,
        },
    }
    _write_json("00_summary.json", summary)

    print()
    print("Demo summary")
    for name, payload in summary["cases"].items():
        if name == "bypass":
            print(f"- {name}: blocked={payload['blocked']} trace_id={payload['trace_id']}")
            continue
        print(
            f"- {name}: status={payload.get('status', payload.get('status'))} "
            f"trace_id={payload.get('trace_id')} signal_type={payload.get('signal_type')}"
        )

    print()
    print("Ready for demo recording.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
