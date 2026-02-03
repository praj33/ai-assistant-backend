import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
# Set API key for all requests
client.headers.update({"X-API-Key": "localtest"})

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Assistant Core v3 API" in response.json()["message"]

def test_summarize():
    response = client.post("/api/summarize", json={"text": "This is a test text.", "max_length": 10})
    assert response.status_code == 200
    assert "summary" in response.json()

def test_intent():
    response = client.post("/api/intent", json={"text": "Hello"})
    assert response.status_code == 200
    assert "intent" in response.json()

def test_task():
    response = client.post("/api/task", json={"description": "Test task"})
    assert response.status_code == 200
    assert "task_id" in response.json()

def test_decision_hub():
    response = client.post("/api/decision_hub", data={
        "input_text": "Test input",
        "platform": "web",
        "device_context": "desktop"
    })
    assert response.status_code == 200
    data = response.json()
    assert "final_decision" in data
    assert "confidence" in data
    assert "selected_agent" in data
    assert "preferred_llm" in data
    assert "device_context" in data
    assert "memory_reference" in data

def test_decision_hub_vr():
    response = client.post("/api/decision_hub", json={
        "input_text": "Speak something",
        "platform": "vr",
        "device_context": "vr",
        "voice_input": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["device_context"] == "vr"

def test_rl_action():
    response = client.post("/api/rl_action", json={"state": {}, "actions": ["action1", "action2"]})
    assert response.status_code == 200
    assert "selected_action" in response.json()

def test_embed():
    response = client.post("/api/embed", json={"texts": ["Hello world"]})
    assert response.status_code == 200
    assert "embeddings" in response.json()

def test_respond():
    response = client.post("/api/respond", json={"query": "Hello", "context": {}})
    assert response.status_code == 200
    assert "response" in response.json()

def test_voice_stt():
    # Mock file upload
    response = client.post("/api/voice_stt", data={"request": '{"audio_url": "test"}'})
    assert response.status_code == 200
    assert "text" in response.json()

def test_voice_tts():
    response = client.post("/api/voice_tts", json={"text": "Hello", "voice": "default"})
    assert response.status_code == 200
    assert "audio_url" in response.json()

def test_external_llm():
    response = client.post("/api/external_llm", json={"prompt": "Hello", "model": "uniguru"})
    assert response.status_code == 200
    assert "response" in response.json()

def test_external_app_crm():
    response = client.post("/api/external_app", json={"app": "crm", "action": "update", "params": {}})
    assert response.status_code == 200
    assert "crm_action" in response.json()["result"]

def test_external_app_erp():
    response = client.post("/api/external_app", json={"app": "erp", "action": "process", "params": {}})
    assert response.status_code == 200
    assert "erp_action" in response.json()["result"]

def test_external_app_calendar():
    response = client.post("/api/external_app", json={"app": "calendar", "action": "add", "params": {}})
    assert response.status_code == 200
    assert "calendar_action" in response.json()["result"]

def test_external_app_email():
    response = client.post("/api/external_app", json={"app": "email", "action": "send", "params": {}})
    assert response.status_code == 200
    assert "email_action" in response.json()["result"]

def test_voice_to_intent_flow():
    # Test voice STT then intent
    stt_response = client.post("/api/voice_stt", data={"request": '{"audio_url": "test"}'})
    text = stt_response.json()["text"]
    intent_response = client.post("/api/intent", json={"text": text})
    assert intent_response.status_code == 200

def test_multi_llm_routing():
    models = ["uniguru", "chatgpt", "groq", "gemini", "mistral"]
    for model in models:
        response = client.post("/api/external_llm", json={"prompt": "Hello", "model": model})
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__])