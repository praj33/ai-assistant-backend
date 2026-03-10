# EXECUTION -> ENFORCEMENT GATE

## Requirement
No real-world action may execute unless the final enforcement verdict allows action execution.

## Final implementation
`app/services/execution_service.py` now:

- accepts the runtime enforcement surface as either a dict or `EnforcementVerdict`
- coerces that input into the canonical `EnforcementVerdict`
- checks `verdict.allows_action()` before any executor call
- returns `{"status": "blocked", ...}` for `REWRITE`, `BLOCK`, and `TERMINATE`

## Runtime authority guarantees
- `ALLOW` with action-capable scope is the only path that can issue gateway auth and reach an executor
- `REWRITE` affects the response path only and cannot execute platform actions
- `BLOCK` and `TERMINATE` fail closed at the execution boundary
- direct execution bypasses were removed from `device_bridge_service.py`
- reminder delivery now passes the full enforcement verdict into the execution gate

## Verification
- `ExecutionService.execute_action(...)` blocks when the verdict is `REWRITE`
- `ExecutionService.execute_action(...)` succeeds only when the verdict is `ALLOW`
- `DeviceBridgeService.send_command(...)` now routes through enforcement first and is blocked on `TERMINATE`
