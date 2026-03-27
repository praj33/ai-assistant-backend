import json
import os

from fastapi.testclient import TestClient


os.environ.setdefault("API_KEY", "localtest")

from app.main import app


client = TestClient(app)
client.headers.update({"X-API-Key": "localtest"})

sample_input = {
    "event": {
        "title": "Emotional dependency signal",
        "content": "You're the only one who gets me. Don't ever leave me.",
        "category": "conversation",
        "confidence": 0.91,
    }
}

response = client.post("/api/mitra/evaluate", json=sample_input)

print("INPUT")
print(json.dumps(sample_input, indent=2))
print()
print("OUTPUT")
print(json.dumps(response.json(), indent=2))
