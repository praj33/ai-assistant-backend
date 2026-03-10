# RUNTIME DEPENDENCIES IMPLEMENTATION

Raj’s deterministic engine (`app/external/enforcement/enforcement_engine.py`) referenced several runtime modules that were missing in this codebase. Minimal implementations were added to satisfy those imports and provide production-safe behavior.

## Added modules

### `utils/deterministic_trace.py`
- Provides deterministic trace id generation via SHA-256 over a canonical JSON payload.
- Export: `generate_trace_id(input_payload, enforcement_category, salt=None)`

### `config_loader.py`
- Minimal environment-driven runtime config.
- Export: `RUNTIME_CONFIG`
  - `kill_switch` controlled by `ENFORCEMENT_KILL_SWITCH=1|true|yes`

### `logs/bucket_logger.py`
- Provides `log_enforcement(...)` used by the deterministic engine.
- Default behavior is **non-blocking** logging (stdout/logger).
- Optional bridge to existing `BucketService` if `BUCKET_LOGGER_USE_BUCKETSERVICE=1`.

## Compatibility shims

### `enforcement_verdict.py`
- Re-exports canonical `EnforcementVerdict` from `app.external.enforcement.enforcement_verdict`.

### `evaluator_modules.py`
- Minimal evaluator registry implementing `ALL_EVALUATORS` with deterministic outputs.

### `validators/akanksha/enforcement_adapter.py`
- Bridges Raj’s engine to the existing SafetyService validator.
- Returns `{decision, risk_category, confidence}`.
- Can inject failure for tests using `AKANKSHA_VALIDATOR_FAIL=1` to force fail-closed termination in the engine.

