import os

from fastapi.testclient import TestClient


os.environ.setdefault("API_KEY", "localtest")

from app.main import app
from app.services.bucket_service import BucketService


client = TestClient(app)
client.headers.update({"X-API-Key": "localtest"})


def setup_function():
    BucketService.clear_memory_logs()


def _mitra_payload(*, title: str, content: str, category: str, user_id: str, session_id: str) -> dict:
    return {
        "user_id": user_id,
        "context": {
            "platform": "samachar",
            "device": "api",
            "session_id": session_id,
            "voice_input": False,
        },
        "event": {
            "title": title,
            "content": content,
            "category": category,
            "confidence": 0.92,
        },
    }


def _artifact(trace_id: str, stage: str) -> dict | None:
    return BucketService().get_artifact(trace_id, stage=stage)


def test_mitra_control_plane_logs_correction_signal():
    first = client.post(
        "/api/mitra/evaluate",
        json=_mitra_payload(
            title="Outbound action",
            content="Send the school update on WhatsApp.",
            category="messaging",
            user_id="signal_user",
            session_id="signal_session",
        ),
    )
    assert first.status_code == 200

    second = client.post(
        "/api/mitra/evaluate",
        json=_mitra_payload(
            title="Outbound action correction",
            content="Actually, send the school update by email instead.",
            category="messaging",
            user_id="signal_user",
            session_id="signal_session",
        ),
    )

    assert second.status_code == 200
    second_body = second.json()
    assert second_body["signal_type"] == "correction"

    trace_id = second_body["trace_id"]
    signal_log = _artifact(trace_id, "rl_signal_capture")
    request_log = _artifact(trace_id, "mitra_request_log")

    assert signal_log is not None
    assert signal_log["data"]["signal_type"] == "correction"
    assert request_log is not None
    assert request_log["data"]["user_id"] == "signal_user"
    assert request_log["data"]["mitra_output"]["trace_id"] == trace_id


def test_mitra_control_plane_logs_refinement_signal():
    first = client.post(
        "/api/mitra/evaluate",
        json=_mitra_payload(
            title="Weather brief",
            content="Share the school weather update.",
            category="weather",
            user_id="refine_user",
            session_id="refine_session",
        ),
    )
    assert first.status_code == 200

    second = client.post(
        "/api/mitra/evaluate",
        json=_mitra_payload(
            title="Weather brief refinement",
            content="Let me rephrase: share the same school weather update for tomorrow morning only.",
            category="weather",
            user_id="refine_user",
            session_id="refine_session",
        ),
    )

    assert second.status_code == 200
    second_body = second.json()
    assert second_body["signal_type"] == "intent_refinement"

    signal_log = _artifact(second_body["trace_id"], "rl_signal_capture")
    assert signal_log is not None
    assert signal_log["data"]["signal_type"] == "intent_refinement"


def test_mitra_control_plane_marks_abrupt_topic_change_as_implicit_negative():
    first = client.post(
        "/api/mitra/evaluate",
        json=_mitra_payload(
            title="Weather brief",
            content="Share the school weather update.",
            category="weather",
            user_id="topic_user",
            session_id="topic_session",
        ),
    )
    assert first.status_code == 200

    second = client.post(
        "/api/mitra/evaluate",
        json=_mitra_payload(
            title="Sports switch",
            content="What is the cricket score right now?",
            category="sports",
            user_id="topic_user",
            session_id="topic_session",
        ),
    )

    assert second.status_code == 200
    assert second.json()["signal_type"] == "implicit_negative"


def test_assistant_response_exposes_trace_and_signal_for_frontend():
    response = client.post(
        "/api/assistant",
        json={
            "version": "3.0.0",
            "input": {"message": "hello"},
            "context": {
                "platform": "web",
                "device": "desktop",
                "session_id": "assistant_control_plane_session",
                "preferred_language": "en",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["trace_id"].startswith("trace_")
    assert body["signal_type"] == "implicit_positive"
    assert body["result"]["mitra"]["trace_id"] == body["trace_id"]
    assert body["result"]["mitra"]["signal_type"] == body["signal_type"]


def test_telephony_voice_input_flows_through_mitra_control_plane():
    response = client.post(
        "/webhook/telephony",
        json={
            "caller_id": "voice_user",
            "transcription": "Please remind me to call the school tomorrow morning.",
        },
    )

    assert response.status_code == 200
    trace_id = response.json()["trace_id"]
    request_log = _artifact(trace_id, "mitra_request_log")

    assert request_log is not None
    assert request_log["data"]["mitra_output"]["trace_id"] == trace_id
    assert request_log["data"]["mitra_output"]["system_context"]["voice_input"] is True
