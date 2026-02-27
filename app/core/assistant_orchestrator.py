from datetime import datetime
import hashlib
import uuid
import json
import traceback
from typing import Dict, Any, Optional

from app.core.summaryflow import summary_flow
from app.core.intentflow import intent_flow
from app.core.taskflow import task_flow
from app.core.decision_hub import decision_hub
from app.core.logging import get_logger
from app.core.database import get_db

# Import integrated services
from app.services.safety_service import SafetyService
from app.services.intelligence_service import IntelligenceService
from app.services.enforcement_service import EnforcementService
from app.services.bucket_service import BucketService
from app.services.execution_service import ExecutionService
from app.services.multilingual_service import MultilingualService
from app.services.audio_service import AudioService

logger = get_logger(__name__)

CRISIS_SAFE_RESPONSE = (
    "I'm really glad you shared this. I can't help with harming yourself, "
    "but I want you to have immediate support right now. "
    "If you're in immediate danger, call emergency services now. "
    "In the U.S. and Canada, call or text 988 for the Suicide & Crisis Lifeline. "
    "If you're elsewhere, contact your local emergency number or nearest crisis line."
)

# Initialize services
safety_service = SafetyService()
intelligence_service = IntelligenceService()
enforcement_service = EnforcementService()
bucket_service = BucketService()
execution_service = ExecutionService()
multilingual_service = MultilingualService()
audio_service = AudioService()

def generate_trace_id() -> str:
    """Generate unique trace ID for request tracking"""
    return f"trace_{uuid.uuid4().hex[:12]}"

def extract_action_parameters(text: str, action_type: str) -> Dict[str, Any]:
    """Extract action parameters from user text"""
    import re
    
    if action_type == "email":
        # Extract email parameters
        email_match = re.search(r'(?:to|send.*?to)\s+([\w\.-]+@[\w\.-]+)', text, re.IGNORECASE)
        subject_match = re.search(r"(?:subject|with subject)\s+['\"](.*?)['\"]", text, re.IGNORECASE)
        message_match = re.search(r"(?:message|saying|body)\s+['\"](.*?)['\"]", text, re.IGNORECASE)
        
        if email_match:
            return {
                "to": email_match.group(1),
                "subject": subject_match.group(1) if subject_match else "Message from AI Assistant",
                "message": message_match.group(1) if message_match else text
            }
    
    elif action_type == "whatsapp":
        # Extract WhatsApp parameters
        phone_match = re.search(r'(?:to|send.*?to)\s+(\+?[\d\s\-\(\)]+)', text, re.IGNORECASE)
        message_match = re.search(r"(?:saying|message)\s+['\"](.*?)['\"]", text, re.IGNORECASE)
        
        if phone_match:
            return {
                "to": phone_match.group(1).strip(),
                "message": message_match.group(1) if message_match else text
            }
    
    return None

