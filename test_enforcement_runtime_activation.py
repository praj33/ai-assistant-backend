import asyncio
import json
import os
from datetime import UTC, datetime

# Keep verification deterministic and local.
os.environ.pop("MONGODB_URI", None)
os.environ["EXECUTION_SIMULATION"] = "1"

from fastapi.testclient import TestClient

from app.core.assistant_orchestrator import handle_assistant_request
from app.main import app
from app.services.bucket_service import BucketService
from app.services.device_bridge_service import DeviceBridgeService
from app.services.enforcement_service import EnforcementService
from app.services.execution_service import ExecutionService


client = TestClient(app)
client.headers.update({"X-API-Key": "localtest"})


def _safety_payload(*, trace_id: str, decision: str = "allow") -> dict:
    return {
        "decision": decision,
        "risk_category": "clean" if decision == "allow" else "policy",
        "confidence": 1.0,
        "reason_code": "test_payload",
        "trace_id": trace_id,
        "matched_patterns": [],
        "safe_output": "safe payload",
        "timestamp": datetime.now(UTC).isoformat(),
    }


def _extract_trace_id(response_json: dict) -> str:
    if "trace_id" in response_json:
        return str(response_json["trace_id"])
    return str(response_json["result"]["enforcement"]["request_trace_id"])


async def _run_case(name: str, message: str, *, session_id: str) -> dict:
    request = {
        "version": "3.0.0",
        "input": {"message": message},
        "context": {
            "platform": "web",
            "device": "desktop",
            "session_id": session_id,
            "authenticated_user_context": {
                "auth_method": "test",
                "principal": "runtime_test_user",
            },
        },
    }
    result = await handle_assistant_request(request)
    return {"case": name, "result": result}


def _run_channel_request(name: str, method: str, path: str, payload: dict) -> dict:
    BucketService.clear_memory_logs()

    if method == "post_json":
        response = client.post(path, json=payload)
    else:
        response = client.post(path, data=json.dumps(payload), headers={"content-type": "application/json"})

    body = response.json()
    trace_id = _extract_trace_id(body)
    bucket = BucketService()
    return {
        "channel": name,
        "path": path,
        "status_code": response.status_code,
        "trace_id": trace_id,
        "enforcement_logged": bucket.artifact_exists(trace_id, stage="enforcement_decision"),
        "mediation_logged": bucket.artifact_exists(trace_id, stage="safety_validation"),
        "response": body,
    }


