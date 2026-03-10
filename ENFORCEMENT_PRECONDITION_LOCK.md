# Enforcement Precondition Lock

Validated on March 10, 2026 with:

```bash
python test_enforcement_runtime_activation.py
```

## Runtime lock

Enforcement now blocks before Raj evaluator resolution unless all mediation preconditions exist:

- request `trace_id`
- mediation `safety.decision`
- mediation `safety.trace_id`
- mediation bucket artifact for stage `safety_validation` when Bucket is enabled

Implemented in:

- `app/external/enforcement/enforcement_engine.py`
- `app/services/enforcement_service.py`
- `app/services/bucket_service.py`

## Verified outcomes

| Check | Decision | Reason code |
| --- | --- | --- |
| missing_mediation_blocks | BLOCK | `MISSING_MEDIATION` |
| missing_trace_blocks | BLOCK | `MISSING_MEDIATION` |
| trace_mismatch_blocks | BLOCK | `TRACE_MISMATCH` |
| missing_bucket_artifact_blocks | BLOCK | `MISSING_BUCKET_ARTIFACT` |

## Trace evidence

- Unmediated payloads never reach normal Raj decision resolution.
- Missing request trace ids are rejected fail-closed.
- Safety trace and runtime trace must match exactly.
- If Bucket enforcement is active and no mediation artifact exists for the trace, enforcement blocks the request.

Result: unmediated payloads are now non-executable by construction.
