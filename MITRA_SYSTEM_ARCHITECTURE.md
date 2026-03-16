# Mitra System Architecture

## High‑Level Runtime Flow

Every inbound event follows the same deterministic pipeline:

1. **Inbound Handler** (per platform)
2. **Inbound Gateway** (`app/inbound/inbound_gateway.py`)
3. **Assistant Orchestrator** (`app/core/assistant_orchestrator.py`)
   - Safety → Intelligence → Enforcement → Orchestration → Execution
4. **Execution Service** (`app/services/execution_service.py`)
5. **Bucket Logging** (`app/services/bucket_service.py`)

No module is allowed to bypass this sequence.

## Core Components

- **Inbound Communication**
  - Handlers: WhatsApp, Telegram, Email, Reminder, Telephony, Instagram.
  - All call `process_message()` from `inbound_gateway`, which builds the internal request and forwards to the orchestrator.

- **Safety Layer (Akanksha)**
  - `SafetyService.validate_content()` wraps `behavior_validator.validate_behavior`.
  - Receives message text + context and produces a safety decision and mediation artifact.
  - Logs to Bucket via `call_safety_service` helpers in the orchestrator.

- **Intelligence Layer (Sankalp)**
  - `IntelligenceService.process_interaction()` calls the external intelligence core.
  - Input context includes:
    - `user_input`
    - platform / session information
    - `karma_data` from `karma_adapter`.
  - Output includes intent, risk flags, and (now) a deterministic `karma_score`.

- **Enforcement Runtime (Raj)**
  - `EnforcementService.enforce_policy()` converts runtime payloads into the deterministic enforcement engine format.
  - Enforces:
    - Terminate / Block / Rewrite / Allow decisions
    - Scope over response vs. action
    - Bucket mediation artifact requirements.
  - Emits enforcement telemetry into Bucket.

- **Execution Layer (Chandresh)**
  - `ExecutionService.execute_action()` is the universal execution gateway.
  - All platform actions are gated by an `EnforcementVerdict` and bucket validation before real executors are called.

- **Bucket Infrastructure (Ashmit)**
  - `BucketService.log_event()` stores immutable, integrity‑hashed artifacts for every critical stage:
    - `request_received`
    - `safety_validation`
    - `intelligence_processing`
    - `enforcement_decision`
    - `orchestration_processing`
    - `action_execution`
    - `response_generated`
    - `inbound_event`.

- **Audio Layer (Soham)**
  - `AudioService` provides STT and TTS.
  - Orchestrator uses it to:
    - Convert audio payloads into text before safety/intelligence.
    - Optionally produce audio responses.

- **System Registry**
  - `app/mitra_system_registry.py` holds single shared instances of:
    - SafetyService
    - IntelligenceService
    - EnforcementService
    - ExecutionService
    - BucketService
    - AudioService
  - Orchestrator imports services from this registry, ensuring a single point of construction.

- **Karma Adapter**
  - `app/karma_adapter.py` fetches user karma from `hooks/karma.py`.
  - Injects `karma_data` into intelligence context and ensures `karma_score` is always present for enforcement.

- **BHIV Core Gateway**
  - `app/bhiv_core_gateway.py` adapts Mitra runtime to BHIV Core:
    - Identity registration payload.
    - System health reporting.
    - Governance hook descriptions.

- **System Health Monitor**
  - `app/mitra_system_health.py` exposes `get_system_health_snapshot()`.
  - `/health/system` endpoint in `app/main.py` returns:
    - Module status snapshot from the registry.
    - Deep Bucket status (`mongo_connected`, `audit_active`, etc.).

## Determinism, Trace Continuity, and Observability

- Every request is normalized into a canonical payload in `inbound_gateway`.
- `assistant_orchestrator` computes a deterministic request trace ID via `deterministic_trace.generate_trace_id`.
- The same `trace_id` is propagated through:
  - Safety
  - Intelligence
  - Enforcement
  - Orchestration
  - Execution
  - Bucket logging.
- Bucket artifacts include an integrity hash so traces can be verified end‑to‑end.

## Integration with BHIV, Bucket, and Karma

- **BHIV Core**
  - Accesses Mitra via the BHIV core gateway and the dedicated BHIV router.
  - Can query system health and governance hooks.

- **Bucket**
  - Required for enforcement + execution mediation in production.
  - Validates safety artifacts before any real‑world action is executed.

- **Karma**
  - Integrated as an input signal into intelligence and enforcement decisions.
  - Used as a bias input (`karma_bias_input`) for safety/intelligence and a numeric `karma_score` for enforcement.

