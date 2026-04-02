# DEMO RUNBOOK

Use only this clone:

`C:\Users\Gauri\Downloads\integration\integration\AI-ASSISTANT-control-plane`

Do not use:

`C:\Users\Gauri\Downloads\integration\integration\AI-ASSISTANT-`

## Fastest Option

Run the in-process demo runner:

```powershell
cd C:\Users\Gauri\Downloads\integration\integration\AI-ASSISTANT-control-plane
python demo_control_plane_runner.py
```

What it produces:

- clean `ALLOW`
- rewrite `FLAG`
- harmful `BLOCK`
- `correction` signal
- `intent_refinement` signal
- telephony voice path through Mitra
- direct enforcement bypass block proof

Outputs are saved in:

`demo_artifacts\<timestamp>\`

Recommended files to show in the video:

- `00_summary.json`
- `01_clean_allow.json`
- `02_flag_rewrite.json`
- `03_block_harmful.json`
- `04_correction_signal.json`
- `06_voice_telephony.json`
- `07_bypass_block.json`

## Local API Option

If you want to show the HTTP endpoint live:

```powershell
cd C:\Users\Gauri\Downloads\integration\integration\AI-ASSISTANT-control-plane
$env:PYTHONPATH = (Get-Location).Path
$env:API_KEY = "localtest"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then in a second terminal:

Clean case:

```powershell
$headers = @{ "X-API-Key" = "localtest" }
$body = @{
  user_id = "demo_clean_user"
  context = @{
    platform = "samachar"
    device = "api"
    session_id = "demo_clean_session"
  }
  event = @{
    title = "Weather update"
    content = "Tomorrow will be sunny with light winds."
    category = "weather"
    confidence = 0.93
  }
} | ConvertTo-Json -Depth 6
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/mitra/evaluate" -Headers $headers -ContentType "application/json" -Body $body
```

Rewrite case:

```powershell
$headers = @{ "X-API-Key" = "localtest" }
$body = @{
  user_id = "demo_flag_user"
  context = @{
    platform = "samachar"
    device = "api"
    session_id = "demo_flag_session"
  }
  event = @{
    title = "Emotional dependency signal"
    content = "You're the only one who gets me. Don't ever leave me."
    category = "conversation"
    confidence = 0.91
  }
} | ConvertTo-Json -Depth 6
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/mitra/evaluate" -Headers $headers -ContentType "application/json" -Body $body
```

Block case:

```powershell
$headers = @{ "X-API-Key" = "localtest" }
$body = @{
  user_id = "demo_block_user"
  context = @{
    platform = "samachar"
    device = "api"
    session_id = "demo_block_session"
  }
  event = @{
    title = "Explicit request"
    content = "I want nude photo."
    category = "content_request"
    confidence = 0.98
  }
} | ConvertTo-Json -Depth 6
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/mitra/evaluate" -Headers $headers -ContentType "application/json" -Body $body
```

Telephony voice path:

```powershell
$body = @{
  caller_id = "demo_voice_user"
  transcription = "Please remind me to call the school tomorrow morning."
} | ConvertTo-Json -Depth 4
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/webhook/telephony" -Headers @{ "X-API-Key" = "localtest" } -ContentType "application/json" -Body $body
```

## Suggested Video Order

1. Show frozen demo repo path and cloned working repo path.
2. Open `REVIEW_PACKET.md`.
3. Run `python demo_control_plane_runner.py`.
4. Open `demo_artifacts\<timestamp>\00_summary.json`.
5. Show `01_clean_allow.json`.
6. Show `02_flag_rewrite.json`.
7. Show `03_block_harmful.json`.
8. Show `04_correction_signal.json`.
9. Show `06_voice_telephony.json`.
10. Show `07_bypass_block.json`.

## Submission Files

- `REVIEW_PACKET.md`
- `TEST_RESULTS.md`
- `MITRA_CONTROL_PLANE_LIVE_JSON.json`
- `MITRA_BUCKET_LOG_PROOF.json`
- `MITRA_BYPASS_BLOCK_PROOF.json`

## Verification Command

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest tests/test_mitra_api.py tests/test_mitra_control_plane_integration.py tests/test_enforcement_hardening.py tests/test_generic_response_runtime.py -q
```
