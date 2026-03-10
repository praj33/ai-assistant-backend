# ENFORCEMENT RUNTIME TEST REPORT

## Test artifact
- Script: `test_enforcement_runtime_activation.py`

## Scenarios covered
- Safe message → `ALLOW`
- Risk content → `REWRITE`
- Unsafe request → `BLOCK`
- Validator failure → `TERMINATE` (fail-closed)

## Execution authority checks
- Execution refused on `REWRITE`
- Execution allowed on `ALLOW` (using `EXECUTION_SIMULATION=1` for side-effect free run)

## How to run

```bash
python test_enforcement_runtime_activation.py
```

Exit code `0` indicates all assertions passed.

