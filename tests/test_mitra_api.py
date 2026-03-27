import os
import time

from fastapi.testclient import TestClient


os.environ.setdefault("API_KEY", "localtest")

from app.main import app
from app.services.bucket_service import BucketService


client = TestClient(app)
client.headers.update({"X-API-Key": "localtest"})


def _post(payload: dict):
    return client.post("/api/mitra/evaluate", json=payload)


def setup_function():
    BucketService.clear_memory_logs()


def test_mitra_evaluate_allows_safe_event():
    response = _post(
        {
            "event": {
                "title": "Weather update",
                "content": "Tomorrow will be sunny with light winds.",
                "category": "weather",
                "confidence": 0.93,
            }
        }
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ALLOW"
    assert body["risk_level"] == "LOW"
    assert isinstance(body["reason"], str) and body["reason"]
    assert 0.0 <= body["confidence"] <= 1.0


def test_mitra_evaluate_flags_existing_rewrite_flow():
    response = _post(
        {
            "event": {
                "title": "Emotional dependency signal",
                "content": "You're the only one who gets me. Don't ever leave me.",
                "category": "conversation",
                "confidence": 0.91,
            }
        }
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FLAG"
    assert body["risk_level"] == "MEDIUM"
    assert 0.0 <= body["confidence"] <= 1.0


def test_mitra_evaluate_blocks_existing_hard_deny_flow():
    response = _post(
        {
            "event": {
                "title": "Explicit request",
                "content": "I want nude photo.",
                "category": "content_request",
                "confidence": 0.98,
            }
        }
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "BLOCK"
    assert body["risk_level"] == "HIGH"
    assert 0.0 <= body["confidence"] <= 1.0


def test_mitra_evaluate_missing_event_returns_clear_error():
    response = _post({})

    assert response.status_code == 400
    assert response.json() == {"error": "Missing event payload."}


def test_mitra_evaluate_is_deterministic_and_fast():
    payload = {
        "event": {
            "title": "Dependency signal",
            "content": "You're the only one who gets me. Don't ever leave me.",
            "category": "conversation",
            "confidence": 0.9,
        }
    }

    first_elapsed_start = time.perf_counter()
    first = _post(payload)
    first_elapsed = time.perf_counter() - first_elapsed_start

    second_elapsed_start = time.perf_counter()
    second = _post(payload)
    second_elapsed = time.perf_counter() - second_elapsed_start

    third_elapsed_start = time.perf_counter()
    third = _post(payload)
    third_elapsed = time.perf_counter() - third_elapsed_start

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200
    assert first.json() == second.json() == third.json()
    assert first_elapsed < 2.0
    assert second_elapsed < 2.0
    assert third_elapsed < 2.0


def test_samachar_shaped_payload_chains_without_schema_mismatch():
    samachar_output = {
        "event": {
            "title": "Incoming narrative classification",
            "content": "Tomorrow will be sunny with light winds.",
            "category": "weather",
            "confidence": 0.87,
        }
    }

    response = _post(samachar_output)

    assert response.status_code == 200
    body = response.json()
    assert sorted(body.keys()) == ["confidence", "reason", "risk_level", "status"]
    assert body["status"] in {"ALLOW", "FLAG", "BLOCK"}
