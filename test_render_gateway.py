"""Test deployed Render gateway endpoints"""
import requests
import json

BASE = "https://ai-assistant-backend-8hur.onrender.com"

endpoints = [
    ("GET", "/health", None),
    ("GET", "/webhook/health", None),
    ("GET", "/webhook/telegram", None),
    ("POST", "/api/assistant", {
        "version": "3.0.0",
        "input": {"message": "Send a telegram message to @Zorollo saying Hello from the cloud!"},
        "context": {
            "platform": "web",
            "device": "desktop",
            "session_id": "render_test_001",
            "voice_input": False,
            "preferred_language": "en",
            "detected_language": "en"
        }
    })
]

for method, path, body in endpoints:
    try:
        url = BASE + path
        if method == "GET":
            r = requests.get(url, timeout=45)
        else:
            r = requests.post(url, json=body, timeout=45)
        print(f"{method} {path}: {r.status_code}")
        try:
            print(json.dumps(r.json(), indent=2)[:500])
        except Exception:
            print(r.text[:500])
    except Exception as e:
        print(f"{method} {path}: ERROR - {e}")
    print("---")
