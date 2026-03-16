# Inbound Gateway Architecture

## Purpose
Mitra’s inbound nervous system standardizes all inbound messages before any processing.
Every inbound event enters the same deterministic pipeline:

Safety → Intelligence → Enforcement → Orchestrator → Execution

There are no bypass paths and no direct execution from inbound handlers.

## Core Components
1. `app/inbound/inbound_gateway.py`
   - Normalizes inbound events into a common structure.
   - Builds a single internal request format.
   - Calls `assistant_orchestrator.handle_assistant_request()`.
   - Logs inbound trace artifacts to Bucket.

2. Inbound handlers
   - `app/inbound/whatsapp_inbound_handler.py`
   - `app/inbound/telegram_inbound_handler.py`
   - `app/inbound/email_inbound_handler.py`
   - `app/inbound/reminder_event_handler.py`
   - These parse provider payloads and call `inbound_gateway.process_message()`.

3. Bucket logging
   - Each inbound event logs: `trace_id`, `platform`, `message`, `timestamp`, and `metadata`.
   - Stage: `inbound_event`.

## Standard Normalized Format
Each inbound handler produces a standard structure:
```
{
  "platform": "<platform>",
  "user_id": "<sender or system id>",
  "message": "<text content>",
  "timestamp": "<ISO-8601>",
  "metadata": { ... }
}
```

## Determinism & Fail-Closed Guarantees
- The inbound gateway does not execute actions directly.
- The orchestrator controls execution through enforcement decisions.
- Bucket logging provides replayable trace artifacts.

## Extension Guidance
To add a new inbound platform:
1. Create a new handler in `app/inbound/`.
2. Normalize to the standard format.
3. Call `process_message()` only.
