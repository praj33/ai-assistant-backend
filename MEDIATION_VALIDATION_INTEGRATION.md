# MEDIATION VALIDATION INTEGRATION (AKANKSHA)

## Integration point
Raj’s deterministic engine calls:
- `validators.akanksha.enforcement_adapter.EnforcementAdapter.validate(input_payload)`

## Adapter behavior
The adapter bridges to the runtime Safety layer:
- Calls `app/services/safety_service.py` (behavior validator)
- Maps safety decisions to enforcement adapter decisions:
  - `hard_deny` → `BLOCK`
  - `soft_rewrite` → `REWRITE`
  - `allow` → `EXECUTE`

## Fail-closed guarantee
If the adapter throws for any reason, Raj’s engine returns:
- `decision = TERMINATE`
- `reason_code = AKANKSHA_VALIDATION_FAILED`

## Output contract
Adapter returns:
- `decision`
- `risk_category`
- `confidence`

