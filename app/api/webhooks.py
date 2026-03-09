from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from typing import Dict, Any, Optional
import os
import json
from datetime import datetime

from app.core.assistant_orchestrator import handle_assistant_request
from app.services.telegram_contact_service import TelegramContactService

router = APIRouter()


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Handle incoming WhatsApp messages
    Ensures inbound messages go through the same safety → intelligence → enforcement → orchestration flow
    """
    try:
        payload = await request.json()
        
        # Extract message from WhatsApp Business API payload
        # Different providers may have different payload structures
        entries = payload.get("entry", [])
        if not entries:
            return {"status": "ignored", "reason": "no_entries"}
        
        messaging_events = entries[0].get("messaging", [])
        if not messaging_events:
            # May be other event types like message status updates
            return {"status": "ignored", "reason": "no_messaging_events"}
        
        messaging_event = messaging_events[0]
        
        # Check if it's a message event
        if messaging_event.get("message"):
            message_data = messaging_event["message"]
            
            # Only process text messages (ignore images, videos, etc. for now)
            if message_data.get("type") == "text":
                message_text = message_data["text"]["body"]
                sender_id = messaging_event["sender"]["id"]
                
                # Create internal request object that follows the same flow as regular API requests
                internal_request = {
                    "version": "3.0.0",
                    "input": {"message": message_text},
                    "context": {
                        "platform": "whatsapp",
                        "device": "mobile",
                        "session_id": sender_id,
                        "voice_input": False,
                        "preferred_language": "auto",
                        "detected_language": None
                    }
                }
                
                # Process through main orchestrator (same safety → intelligence → enforcement → orchestration flow)
                result = await handle_assistant_request(internal_request)
                
                # Log the processed message
                print(f"WhatsApp message from {sender_id} processed. Trace ID: {result.get('trace_id')}")
                
                return {
                    "status": "processed", 
                    "trace_id": result.get("trace_id"),
                    "processed_at": datetime.utcnow().isoformat()
                }
            else:
                # For non-text messages, we could implement media processing
                return {"status": "ignored", "reason": f"unsupported_message_type: {message_data.get('type')}"}
        else:
            # Could be other events like delivery receipts, read receipts, etc.
            return {"status": "ignored", "reason": "non_message_event"}
    
    except Exception as e:
        print(f"Error processing WhatsApp webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")


@router.post("/webhook/email")
async def email_webhook(request: Request):
    """
    Handle incoming email parsing
    Ensures inbound emails go through the same safety → intelligence → enforcement → orchestration flow
    """
    try:
        # For email, we might receive raw MIME data or parsed email data depending on the email provider
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            payload = await request.json()
        else:
            # For raw email data, we'd need to parse it differently
            raw_body = await request.body()
            # For now, assume it's JSON with content field
            payload = {"content": raw_body.decode('utf-8')}
        
        # Extract email content
        email_content = payload.get("content", "") or payload.get("text", "") or payload.get("body", "")
        sender = payload.get("from", payload.get("sender", ""))
        subject = payload.get("subject", "No Subject")
        
        if not email_content:
            return {"status": "ignored", "reason": "empty_content"}
        
        # Create internal request object
        internal_request = {
            "version": "3.0.0",
            "input": {"message": f"Subject: {subject}\n\n{email_content}"},
            "context": {
                "platform": "email",
                "device": "desktop",
                "session_id": sender,
                "voice_input": False,
                "preferred_language": "auto",
                "detected_language": None
            }
        }
        
        # Process through main orchestrator (same safety → intelligence → enforcement → orchestration flow)
        result = await handle_assistant_request(internal_request)
        
        # Log the processed email
        print(f"Email from {sender} processed. Trace ID: {result.get('trace_id')}")
        
        return {
            "status": "processed", 
            "trace_id": result.get("trace_id"),
            "processed_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        print(f"Error processing email webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")


@router.post("/webhook/telephony")
async def telephony_webhook(request: Request):
    """
    Handle telephony inbound (call received → transcription → intent)
    This is a stub for telephony integration
    """
    try:
        payload = await request.json()
        
        # Extract call details and transcription
        caller_id = payload.get("caller_id", "")
        transcription = payload.get("transcription", "")
        
        if not transcription:
            return {"status": "ignored", "reason": "no_transcription"}
        
        # Create internal request object
        internal_request = {
            "version": "3.0.0",
            "input": {"message": transcription},
            "context": {
                "platform": "telephony",
                "device": "phone",
                "session_id": caller_id,
                "voice_input": True,  # Voice input from call
                "preferred_language": "auto",
                "detected_language": None
            }
        }
        
        # Process through main orchestrator (same safety → intelligence → enforcement → orchestration flow)
        result = await handle_assistant_request(internal_request)
        
        # Log the processed call
        print(f"Telephony call from {caller_id} processed. Trace ID: {result.get('trace_id')}")
        
        return {
            "status": "processed", 
            "trace_id": result.get("trace_id"),
            "processed_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        print(f"Error processing telephony webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """
    Handle incoming Telegram Bot API updates.
    Routes inbound messages through Safety → Intelligence → Enforcement → Orchestration.
    """
    try:
        payload = await request.json()

        # Telegram sends updates with a "message" field
        message = payload.get("message", {})
        if not message or not message.get("text"):
            return {"status": "ignored", "reason": "no_text_message"}

        chat = message.get("chat", {})
        sender = message.get("from", {})
        text = message.get("text", "")

        # Persist username -> chat_id mapping for future outbound sends
        chat_id = chat.get("id")
        username = sender.get("username")
        if chat_id is not None and username:
            TelegramContactService().save_contact(username=username, chat_id=int(chat_id))

        internal_request = {
            "version": "3.0.0",
            "input": {"message": text},
            "context": {
                "platform": "telegram",
                "device": "mobile",
                "session_id": str(chat_id or ""),
                "voice_input": False,
                "preferred_language": sender.get("language_code", "auto"),
                "detected_language": None
            }
        }

        result = await handle_assistant_request(internal_request)
        print(f"Telegram message from {sender.get('username', sender.get('id'))} processed. Trace: {result.get('trace_id')}")

        return {
            "status": "processed",
            "trace_id": result.get("trace_id"),
            "processed_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"Error processing Telegram webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")


@router.get("/webhook/telegram")
async def telegram_webhook_verify(request: Request):
    """Telegram webhook verification — just returns OK."""
    return {"status": "ok", "service": "telegram_webhook"}


@router.post("/webhook/instagram")
async def instagram_webhook(request: Request):
    """
    Handle incoming Instagram Messenger API webhooks.
    Routes inbound messages through Safety → Intelligence → Enforcement → Orchestration.
    """
    try:
        payload = await request.json()

        entries = payload.get("entry", [])
        if not entries:
            return {"status": "ignored", "reason": "no_entries"}

        for entry in entries:
            messaging_events = entry.get("messaging", [])
            for event in messaging_events:
                if event.get("message") and event["message"].get("text"):
                    sender_id = event.get("sender", {}).get("id", "")
                    text = event["message"]["text"]

                    internal_request = {
                        "version": "3.0.0",
                        "input": {"message": text},
                        "context": {
                            "platform": "instagram",
                            "device": "mobile",
                            "session_id": sender_id,
                            "voice_input": False,
                            "preferred_language": "auto",
                            "detected_language": None
                        }
                    }

                    result = await handle_assistant_request(internal_request)
                    print(f"Instagram message from {sender_id} processed. Trace: {result.get('trace_id')}")

        return {
            "status": "processed",
            "processed_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"Error processing Instagram webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")


@router.get("/webhook/instagram")
async def instagram_webhook_verify(request: Request):
    """Instagram/Meta webhook verification challenge."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    verify_token = os.getenv("META_VERIFY_TOKEN", "mitra_verify_token")
    if mode == "subscribe" and token == verify_token:
        return int(challenge) if challenge else "ok"
    raise HTTPException(status_code=403, detail="Verification failed")


# Health check for webhook endpoints
@router.get("/webhook/health")
async def webhook_health():
    return {
        "status": "healthy",
        "service": "webhook_handler",
        "platforms": ["whatsapp", "email", "telegram", "instagram", "telephony"],
        "timestamp": datetime.utcnow().isoformat()
    }