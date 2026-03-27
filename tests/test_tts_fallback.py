import os

from fastapi.testclient import TestClient


os.environ.setdefault("API_KEY", "localtest")

from app.main import app


client = TestClient(app)
client.headers.update({"X-API-Key": "localtest"})


def test_tts_status_reports_unavailable_without_optional_xtts_runtime():
    response = client.get("/api/tts/status")

    assert response.status_code == 200
    body = response.json()
    assert body["tts"]["status"] == "unavailable"
    assert body["tts"]["model_loaded"] is False


def test_tts_endpoint_fails_softly_when_optional_xtts_runtime_is_missing():
    response = client.post(
        "/api/tts",
        json={"text": "Hello from Mitra", "language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["audio_base64"] is None
