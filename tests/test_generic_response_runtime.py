import asyncio

from fastapi.testclient import TestClient

from app.core.respond_service import build_fallback_response, generate_generic_response
from app.main import app


client = TestClient(app)
client.headers.update({"X-API-Key": "localtest"})


def test_build_fallback_response_weather_requests_location():
    response = build_fallback_response("what's the weather today?", {})
    assert "location" in response.lower() or "city" in response.lower()
    assert "i understand:" not in response.lower()


def test_build_fallback_response_telegram_requests_details():
    response = build_fallback_response("send telegram", {})
    lowered = response.lower()
    assert "telegram" in lowered
    assert "username" in lowered or "chat id" in lowered
    assert "message" in lowered


def test_build_fallback_response_ems_requests_details():
    response = build_fallback_response("create ems task", {})
    lowered = response.lower()
    assert "ems" in lowered
    assert "title" in lowered
    assert "assignee" in lowered
    assert "priority" in lowered


def test_build_fallback_response_task_requests_details():
    response = build_fallback_response("create task", {})
    lowered = response.lower()
    assert "task" in lowered
    assert "title" in lowered
    assert "details" in lowered or "deadline" in lowered


def test_generate_generic_response_rejects_mock_style_output(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    response = asyncio.run(
        generate_generic_response(
            query="hello",
            context={"platform": "web", "device": "desktop"},
            model="uniguru",
        )
    )

    assert response == "Hello. How can I help?"
    assert "mock" not in response.lower()
    assert "context:" not in response.lower()


def test_assistant_runtime_uses_improved_generic_response(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    response = client.post(
        "/api/assistant",
        json={
            "version": "3.0.0",
            "input": {"message": "what's the weather today?"},
            "context": {"platform": "web", "device": "desktop", "session_id": "generic_response_test"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    text = body["result"]["response"].lower()

    assert "i understand:" not in text
    assert "how can i help you with that?" not in text
    assert "location" in text or "city" in text


def test_assistant_runtime_handles_swagger_style_payload_without_internal_error(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    response = client.post(
        "/api/assistant",
        json={
            "version": "3.0.0",
            "input": {
                "message": "hello",
                "summarized_payload": {},
                "audio_data": "string",
                "audio_format": "mp3",
            },
            "context": {
                "platform": "web",
                "device": "desktop",
                "session_id": "swagger_session",
                "voice_input": False,
                "preferred_language": "auto",
                "detected_language": "string",
                "audio_input_data": "string",
                "audio_output_requested": False,
                "age_gate_status": False,
                "region_policy": {},
                "platform_policy": {},
                "user_context": {},
                "authenticated_user_context": {},
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["result"]["enforcement"]["decision"] in {"ALLOW", "REWRITE", "BLOCK"}