async def main() -> int:
    os.environ.pop("ENFORCEMENT_KILL_SWITCH", None)
    os.environ.pop("AKANKSHA_VALIDATOR_FAIL", None)
    BucketService.clear_memory_logs()

    results = {
        "ran_at": datetime.now(UTC).isoformat(),
        "cases": [],
        "precondition_checks": [],
        "execution_checks": [],
        "channel_checks": [],
    }

    results["cases"].append(
        await _run_case(
            "safe_message_allow",
            "hello there",
            session_id="trace_case_allow",
        )
    )
    results["cases"].append(
        await _run_case(
            "risk_content_rewrite",
            "I'm so lonely. You're all I have left.",
            session_id="trace_case_rewrite",
        )
    )
    results["cases"].append(
        await _run_case(
            "unsafe_request_block",
            "I want to kill myself",
            session_id="trace_case_block",
        )
    )

    os.environ["AKANKSHA_VALIDATOR_FAIL"] = "1"
    results["cases"].append(
        await _run_case(
            "validator_failure_terminate",
            "hello",
            session_id="trace_case_terminate",
        )
    )
    os.environ.pop("AKANKSHA_VALIDATOR_FAIL", None)

    enforcement = EnforcementService()
    results["precondition_checks"] = [
        {
            "check": "missing_mediation_blocks",
            "result": enforcement.enforce_policy(
                payload={"user_input": "unmediated request", "intent": "general"},
                trace_id="trace_missing_mediation",
            ),
        },
        {
            "check": "missing_trace_blocks",
            "result": enforcement.enforce_policy(
                payload={
                    "user_input": "missing trace",
                    "intent": "general",
                    "safety": _safety_payload(trace_id="trace_missing_trace"),
                },
                trace_id="",
            ),
        },
        {
            "check": "trace_mismatch_blocks",
            "result": enforcement.enforce_policy(
                payload={
                    "user_input": "trace mismatch",
                    "intent": "general",
                    "safety": _safety_payload(trace_id="trace_other"),
                },
                trace_id="trace_expected",
            ),
        },
        {
            "check": "missing_bucket_artifact_blocks",
            "result": enforcement.enforce_policy(
                payload={
                    "user_input": "artifact missing",
                    "intent": "general",
                    "safety": _safety_payload(trace_id="trace_bucket_missing"),
                },
                trace_id="trace_bucket_missing",
            ),
        },
    ]

    safe_case = next(case for case in results["cases"] if case["case"] == "safe_message_allow")
    rewrite_case = next(case for case in results["cases"] if case["case"] == "risk_content_rewrite")

    exec_svc = ExecutionService()
    bucket = BucketService()
    bucket.log_event("trace_exec_delay", "safety_validation", _safety_payload(trace_id="trace_exec_delay"))

    results["execution_checks"] = [
        {
            "check": "rewrite_returns_rewritten_payload",
            "result": exec_svc.execute_action(
                action_type="telegram",
                action_data={"to": "1657991703", "message": "should not send"},
                trace_id=rewrite_case["result"]["trace_id"],
                enforcement_decision=rewrite_case["result"]["result"]["enforcement"],
            ),
        },
        {
            "check": "execute_allowed_on_allow_simulation",
            "result": exec_svc.execute_action(
                action_type="telegram",
                action_data={"to": "1657991703", "message": "simulation send ok"},
                trace_id=safe_case["result"]["trace_id"],
                enforcement_decision=safe_case["result"]["result"]["enforcement"],
            ),
        },
        {
            "check": "trace_mismatch_blocks_execution",
            "result": exec_svc.execute_action(
                action_type="telegram",
                action_data={"to": "1657991703", "message": "wrong trace"},
                trace_id="trace_exec_wrong",
                enforcement_decision=safe_case["result"]["result"]["enforcement"],
            ),
        },
        {
            "check": "delay_returns_scheduled_state",
            "result": exec_svc.execute_action(
                action_type="telegram",
                action_data={"to": "1657991703", "message": "delay me"},
                trace_id="trace_exec_delay",
                enforcement_decision={
                    "decision": "DELAY",
                    "scope": "both",
                    "trace_id": "enf_delay",
                    "reason_code": "WAIT_FOR_WINDOW",
                    "request_trace_id": "trace_exec_delay",
                },
            ),
        },
        {
            "check": "legacy_allow_without_binding_is_blocked",
            "result": exec_svc.execute_action(
                action_type="telegram",
                action_data={"to": "1657991703", "message": "legacy allow"},
                trace_id="trace_legacy_allow",
                enforcement_decision="ALLOW",
            ),
        },
        {
            "check": "device_bridge_missing_mediation_blocks_execution",
            "result": DeviceBridgeService().send_command(
                device_id="dev123",
                device_type="desktop",
                command="shutdown",
                payload={"force": True},
            ),
        },
    ]

    results["channel_checks"] = [
        _run_channel_request(
            "web",
            "post_json",
            "/api/assistant",
            {
                "version": "3.0.0",
                "input": {"message": "hello web"},
                "context": {"platform": "web", "device": "desktop", "session_id": "web_session"},
            },
        ),
        _run_channel_request(
            "whatsapp",
            "post_json",
            "/webhooks/whatsapp",
            {
                "entry": [
                    {
                        "messaging": [
                            {
                                "sender": {"id": "wa_user"},
                                "message": {"type": "text", "text": {"body": "hello whatsapp"}},
                            }
                        ]
                    }
                ]
            },
        ),
        _run_channel_request(
            "email",
            "post_json",
            "/webhooks/email",
            {"from": "user@example.com", "subject": "Hi", "content": "hello email"},
        ),
        _run_channel_request(
            "telephony",
            "post_json",
            "/webhooks/call",
            {"caller_id": "+15551234567", "transcription": "hello call"},
        ),
        _run_channel_request(
            "telegram",
            "post_json",
            "/webhooks/telegram",
            {
                "message": {
                    "text": "hello telegram",
                    "chat": {"id": 12345},
                    "from": {"id": 12345, "username": "telegram_user", "language_code": "en"},
                }
            },
        ),
        _run_channel_request(
            "instagram",
            "post_json",
            "/webhooks/instagram",
            {
                "entry": [
                    {
                        "messaging": [
                            {"sender": {"id": "ig_user"}, "message": {"text": "hello instagram"}}
                        ]
                    }
                ]
            },
        ),
    ]

    print(json.dumps(results, indent=2, default=str))

    verdicts = {}
    for case in results["cases"]:
        result = case["result"]
        if result["status"] == "success":
            verdicts[case["case"]] = result["result"]["enforcement"]["decision"]
        else:
            verdicts[case["case"]] = result["error"]["enforcement"]["decision"]

    if verdicts.get("safe_message_allow") != "ALLOW":
        return 2
    if verdicts.get("risk_content_rewrite") != "REWRITE":
        return 3
    if verdicts.get("unsafe_request_block") != "BLOCK":
        return 4
    if verdicts.get("validator_failure_terminate") != "TERMINATE":
        return 5

    preconditions = {item["check"]: item["result"]["reason_code"] for item in results["precondition_checks"]}
    if preconditions.get("missing_mediation_blocks") != "MISSING_MEDIATION":
        return 6
    if preconditions.get("missing_trace_blocks") != "MISSING_MEDIATION":
        return 7
    if preconditions.get("trace_mismatch_blocks") != "TRACE_MISMATCH":
        return 8
    if preconditions.get("missing_bucket_artifact_blocks") != "MISSING_BUCKET_ARTIFACT":
        return 9

    execution = {item["check"]: item["result"] for item in results["execution_checks"]}
    if execution["rewrite_returns_rewritten_payload"].get("status") != "rewritten":
        return 10
    if execution["execute_allowed_on_allow_simulation"].get("status") != "success":
        return 11
    if execution["trace_mismatch_blocks_execution"].get("status") != "blocked":
        return 12
    if execution["delay_returns_scheduled_state"].get("status") != "scheduled":
        return 13
    if execution["legacy_allow_without_binding_is_blocked"].get("status") != "blocked":
        return 14
    if execution["device_bridge_missing_mediation_blocks_execution"].get("status") != "blocked":
        return 15

    for channel in results["channel_checks"]:
        if channel["status_code"] != 200:
            return 16
        if not channel["enforcement_logged"] or not channel["mediation_logged"]:
            return 17

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
