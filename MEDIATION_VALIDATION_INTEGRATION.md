# MEDIATION VALIDATION INTEGRATION

## Integration point
Raj's deterministic engine calls:

- `validators.akanksha.enforcement_adapter.EnforcementAdapter.validate(input_payload)`

## Adapter behavior
The adapter bridges to the runtime safety layer and supports both runtime modes:

- uses the already-produced safety result when `akanksha_validation` is present on the enforcement payload
- otherwise calls `app/services/safety_service.py`

## Decision mapping
- `hard_deny` -> `BLOCK`
- `soft_rewrite` -> `REWRITE`
- `allow` -> `EXECUTE`

## Output contract
The adapter returns:

- `decision`
- `risk_category`
- `confidence`

It also forwards `safe_output` when available so the rewrite response can stay deterministic.

## Fail-closed guarantee
If the adapter throws for any reason, Raj's engine returns:

- `decision = TERMINATE`
- `reason_code = AKANKSHA_VALIDATION_FAILED`
