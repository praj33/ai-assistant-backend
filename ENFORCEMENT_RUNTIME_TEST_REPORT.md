# ENFORCEMENT RUNTIME TEST REPORT

## Test artifact
- Script: `test_enforcement_runtime_activation.py`

## End-to-end coverage
The test drives the real runtime path through `app/core/assistant_orchestrator.py`, not just the enforcement service shim.

## Verified scenarios
- Safe message -> `ALLOW`
- Risk content -> `REWRITE`
- Unsafe request -> `BLOCK`
- Validator failure -> `TERMINATE`
- Replay stability -> identical input produced identical request trace and identical verdict
- Runtime authority chain -> `ALLOW` request reached execution with one trace across all stages

## Execution authority verification
- execution is blocked on `REWRITE`
- execution succeeds only on `ALLOW`
- direct device bridge execution is blocked when enforcement returns `TERMINATE`

## Observed runtime evidence
- `ALLOW` produced a normal assistant response and an enforcement verdict with `decision = ALLOW`
- `REWRITE` produced modified safe response text from the deterministic safety output
- `BLOCK` returned the crisis-safe blocked response path
- `TERMINATE` returned `status = error` with `code = ENFORCEMENT_TERMINATED`

## Replay stability evidence
- Request: `hello deterministic replay`
- Request trace: `trace_6bf8a1decef2d740` on both runs
- Enforcement trace: `enf_c7fe387bc89cc8e4` on both runs
- Verdict: `ALLOW` with identical `scope`, `reason_code`, and `request_trace_id`

## Runtime chain demo
- Request: `send telegram to 1657991703 saying hello from runtime demo`
- Request trace: `trace_14a9c1e53981ac67`
- Enforcement decision: `ALLOW`
- Execution status: `success`
- Logged stages:
  - `request_received`
  - `safety_validation`
  - `intelligence_processing`
  - `enforcement_decision`
  - `orchestration_processing`
  - `action_execution`
  - `response_generated`

## How to run
```bash
python test_enforcement_runtime_activation.py
```

Exit code `0` indicates all assertions passed.
