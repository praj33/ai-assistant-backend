# ENFORCEMENT SERVICE RUNTIME

## Runtime authority
`app/services/enforcement_service.py` now uses only:

- `app/external/enforcement/enforcement_engine.py`

## Wiring details
The service builds the attribute-based `input_payload` required by Raj's engine with:

- `intent`
- `emotional_output`
- `age_gate_status`
- `region_policy`
- `platform_policy`
- `karma_score`
- `risk_flags`
- `trace_id`
- `akanksha_validation` when the runtime safety layer already validated the request
- authenticated user context merged into platform policy for enforcement consumption

## Verdict adaptation
Raj's `EnforcementVerdict` is converted into the dict shape consumed by orchestration:

- `decision`
- `scope`
- `reason_code`
- `trace_id`
- `timestamp`
- optional: `rewrite_class`
- optional: `safe_output`
- optional: `rewritten_output`

## Runtime behavior
- the service calls `enforcement_engine.enforce(...)` directly
- the orchestrator receives Raj-owned deterministic trace ids
- rewrite-safe output is propagated back to the response layer
- authenticated user context is available to enforcement through the runtime payload
