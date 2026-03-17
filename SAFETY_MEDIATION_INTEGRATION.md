# Safety Mediation Integration

This backend now includes deterministic inbound mediation and outbound safety gates
inspired by the ai-being safety system. Both features are environment-controlled.

## Inbound Mediation

Purpose:
- Summarize or delay inbound content that contains panic language, manipulation,
  or information overload.
- Optionally silence or escalate severe threats.

How it works:
- Runs before the main orchestration pipeline in `inbound_gateway`.
- Emits an `inbound_mediation` bucket log and a unified inbound payload.

Enable it:
```
INBOUND_MEDIATION_ENABLED=1
INBOUND_MEDIATION_CHANNELS=email,whatsapp,telegram
```

Optional controls:
```
INBOUND_MEDIATION_QUIET_HOURS_START=22:00
INBOUND_MEDIATION_QUIET_HOURS_END=07:00
INBOUND_MEDIATION_TZ_OFFSET=UTC
INBOUND_MEDIATION_CONTACT_LIMITS_ENABLED=0
```

## Outbound Safety Gate

Purpose:
- Remove manipulative phrasing and urgency inflation.
- Strip system-style language before messages are sent.
- Block explicitly threatening outbound content.

How it works:
- Runs inside `ExecutionService.execute_action` after enforcement, before execution.
- Emits `outbound_safety_gate` and `outbound_event` bucket logs with unified schema.

Enable it:
```
OUTBOUND_SAFETY_GATE_ENABLED=1
```

## Unified Schema Logging

Inbound and outbound events now include a `unified_payload` that follows the
ai-being unified schema to improve traceability and audit consistency.
