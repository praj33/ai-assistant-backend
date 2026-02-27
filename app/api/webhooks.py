from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from typing import Dict, Any, Optional
import json
from datetime import datetime

from app.core.assistant_orchestrator import handle_assistant_request

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


# Health check for webhook endpoints
@router.get("/webhook/health")
async def webhook_health():
    return {
        "status": "healthy",
        "service": "webhook_handler",
        "timestamp": datetime.utcnow().isoformat()
    }