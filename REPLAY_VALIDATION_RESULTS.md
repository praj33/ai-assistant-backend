# Replay Validation Results

## Replay Command

```powershell
python -m app.external.enforcement.replay_validation
```

## Result

The replay validator returned `all_identical: true` for all deterministic scenarios.

```json
{
  "all_identical": true,
  "scenario_count": 3,
  "scenarios": [
    {
      "name": "allow_general",
      "request_trace_id": "trace_replay_allow",
      "first": {
        "decision": "ALLOW",
        "trace_id": "enf_211814ba6457de8e"
      },
      "second": {
        "decision": "ALLOW",
        "trace_id": "enf_211814ba6457de8e"
      }
    },
    {
      "name": "rewrite_manipulation",
      "request_trace_id": "trace_replay_rewrite",
      "first": {
        "decision": "REWRITE",
        "trace_id": "enf_44098e78f30ca6bc"
      },
      "second": {
        "decision": "REWRITE",
        "trace_id": "enf_44098e78f30ca6bc"
      }
    },
    {
      "name": "block_unsafe",
      "request_trace_id": "trace_replay_block",
      "first": {
        "decision": "BLOCK",
        "trace_id": "enf_dd543a4292663204"
      },
      "second": {
        "decision": "BLOCK",
        "trace_id": "enf_dd543a4292663204"
      }
    }
  ]
}
```

## Stress Verification

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest tests/test_enforcement_hardening.py -q
```

Observed result:

```text
......                                                                   [100%]
6 passed
```

Stress cases covered:

- manipulation bypass phrasing blocks deterministically
- emotional manipulation rewrites deterministically
- persuasion pressure rewrites deterministically
- benign input allows deterministically
- tampered bucket artifact blocks enforcement
- tampered bucket artifact blocks execution even with forged `ALLOW`

## End-to-End Runtime Confirmation

```powershell
python test_enforcement_runtime_activation.py
```

Key confirmed outcomes:

- `ALLOW` remains executable
- `REWRITE` returns rewritten response only
- `BLOCK` halts unsafe content
- `TERMINATE` remains fail-closed
- runtime trace chain now includes `enforcement_telemetry`
