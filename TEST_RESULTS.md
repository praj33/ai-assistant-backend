# TEST RESULTS

Date: 2026-03-30
Working clone: `C:\Users\Gauri\Downloads\integration\integration\AI-ASSISTANT-control-plane`
Branch: `mitra-control-plane`
Frozen demo repo left untouched: `C:\Users\Gauri\Downloads\integration\integration\AI-ASSISTANT-` at `e40948ec6c098920e629a0be1e302e47665d8b97`

Command used:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest tests/test_mitra_api.py tests/test_mitra_control_plane_integration.py tests/test_enforcement_hardening.py tests/test_generic_response_runtime.py -q
```

Result:

```text
32 passed
```

Scenarios verified:

| Scenario | Result | Proof |
| --- | --- | --- |
| Clean input | `ALLOW` with `LOW` risk, unified contract returned, trace continuity preserved | `trace_1d18ac2061449063` |
| Rewrite input | `FLAG` with `MEDIUM` risk, existing Akanksha rewrite used, no duplicate safety path | `trace_9908ca81967a0e5d` |
| Harmful input | `BLOCK` with `HIGH` risk, same request trace preserved through Mitra flow | `trace_fb16cd7ef39c9f86` |
| Correction flow | RL signal captured as `correction` and written to bucket | `trace_319fed4a847f63f1` |
| Refinement flow | RL signal captured as `intent_refinement` and written to bucket | `trace_ed4265c57e0c6148` |
| Repeated usage / abrupt topic change | RL signal captured as `implicit_negative` | verified by `test_mitra_control_plane_marks_abrupt_topic_change_as_implicit_negative` |
| Voice input | Telephony webhook entered assistant path, then Mitra control plane, with `voice_input: true` in system context | `trace_ef47ca393f29ac0e` |
| Direct enforcement bypass | Blocked before Raj runtime could be used directly | `trace_review_direct_bypass` |

What was verified:

- Every public Mitra response now includes `status`, `risk_level`, `reason`, `confidence`, `trace_id`, `signal_type`, and `system_context`.
- The same request trace is carried through safety, intelligence, enforcement logging, response contract logging, and bucket request logging.
- Bucket request logs include `user_id`, `input`, `mitra_output`, `trace_id`, and `timestamp`.
- RL signal capture is deterministic and bucket logged.
- `/api/assistant` now exposes `trace_id` and `signal_type` for frontend consumption.
- Voice input reaches Mitra authority before downstream orchestration/execution.
- Direct `EnforcementService.enforce_policy()` access is blocked unless Mitra opens the internal guard.

Artifacts produced:

- `MITRA_CONTROL_PLANE_LIVE_JSON.json`
- `MITRA_BUCKET_LOG_PROOF.json`
- `MITRA_BYPASS_BLOCK_PROOF.json`
- `REVIEW_PACKET.md`

Notes:

- The existing bucket service ran in its real fallback mode because local Mongo was not available in this environment. No new mock logger was introduced.
- The telephony voice test completed successfully, but reminder task persistence still logs a local Mongo warning when task-save is attempted. The Mitra control-plane trace, logging, and response path still completed successfully.
