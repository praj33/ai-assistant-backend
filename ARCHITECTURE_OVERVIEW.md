# Assistant Backend Architecture (v3)

## Overview

This backend implements the AI Assistant as a **single, production-ready system**
with a **locked public interface**.

The system exposes **one public API endpoint** for all assistant interactions
and encapsulates all intelligence, workflow execution, and integrations internally.

### Public API
- POST /api/assistant
- GET /health

No other endpoints are supported for frontend integration.

---

## High-Level Architecture

Client (Web / Mobile / Desktop)
|
v
POST /api/assistant
|
v
Assistant Orchestrator
|
+--> Input Normalization
+--> Intent & Task Analysis (internal)
+--> Routing & Control Logic
|
+--> Intelligence Response Path
|     |
|     +--> LLM Response
|
+--> Workflow Execution Path
|     |
|     +--> Internal Workflow Engine
|     +--> External Services
|
+--> Fallback Response Path

---

## Architectural Layers

### 1. API Layer
- Exposes a single endpoint: `/api/assistant`
- Handles authentication, validation, and error normalization
- Provides a deterministic, frontend-safe contract

### 2. Orchestration Layer
- Central decision point for all assistant requests
- Applies routing and fallback rules deterministically
- Ensures frontend never depends on internal systems

### 3. Intelligence & Workflow Layer (Internal)
- Performs intent classification and task analysis
- Executes workflows when side-effects are required
- Integrates with language models and external services
- **Not accessible directly by clients**

### 4. Infrastructure Layer
- API key validation and rate limiting
- Logging and audit trails
- Persistence and caching
- External service integrations

---

## Routing & Control Logic

The assistant uses explicit, centralized routing rules.

### Intelligence Response Path (Passive)
Used when:
- The user request is informational (Q&A, explanation, summarization)
- No side effects or state mutation are required
- A workflow execution is not necessary

Result:
- Response generated via intelligence layer
- No workflow execution
- Deterministic response returned

---

### Workflow Execution Path (Active)
Used when:
- The user request implies an action (task creation, reminder, scheduling)
- Side effects or state changes are required
- Structured parameters are available

Result:
- Internal workflow engine is triggered
- Execution result returned in normalized format
- Frontend contract remains unchanged

---

### Fallback Path
Used when:
- Intent confidence is low
- Required dependencies are unavailable
- Partial workflow failures occur

Result:
- Safe passive response returned
- No workflow execution
- Frontend schema preserved

---

## Graceful Failure & Safety Policy

The backend guarantees frontend-safe behavior under all failure conditions.

### Failure Handling Rules

- **Missing Dependencies**
  - Dependency is skipped
  - Passive response returned

- **Timeouts or Slow Responses**
  - Orchestration timeout enforced
  - Partial execution abandoned
  - Safe fallback response returned

- **Partial Workflow Failure**
  - Failure does not break response schema
  - User receives stable acknowledgement or retry-safe message

- **Unexpected Errors**
  - Deterministic error envelope returned
  - No internal stack traces exposed

### Guarantee

Under no condition does the backend:
- Break the response schema
- Leak internal logic
- Require frontend retries due to instability

---

## Request Lifecycle

1. Client sends request to `/api/assistant`
2. API layer validates authentication and input
3. Orchestrator normalizes request
4. Routing logic selects execution path
5. Response is normalized and returned
6. Frontend renders without awareness of internals

---

## Design Principles

- **Single Entry Point**
- **Encapsulation of internals**
- **Deterministic routing**
- **Frontend safety**
- **Production stability**

---

## Deployment & Monitoring

- Containerized deployment
- Health endpoint for uptime checks
- Structured logging and error tracking
- Stateless execution for scalability

---

## Architecture Status

**LOCKED**

This architecture is production-ready and safe for frontend integration.

No additional public endpoints or routing paths may be introduced without review.
