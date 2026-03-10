# EXECUTION → ENFORCEMENT GATE

## Requirement
No real-world action may execute unless enforcement verdict is **ALLOW**.

## Implementation
`app/services/execution_service.py` now enforces:
- `enforcement_decision` must be exactly `ALLOW`
- Otherwise returns `{"status": "blocked", ...}`

This ensures:
- `REWRITE` affects responses only (no action execution)
- `BLOCK` and `TERMINATE` fail closed

