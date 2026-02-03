"""
RAJ PRAJAPATI — ENFORCEMENT ENGINE
---------------------------------
Deterministic. Fail-closed. Auditable.

FINAL AUTHORITY.
Returns ONLY EnforcementVerdict.
"""

from evaluator_modules import ALL_EVALUATORS
from logs.bucket_logger import log_enforcement
from config_loader import RUNTIME_CONFIG
from utils.deterministic_trace import generate_trace_id
from validators.akanksha.enforcement_adapter import EnforcementAdapter

from enforcement_verdict import EnforcementVerdict

# STRICT PRIORITY — DO NOT CHANGE
DECISION_PRIORITY = ["BLOCK", "REWRITE", "EXECUTE"]


def _canonical_trace_payload(input_payload) -> dict:
    """
    SINGLE SOURCE OF TRUTH for trace hashing & replay.
    MUST be identical during live run and replay.
    """
    return {
        "intent": input_payload.intent,
        "emotional_output": input_payload.emotional_output,
        "age_gate_status": input_payload.age_gate_status,
        "region_policy": input_payload.region_policy,
        "platform_policy": input_payload.platform_policy,
        "karma_score": input_payload.karma_score,
        "risk_flags": input_payload.risk_flags,
    }


def enforce(input_payload) -> EnforcementVerdict:
    """
    Sole enforcement entrypoint.
    ALWAYS returns EnforcementVerdict.
    """

    # -------------------------------------------------
    # STEP 0 — CANONICAL INPUT SNAPSHOT (LOCKED)
    # -------------------------------------------------
    trace_payload = _canonical_trace_payload(input_payload)

    # -------------------------------------------------
    # STEP 1 — GLOBAL KILL SWITCH (ABSOLUTE)
    # -------------------------------------------------
    if RUNTIME_CONFIG.get("kill_switch") is True:
        trace_id = generate_trace_id(
            input_payload=trace_payload,
            enforcement_category="TERMINATE",
        )

        verdict = EnforcementVerdict(
            decision="TERMINATE",
            scope="both",
            trace_id=trace_id,
            reason_code="GLOBAL_KILL_SWITCH",
        )

        log_enforcement(
            trace_id=trace_id,
            input_snapshot=trace_payload,
            akanksha_verdict=None,
            evaluator_results=[],
            final_decision=verdict.decision,
        )
        return verdict

    # -------------------------------------------------
    # STEP 2 — RUN RAJ EVALUATORS
    # -------------------------------------------------
    evaluator_results = [e.evaluate(input_payload) for e in ALL_EVALUATORS]
    raj_decision = _resolve_raj_decision(evaluator_results)

    # -------------------------------------------------
    # STEP 3 — RUN AKANKSHA (MANDATORY, FAIL-CLOSED)
    # -------------------------------------------------
    try:
        adapter = EnforcementAdapter()
        akanksha_result = adapter.validate(input_payload)
        ak_decision = akanksha_result["decision"]
    except Exception:
        trace_id = generate_trace_id(
            input_payload=trace_payload,
            enforcement_category="TERMINATE",
        )

        verdict = EnforcementVerdict(
            decision="TERMINATE",
            scope="both",
            trace_id=trace_id,
            reason_code="AKANKSHA_VALIDATION_FAILED",
        )

        log_enforcement(
            trace_id=trace_id,
            input_snapshot=trace_payload,
            akanksha_verdict=None,
            evaluator_results=evaluator_results,
            final_decision=verdict.decision,
        )
        return verdict

    # -------------------------------------------------
    # STEP 4 — FINAL DECISION RESOLUTION
    # -------------------------------------------------
    final_decision = _resolve_final_decision(
        raj_decision=raj_decision,
        ak_decision=ak_decision,
    )

    # -------------------------------------------------
    # STEP 5 — TRACE ID (BEFORE VERDICT — IMMUTABLE)
    # -------------------------------------------------
    public_decision = (
        "ALLOW" if final_decision == "EXECUTE" else final_decision
    )

    trace_id = generate_trace_id(
        input_payload=trace_payload,
        enforcement_category=public_decision,
    )

    # -------------------------------------------------
    # STEP 6 — CONSTRUCT FINAL VERDICT (NO MUTATION)
    # -------------------------------------------------
    if final_decision == "EXECUTE":
        verdict = EnforcementVerdict(
            decision="ALLOW",
            scope="both",
            trace_id=trace_id,
            reason_code="CONTENT_AND_ACTION_ALLOWED",
        )

    elif final_decision == "REWRITE":
        verdict = EnforcementVerdict(
            decision="REWRITE",
            scope="response",
            trace_id=trace_id,
            reason_code="SAFE_REWRITE_REQUIRED",
            rewrite_class="DETERMINISTIC_REWRITE",
        )

    elif final_decision == "BLOCK":
        verdict = EnforcementVerdict(
            decision="BLOCK",
            scope="both",
            trace_id=trace_id,
            reason_code="POLICY_VIOLATION",
        )

    else:  # TERMINATE
        verdict = EnforcementVerdict(
            decision="TERMINATE",
            scope="both",
            trace_id=trace_id,
            reason_code="SYSTEM_TERMINATION",
        )

    # -------------------------------------------------
    # STEP 7 — AUDIT LOG (REPLAYABLE)
    # -------------------------------------------------
    log_enforcement(
        trace_id=trace_id,
        input_snapshot=trace_payload,
        akanksha_verdict={
            "decision": ak_decision,
            "risk_category": akanksha_result.get("risk_category"),
            "confidence": akanksha_result.get("confidence"),
        },
        evaluator_results=evaluator_results,
        final_decision=verdict.decision,
    )

    # -------------------------------------------------
    # STEP 8 — RETURN FINAL VERDICT
    # -------------------------------------------------
    return verdict


# -------------------------------------------------
# INTERNAL HELPERS
# -------------------------------------------------

def _resolve_raj_decision(evaluator_results):
    for decision in DECISION_PRIORITY:
        for result in evaluator_results:
            if result.action == decision:
                return decision
    return "EXECUTE"


def _resolve_final_decision(*, raj_decision: str, ak_decision: str) -> str:
    for decision in DECISION_PRIORITY:
        if decision == raj_decision or decision == ak_decision:
            return decision
    return "EXECUTE"
