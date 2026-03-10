"""
RAJ PRAJAPATI — ENFORCEMENT ENGINE
---------------------------------
Deterministic. Fail-closed. Auditable.

FINAL AUTHORITY.
Returns ONLY EnforcementVerdict.
"""

from evaluator_modules import ALL_EVALUATORS
from validators.akanksha.enforcement_adapter import EnforcementAdapter

from .bucket_logger import log_enforcement
from .config_loader import RUNTIME_CONFIG
from .deterministic_trace import generate_trace_id
from .enforcement_verdict import EnforcementVerdict

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


def _precondition_block(trace_payload: dict, *, request_trace_id: str | None, reason_code: str) -> EnforcementVerdict:
    trace_id = generate_trace_id(
        input_payload=trace_payload,
        enforcement_category="BLOCK",
    )
    return EnforcementVerdict(
        decision="BLOCK",
        scope="both",
        trace_id=trace_id,
        reason_code=reason_code,
        request_trace_id=request_trace_id,
    )


def _extract_mediation_decision(input_payload) -> str | None:
    decision = getattr(input_payload, "mediation_decision", None)
    if decision:
        return str(decision)

    validation = getattr(input_payload, "akanksha_validation", None)
    if isinstance(validation, dict):
        raw = validation.get("decision")
        if raw:
            return str(raw)

    return None


def _extract_mediation_trace_id(input_payload) -> str | None:
    trace_id = getattr(input_payload, "mediation_trace_id", None)
    if trace_id:
        return str(trace_id)

    validation = getattr(input_payload, "akanksha_validation", None)
    if isinstance(validation, dict):
        raw = validation.get("trace_id")
        if raw:
            return str(raw)

    return None


def enforce(input_payload) -> EnforcementVerdict:
    """
    Sole enforcement entrypoint.
    ALWAYS returns EnforcementVerdict.
    """

    # -------------------------------------------------
    # STEP 0 — CANONICAL INPUT SNAPSHOT (LOCKED)
    # -------------------------------------------------
    trace_payload = _canonical_trace_payload(input_payload)
    request_trace_id = getattr(input_payload, "trace_id", None)
    mediation_decision = _extract_mediation_decision(input_payload)
    mediation_trace_id = _extract_mediation_trace_id(input_payload)

    if not request_trace_id or not mediation_decision or not mediation_trace_id:
        verdict = _precondition_block(
            trace_payload,
            request_trace_id=str(request_trace_id) if request_trace_id else None,
            reason_code="MISSING_MEDIATION",
        )
        log_enforcement(
            trace_id=verdict.trace_id,
            input_snapshot=trace_payload,
            akanksha_verdict={
                "decision": mediation_decision,
                "trace_id": mediation_trace_id,
            },
            evaluator_results=[],
            final_decision=verdict.decision,
        )
        return verdict

    request_trace_id = str(request_trace_id)
    mediation_trace_id = str(mediation_trace_id)

    if request_trace_id != mediation_trace_id:
        verdict = _precondition_block(
            trace_payload,
            request_trace_id=request_trace_id,
            reason_code="TRACE_MISMATCH",
        )
        log_enforcement(
            trace_id=verdict.trace_id,
            input_snapshot=trace_payload,
            akanksha_verdict={
                "decision": mediation_decision,
                "trace_id": mediation_trace_id,
            },
            evaluator_results=[],
            final_decision=verdict.decision,
        )
        return verdict

    if getattr(input_payload, "bucket_active", False) and not getattr(
        input_payload,
        "mediation_artifact_present",
        False,
    ):
        verdict = _precondition_block(
            trace_payload,
            request_trace_id=request_trace_id,
            reason_code="MISSING_BUCKET_ARTIFACT",
        )
        log_enforcement(
            trace_id=verdict.trace_id,
            input_snapshot=trace_payload,
            akanksha_verdict={
                "decision": mediation_decision,
                "trace_id": mediation_trace_id,
            },
            evaluator_results=[],
            final_decision=verdict.decision,
        )
        return verdict

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
            request_trace_id=request_trace_id,
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
            request_trace_id=request_trace_id,
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
            request_trace_id=request_trace_id,
        )

    elif final_decision == "REWRITE":
        verdict = EnforcementVerdict(
            decision="REWRITE",
            scope="response",
            trace_id=trace_id,
            reason_code="SAFE_REWRITE_REQUIRED",
            request_trace_id=request_trace_id,
            rewrite_class="DETERMINISTIC_REWRITE",
            safe_output=akanksha_result.get("safe_output"),
        )

    elif final_decision == "BLOCK":
        verdict = EnforcementVerdict(
            decision="BLOCK",
            scope="both",
            trace_id=trace_id,
            reason_code="POLICY_VIOLATION",
            request_trace_id=request_trace_id,
        )

    else:  # TERMINATE
        verdict = EnforcementVerdict(
            decision="TERMINATE",
            scope="both",
            trace_id=trace_id,
            reason_code="SYSTEM_TERMINATION",
            request_trace_id=request_trace_id,
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
