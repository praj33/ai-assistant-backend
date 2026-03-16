# MITRA Repository Integration Map

## Core Modules and Builders

- **assistant_orchestrator (Nilesh)**
  - File: `app/core/assistant_orchestrator.py`
  - Role: Central pipeline orchestration  
    Safety → Intelligence → Enforcement → Orchestration → Execution.

- **Safety Service (Akanksha)**
  - Files:
    - `app/services/safety_service.py`
    - `app/external/safety/behavior_validator.py`
  - Role: Content moderation and safety decision engine.

- **Intelligence Service (Sankalp)**
  - Files:
    - `app/services/intelligence_service.py`
    - `app/external/intelligence/intelligence_service.py`
    - `app/core/intentflow.py`
  - Role: Intent classification, risk detection, and high‑level reasoning context.

- **Enforcement Runtime (Raj)**
  - Files:
    - `app/services/enforcement_service.py`
    - `app/external/enforcement/enforcement_engine.py`
    - `app/external/enforcement/enforcement_verdict.py`
    - `app/external/enforcement/deterministic_trace.py`
  - Role: Deterministic enforcement authority over all responses and actions.

- **Execution Layer (Chandresh)**
  - Files:
    - `app/services/execution_service.py`
    - `app/executors/*.py`
  - Role: Universal execution gateway for WhatsApp, Email, Telegram, Instagram, Calendar, Reminder, EMS, and Device Gateway.

- **Bucket Infrastructure (Ashmit)**
  - Files:
    - `app/services/bucket_service.py`
    - `app/external/bucket/database/mongo_db.py`
    - `app/external/bucket/middleware/audit_middleware.py`
  - Role: Trace logging, integrity hashing, and immutable audit storage.

- **Audio Layer (Soham)**
  - Files:
    - `app/services/audio_service.py`
    - `Multilingual_Audio_Integration.md`
  - Role: Text‑to‑speech and speech‑to‑text integration.

- **Inbound Communication**
  - Files:
    - `app/inbound/inbound_gateway.py`
    - `app/inbound/whatsapp_inbound_handler.py`
    - `app/inbound/telegram_inbound_handler.py`
    - `app/inbound/email_inbound_handler.py`
    - `app/inbound/reminder_event_handler.py`
    - `app/api/webhooks.py`
  - Role: Unified inbound gateway for all external channels.

- **Device Bridge**
  - Files:
    - `app/services/device_bridge_service.py`
    - `app/executors/device_gateway_executor.py`
    - `DEVICE_BRIDGE_FOUNDATION.md`
  - Role: Connect Mitra to user devices (desktop, mobile, tablet, XR).

- **BHIV Core Interfaces**
  - Files:
    - `app/core/bhiv_core.py`
    - `app/core/bhiv_reasoner.py`
    - `app/routers/bhiv.py`
    - `app/bhiv_core_gateway.py`
  - Role: Connect Mitra runtime to BHIV Core governance and reasoning.

- **Karma Integration**
  - Files:
    - `hooks/karma.py`
    - `app/karma_adapter.py`
  - Role: User behavior scoring integrated into intelligence and enforcement context.

- **System Registry and Health**
  - Files:
    - `app/mitra_system_registry.py`
    - `app/mitra_system_health.py`
    - `app/main.py` (`/health/system` endpoint)
  - Role: Central module registry and unified system health reporting.

