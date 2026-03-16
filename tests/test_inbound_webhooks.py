from datetime import datetime
import json
import os

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_telegram_inbound_webhook_flow():
    """Full spine wiring: Telegram webhook → inbound gateway → orchestrator."""
    payload = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "from": {"id": 222, "username": "test_user", "language_code": "en"},
            "chat": {"id": 111, "type": "private"},
            "date": 0,
            "text": "hello from telegram",
        },
    }

    resp = client.post("/webhook/telegram", json=payload)
    assert resp.status_code == 200
    body = resp.json()

    # Handler wrapper response
    assert body.get("status") == "processed"
    assert "trace_id" in body


def test_whatsapp_inbound_webhook_flow_no_secret():
    """
    WhatsApp webhook → inbound gateway when WHATSAPP_WEBHOOK_SECRET is not set.
    Verification should fail-open but still route through the gateway.
    """
    # Ensure secret is not set for this test
    os.environ.pop("WHATSAPP_WEBHOOK_SECRET", None)

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WAB123",
                "messaging": [
                    {
                        "sender": {"id": "user_wa_1"},
                        "message": {"type": "text", "text": {"body": "hello from whatsapp"}},
                    }
                ],
            }
        ],
    }

    resp = client.post(
        "/webhook/whatsapp",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "processed"
    assert "trace_id" in body


def test_whatsapp_inbound_webhook_rejects_invalid_signature_when_secret_set():
    """
    When WHATSAPP_WEBHOOK_SECRET is configured, WhatsApp webhook MUST verify
    X-Hub-Signature-256 and reject invalid signatures.
    """
    os.environ["WHATSAPP_WEBHOOK_SECRET"] = "test_secret"

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WAB123",
                "messaging": [
                    {
                        "sender": {"id": "user_wa_2"},
                        "message": {"type": "text", "text": {"body": "hello with bad signature"}},
                    }
                ],
            }
        ],
    }

    resp = client.post(
        "/webhook/whatsapp",
        data=json.dumps(payload),
        headers={
            "Content-Type": "application/json",
            # Intentionally wrong signature
            "X-Hub-Signature-256": "sha256=deadbeef",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "rejected"
    assert body.get("reason") == "webhook_verification_failed"


def test_email_inbound_webhook_flow_json():
    """Email webhook (JSON) → inbound gateway → orchestrator."""
    payload = {
        "from": "sender@example.com",
        "subject": "Test Subject",
        "content": "Body from email provider",
    }

    resp = client.post(
        "/webhook/email",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "processed"
    assert "trace_id" in body


def test_email_inbound_webhook_flow_raw_body():
    """Email webhook (raw body) → inbound gateway → orchestrator."""
    raw_body = "Raw email body without JSON"

    resp = client.post(
        "/webhook/email",
        data=raw_body.encode("utf-8"),
        headers={"Content-Type": "text/plain"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "processed"
    assert "trace_id" in body

