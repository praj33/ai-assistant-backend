# AI Assistant Backend

Production-locked backend for the AI Assistant.
Exposes a single public API for frontend integration.

---

## Public API

POST /api/assistant  
POST /api/mitra/evaluate  
GET /health

`/api/assistant` remains the assistant entrypoint.
`/api/mitra/evaluate` exposes Mitra's existing deterministic decision flow for structured event input.
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

## Optional TTS Runtime

The main backend deploy does not require Coqui XTTS.
Optional TTS dependencies are isolated from the base deployment so the core API can build reliably on Render.

To enable the XTTS stack on a dedicated environment, install:

`pip install -r requirements-tts.txt`
