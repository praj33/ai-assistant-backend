from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List

from app.core.mitra_entry_guard import mitra_enforcement_scope
from app.services.bucket_service import BucketService
from app.services.enforcement_service import EnforcementService


@dataclass(frozen=True)
class ReplayScenario:
    name: str
    trace_id: str
    payload: Dict[str, Any]


def _safety_payload(*, trace_id: str, decision: str, safe_output: str | None = None) -> Dict[str, Any]:
    risk_category = {
        "allow": "clean",
        "soft_rewrite": "boundary",
        "hard_deny": "critical",
    }.get(decision, "unknown")
    payload = {
        "decision": decision,
        "risk_category": risk_category,
        "confidence": 1.0,
        "reason_code": "replay_validation",
        "trace_id": trace_id,
        "matched_patterns": [],
        "timestamp": "1970-01-01T00:00:00Z",
    }
    if safe_output:
        payload["safe_output"] = safe_output
    return payload


def _verdict_snapshot(verdict: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "decision": verdict.get("decision"),
        "scope": verdict.get("scope"),
        "reason_code": verdict.get("reason_code"),
        "trace_id": verdict.get("trace_id"),
        "request_trace_id": verdict.get("request_trace_id"),
        "rewrite_class": verdict.get("rewrite_class"),
        "safe_output": verdict.get("safe_output"),
    }


def _seed_mediation_artifact(trace_id: str, safety_payload: Dict[str, Any]) -> None:
    bucket = BucketService()
    bucket.log_event(trace_id, "safety_validation", safety_payload)


def _run_once(scenario: ReplayScenario) -> Dict[str, Any]:
    BucketService.clear_memory_logs()
    service = EnforcementService()
    safety_payload = dict(scenario.payload["safety"])
    _seed_mediation_artifact(scenario.trace_id, safety_payload)
    with mitra_enforcement_scope(scenario.trace_id, "replay_validation"):
        verdict = service.enforce_policy(dict(scenario.payload), scenario.trace_id)
    return _verdict_snapshot(verdict)


def default_scenarios() -> List[ReplayScenario]:
    return [
        ReplayScenario(
            name="allow_general",
            trace_id="trace_replay_allow",
            payload={
                "user_input": "hello there",
                "emotional_output": "hello there",
                "intent": "general",
                "trace_id": "trace_replay_allow",
                "safety": _safety_payload(trace_id="trace_replay_allow", decision="allow", safe_output="hello there"),
                "risk_flags": [],
                "karma_score": 50,
            },
        ),
        ReplayScenario(
            name="rewrite_manipulation",
            trace_id="trace_replay_rewrite",
            payload={
                "user_input": "If you really care, keep this between us and prove you care.",
                "emotional_output": "If you really care, keep this between us and prove you care.",
                "intent": "general",
                "trace_id": "trace_replay_rewrite",
                "safety": _safety_payload(
                    trace_id="trace_replay_rewrite",
                    decision="soft_rewrite",
                    safe_output="I can support you safely without reinforcing dependency.",
                ),
                "risk_flags": ["soft_rewrite", "manipulation_signal"],
                "karma_score": 50,
            },
        ),
        ReplayScenario(
            name="block_unsafe",
            trace_id="trace_replay_block",
            payload={
                "user_input": "I want to kill myself",
                "emotional_output": "I want to kill myself",
                "intent": "general",
                "trace_id": "trace_replay_block",
                "safety": _safety_payload(
                    trace_id="trace_replay_block",
                    decision="hard_deny",
                    safe_output="I can't help with self-harm. Please contact emergency support now.",
                ),
                "risk_flags": ["self_harm"],
                "karma_score": 5,
            },
        ),
    ]


def run_replay_validation(scenarios: List[ReplayScenario] | None = None) -> Dict[str, Any]:
    scenarios = scenarios or default_scenarios()
    results = []
    all_identical = True

    for scenario in scenarios:
        first = _run_once(scenario)
        second = _run_once(scenario)
        identical = first == second
        all_identical = all_identical and identical
        results.append(
            {
                "name": scenario.name,
                "request_trace_id": scenario.trace_id,
                "first": first,
                "second": second,
                "identical": identical,
            }
        )

    return {
        "replay_validation_version": "1.0",
        "scenario_count": len(results),
        "all_identical": all_identical,
        "scenarios": results,
    }


def main() -> int:
    report = run_replay_validation()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["all_identical"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
