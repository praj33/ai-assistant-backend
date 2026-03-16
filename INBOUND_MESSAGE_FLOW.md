# Inbound Message Flow

## Unified Pipeline
All inbound messages enter the same pipeline, regardless of source:

Inbound Handler → Inbound Gateway → Safety → Intelligence → Enforcement → Orchestrator → Execution

## WhatsApp
1. `/webhooks/whatsapp` receives payload.
2. `whatsapp_inbound_handler` extracts sender + message.
3. `inbound_gateway.process_message()` normalizes and forwards.

## Telegram
1. `/webhooks/telegram` receives update.
2. `telegram_inbound_handler` extracts chat + sender + message.
3. Contact is stored for username resolution.
4. `inbound_gateway.process_message()` forwards to pipeline.

## Email
1. `/webhooks/email` receives provider payload.
2. `email_inbound_handler` extracts sender + subject + body.
3. `inbound_gateway.process_message()` forwards to pipeline.

## Reminder Scheduler
1. Scheduler detects due reminder.
2. `reminder_event_handler` generates a system message.
3. `inbound_gateway.process_message()` forwards to pipeline.

## Trace & Observability
Each inbound event logs an `inbound_event` artifact to Bucket:
- `trace_id`
- `platform`
- `user_id`
- `message`
- `timestamp`
- `metadata`

This provides full observability and replay correlation.
