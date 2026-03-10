# ENFORCEMENT SERVICE RUNTIME

## Runtime authority
`app/services/enforcement_service.py` now uses **only**:

- `app/external/enforcement/enforcement_engine.py`

## Wiring details
- The service builds an attribute-based `input_payload` object (via `SimpleNamespace`) with the fields required by Raj’s engine:
  - `intent`
  - `emotional_output`
  - `age_gate_status`
  - `region_policy`
  - `platform_policy`
  - `karma_score`
  - `risk_flags`
  - `trace_id` (runtime trace for continuity)

## Verdict adaptation
Raj’s `EnforcementVerdict` is converted into the dict shape expected by the orchestrator:
- `decision`
- `scope`
- `reason_code`
- `trace_id` (deterministic enforcement-owned trace id from Raj’s engine)
- `timestamp`
- optional: `rewrite_class`, `safe_output`

