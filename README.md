# AI Assistant Backend

Production-locked backend for the AI Assistant.
Exposes a single public API for frontend integration.

---

## Public API

POST /api/assistant  
GET /health

`/api/assistant` is the only supported endpoint.
All other functionality is internal and not part of the public contract.

---

## Authentication

All requests require:

X-API-Key: <api-key>

---

## API Contract

The request and response schemas are strictly defined and versioned.

See: ASSISTANT_BACKEND_CONTRACT.md

---

## Architecture

The backend uses a single-entry orchestration model.
All intelligence, workflows, and integrations are internal.

See: ARCHITECTURE_OVERVIEW.md

---

## Health Check

GET /health

---

## Status

Backend locked and safe for frontend.