async def save_task_to_db(task_data: Dict[str, Any], trace_id: str) -> Optional[str]:
    """Save task to database with trace_id"""
    try:
        from app.core.database import tasks_collection
        
        task_doc = {
            "trace_id": trace_id,
            "task_type": task_data.get('task_type', 'general'),
            "status": task_data.get('status', 'completed'),
            "execution": task_data.get('execution', {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = await tasks_collection.insert_one(task_doc)
        logger.info(f"[{trace_id}] Task saved to DB")
        return trace_id
    except Exception as e:
        logger.warning(f"[{trace_id}] Failed to save task to DB: {e}")
        return None

def log_to_bucket(trace_id: str, stage: str, data: Dict[str, Any]):
    """Log data to bucket with trace ID"""
    try:
        # Use synchronous logging for now
        bucket_service.log_event(trace_id, stage, data)
    except Exception as e:
        logger.error(f"Bucket logging failed for {trace_id}: {e}")

def call_safety_service(text: str, trace_id: str) -> Dict[str, Any]:
    """Call Aakansha's safety validation service"""
    result = safety_service.validate_content(
        content=text,
        trace_id=trace_id
    )
    log_to_bucket(trace_id, "safety_validation", result)
    return result

def call_intelligence_service(context: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
    """Call Sankalp's intelligence service"""
    result = intelligence_service.process_interaction(
        context=context,
        trace_id=trace_id
    )
    log_to_bucket(trace_id, "intelligence_processing", result)
    return result

def call_enforcement_service(payload: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
    """Call Raj's enforcement service"""
    result = enforcement_service.enforce_policy(
        payload=payload,
        trace_id=trace_id
    )
    log_to_bucket(trace_id, "enforcement_decision", result)
    return result




async def handle_assistant_request(request):
    """
    FULL SPINE WIRING - Central orchestrator for /api/assistant
    Calls: Safety → Intelligence → Enforcement → Orchestration → Execution
    Every step emits same trace_id and deterministic artifacts
    Enhanced with robust error handling and fail-closed behavior
    """
    
    # Generate trace ID for entire request chain
    trace_id = generate_trace_id()
    
    # Validate request structure first
    if not hasattr(request, 'input') or not hasattr(request, 'context'):
        return error_response(
            "INVALID_REQUEST_STRUCTURE",
            "Request must have input and context fields",
            trace_id
        )
    
    try:
        # -------------------------------
        # Input normalization & logging
        # -------------------------------
        
        # Handle audio input if provided (skip placeholder values from Swagger UI)
        audio_data = getattr(request.input, 'audio_data', None)
        if audio_data and isinstance(audio_data, bytes) and len(audio_data) > 0:
            # Convert speech to text using audio service
            try:
                text = audio_service.speech_to_text(
                    audio_data=audio_data,
                    language=request.context.preferred_language if request.context.preferred_language != "auto" else "en"
                )
                # Set voice input flag
                request.context.voice_input = True
            except Exception as e:
                logger.warning(f"[{trace_id}] Audio conversion failed: {str(e)}, falling back to message")
                # Fall back to message if audio fails
                text = getattr(request.input, 'message', None) or ""
        elif hasattr(request.input, 'message') and request.input.message:
            text = request.input.message
        elif (
            request.input.summarized_payload
            and "summary" in request.input.summarized_payload
        ):
            text = request.input.summarized_payload["summary"]
        else:
            return error_response(
                "INVALID_INPUT",
                "Either message or summarized_payload.summary or audio_data is required",
                trace_id
            )
        
        # Detect language if not already specified
        if not request.context.detected_language:
            language_metadata = multilingual_service.get_language_metadata(text)
            detected_language = language_metadata.get("detected_language", "en")
            request.context.detected_language = detected_language
        else:
            detected_language = request.context.detected_language
            language_metadata = multilingual_service.get_language_metadata(text)
        
        # Log initial request
        log_to_bucket(trace_id, "request_received", {
            "input_text": text,
            "detected_language": detected_language,
            "preferred_language": request.context.preferred_language,
            "context": request.context.dict() if hasattr(request.context, 'dict') else str(request.context),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # -------------------------------
        # STEP 1: SAFETY GATE (Aakansha)
        # -------------------------------
        logger.info(f"[{trace_id}] Calling Safety Service")
        safety_result = call_safety_service(text, trace_id)
        
        # If safety blocks, return immediately
        if safety_result.get("decision") == "hard_deny":
            log_to_bucket(trace_id, "request_blocked", {
                "reason": "safety_hard_deny",
                "safety_result": safety_result
            })
            return success_response(
                result_type="passive",
                response_text=CRISIS_SAFE_RESPONSE,
                enforcement={"decision": "BLOCK", "reason": "safety_hard_deny", "trace_id": trace_id},
                safety=safety_result,
                trace_id=trace_id
            )
        
        # -------------------------------
        # STEP 2: INTELLIGENCE (Sankalp)
        # -------------------------------
        logger.info(f"[{trace_id}] Calling Intelligence Service")
        intelligence_context = {
            "user_input": text,
            "platform": request.context.platform if hasattr(request.context, 'platform') else "web",
            "session_id": request.context.session_id if hasattr(request.context, 'session_id') else None
        }
        intelligence_result = call_intelligence_service(intelligence_context, trace_id)
        
        # -------------------------------
        # STEP 3: ENFORCEMENT (Raj)
        # -------------------------------
        logger.info(f"[{trace_id}] Calling Enforcement Service")
        enforcement_payload = {
            "safety": safety_result,
            "intelligence": intelligence_result,
            "user_input": text,
            "intent": "general",  # Will be enhanced later
            "trace_id": trace_id
        }
        enforcement_result = call_enforcement_service(enforcement_payload, trace_id)
        
        # Handle enforcement decisions
        if enforcement_result.get("decision") == "BLOCK":
            log_to_bucket(trace_id, "request_blocked", {
                "reason": "enforcement_block",
                "enforcement_result": enforcement_result
            })
            return success_response(
                result_type="passive",
                response_text=CRISIS_SAFE_RESPONSE,
                enforcement=enforcement_result,
                safety=safety_result,
                trace_id=trace_id
            )
        
        # -------------------------------
        # STEP 4: ORCHESTRATION (Nilesh)
        # -------------------------------
        logger.info(f"[{trace_id}] Processing through Orchestration")
        
        # Summary generation
        try:
            summary = summary_flow.generate_summary(text)
            processed_text = summary.get("summary", text) if summary else text
        except Exception as e:
            logger.warning(f"[{trace_id}] Summary generation failed: {e}. Using original text.")
            processed_text = text
        
        # Intent detection
        try:
            intent = intent_flow.process_text(processed_text)
            if not intent:
                intent = {"intent": "general"}
        except Exception as e:
            logger.warning(f"[{trace_id}] Intent detection failed: {e}. Using general intent.")
            intent = {"intent": "general"}
        
        log_to_bucket(trace_id, "orchestration_processing", {
            "processed_text": processed_text,
            "intent": intent,
            "enforcement_decision": enforcement_result.get("decision")
        })
        
        # -------------------------------
        # STEP 5: RESPONSE GENERATION & EXECUTION
        # -------------------------------
        execution_result = None
        
        if enforcement_result.get("decision") == "REWRITE":
            # Use safe rewritten response
            response_text = enforcement_result.get("rewritten_output", "I understand. Let me help you with that in a different way.")
            result_type = "passive"
        elif intent.get("intent") == "email" or "email" in text.lower():
            # Email execution path
            result_type = "workflow"
            action_data = extract_action_parameters(text, "email")
            
            if action_data:
                logger.info(f"[{trace_id}] Executing email action")
                execution_result = execution_service.execute_action(
                    action_type="email",
                    action_data=action_data,
                    trace_id=trace_id,
                    enforcement_decision=enforcement_result.get("decision", "ALLOW")
                )
                log_to_bucket(trace_id, "action_execution", execution_result)
                
                if execution_result.get("status") == "success":
                    response_text = "Successfully sent email message."
                    task = {"task_type": "email", "status": "completed", "execution": execution_result}
                    # Save task to database
                    saved_trace_id = await save_task_to_db(task, trace_id)
                    if saved_trace_id:
                        task["trace_id"] = saved_trace_id
                elif execution_result.get("status") == "error":
                    response_text = f"Failed to send email: {execution_result.get('error')}"
                    task = {"task_type": "email", "status": "failed", "error": execution_result.get('error')}
                else:
                    response_text = "Email action processed."
                    task = {"task_type": "email", "status": "processed"}
            else:
                response_text = "Could not extract email parameters from request."
                task = {"task_type": "email", "status": "failed", "error": "missing_parameters"}
                result_type = "passive"
        elif "whatsapp" in text.lower() or "send message" in text.lower():
            # WhatsApp execution path
            result_type = "workflow"
            action_data = extract_action_parameters(text, "whatsapp")
            
            if action_data:
                logger.info(f"[{trace_id}] Executing WhatsApp action")
                execution_result = execution_service.execute_action(
                    action_type="whatsapp",
                    action_data=action_data,
                    trace_id=trace_id,
                    enforcement_decision=enforcement_result.get("decision", "ALLOW")
                )
                log_to_bucket(trace_id, "action_execution", execution_result)
                
                if execution_result.get("status") == "success":
                    response_text = "Successfully sent WhatsApp message."
                    task = {"task_type": "whatsapp", "status": "completed", "execution": execution_result}
                    # Save task to database
                    saved_trace_id = await save_task_to_db(task, trace_id)
                    if saved_trace_id:
                        task["trace_id"] = saved_trace_id
                elif execution_result.get("status") == "error":
                    response_text = f"Failed to send WhatsApp: {execution_result.get('error')}"
                    task = {"task_type": "whatsapp", "status": "failed", "error": execution_result.get('error')}
                else:
                    response_text = "WhatsApp action processed."
                    task = {"task_type": "whatsapp", "status": "processed"}
            else:
                response_text = "Could not extract WhatsApp parameters from request."
                task = {"task_type": "whatsapp", "status": "failed", "error": "missing_parameters"}
                result_type = "passive"
        elif intent.get("intent") == "general":
            # Generate normal response
            response_text = decision_hub.simple_response(processed_text)
            result_type = "passive"
        else:
            # Task/workflow path
            try:
                task = task_flow.build_task(intent)
                response_text = "Task processed successfully"
                result_type = "workflow"
            except Exception as e:
                logger.warning(f"[{trace_id}] Task building failed: {e}. Using default response.")
                response_text = decision_hub.simple_response(processed_text)
                result_type = "passive"
                task = None
        
        # -------------------------------
        # FINAL RESPONSE & LOGGING
        # -------------------------------
        
        # Prepare audio response if requested
        audio_response = None
        if request.context.audio_output_requested:
            try:
                target_language = request.context.preferred_language if request.context.preferred_language != "auto" else detected_language
                audio_response = audio_service.text_to_speech(response_text, language=target_language)
            except Exception as e:
                logger.warning(f"[{trace_id}] Audio generation failed: {str(e)}, continuing without audio")
                # Don't fail the entire request if audio generation fails, just continue without audio
        
        final_response = success_response(
            result_type=result_type,
            response_text=response_text,
            task=task if 'task' in locals() else None,
            enforcement=enforcement_result,
            safety=safety_result,
            execution=execution_result,
            trace_id=trace_id,
            language_metadata=language_metadata,
            audio_response=audio_response
        )
        
        log_to_bucket(trace_id, "response_generated", {
            "final_response": final_response,
            "chain_complete": True
        })
        
        logger.info(f"[{trace_id}] Request processing complete")
        return final_response
        
    except Exception as e:
        # Log the actual error for debugging
        error_trace = traceback.format_exc()
        logger.error(f"[{trace_id}] Error processing assistant request: {e}\n{error_trace}")
        
        log_to_bucket(trace_id, "error_occurred", {
            "error": str(e),
            "traceback": error_trace
        })
        
        return error_response(
            "INTERNAL_ERROR",
            f"Unable to process request: {str(e)}",
            trace_id
        )


# ==============================
# Response helpers (LOCKED)
# ==============================

def success_response(result_type, response_text, task=None, enforcement=None, safety=None, execution=None, trace_id=None, language_metadata=None, audio_response=None):
    response = {
        "version": "3.0.0",
        "status": "success",
        "result": {
            "type": result_type,
            "response": response_text,
            "task": task,
            "enforcement": enforcement,
            "safety": safety,
            "execution": execution,
        },
        "processed_at": datetime.utcnow().isoformat() + "Z",
        "trace_id": trace_id,
    }
    
    # Add language metadata if provided
    if language_metadata:
        response["result"]["language_metadata"] = language_metadata
    
    # Add audio response if provided
    if audio_response:
        response["result"]["audio_response"] = audio_response
    
    return response


def error_response(code, message, trace_id=None):
    return {
        "version": "3.0.0",
        "status": "error",
        "error": {
            "code": code,
            "message": message,
        },
        "processed_at": datetime.utcnow().isoformat() + "Z",
        "trace_id": trace_id,
    }

# Fixed audio_data handling for Swagger UI compatibility
