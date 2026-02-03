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

# Import integrated services
from app.services.safety_service import SafetyService
from app.services.intelligence_service import IntelligenceService
from app.services.enforcement_service import EnforcementService
from app.services.bucket_service import BucketService
from app.services.execution_service import ExecutionService

logger = get_logger(__name__)

# Initialize services
safety_service = SafetyService()
intelligence_service = IntelligenceService()
enforcement_service = EnforcementService()
bucket_service = BucketService()
execution_service = ExecutionService()

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
    """
    
    # Generate trace ID for entire request chain
    trace_id = generate_trace_id()
    
    try:
        # -------------------------------
        # Input normalization & logging
        # -------------------------------
        if request.input.message:
            text = request.input.message
        elif (
            request.input.summarized_payload
            and "summary" in request.input.summarized_payload
        ):
            text = request.input.summarized_payload["summary"]
        else:
            return error_response(
                "INVALID_INPUT",
                "Either message or summarized_payload.summary is required",
                trace_id
            )
        
        # Log initial request
        log_to_bucket(trace_id, "request_received", {
            "input_text": text,
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
                response_text="I can't assist with that request. Let's talk about something else.",
                enforcement={"decision": "block", "reason": "safety_violation", "trace_id": trace_id},
                safety=safety_result,
                trace_id=trace_id
            )
        
        # -------------------------------
        # STEP 2: INTELLIGENCE (Sankalp)
        # -------------------------------
        logger.info(f"[{trace_id}] Calling Intelligence Service")
        intelligence_context = {
            "user_input": text,
            "safety_result": safety_result,
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
                response_text="Action blocked by enforcement policy.",
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
            response_text = safety_result.get("safe_output", "I understand. Let me help you with that in a different way.")
            result_type = "passive"
        elif intent.get("intent") == "general":
            # Generate normal response
            response_text = decision_hub.simple_response(processed_text)
            result_type = "passive"
        else:
            # Task/workflow path with potential execution
            try:
                task = task_flow.build_task(intent)
                task_type = task.get("task_type") if task else "general_task"
                response_text = "Task processed successfully"
                result_type = "workflow"
                
                # Check if task requires execution (WhatsApp/Email)
                if task and task.get("task_type") in ["email", "whatsapp"]:
                    action_type = task.get("task_type")
                    
                    # Extract action parameters from original text
                    action_data = extract_action_parameters(text, action_type)
                    
                    if action_data:
                        logger.info(f"[{trace_id}] Executing {action_type} action")
                        execution_result = execution_service.execute_action(
                            action_type=action_type,
                            action_data=action_data,
                            trace_id=trace_id,
                            enforcement_decision=enforcement_result.get("decision", "ALLOW")
                        )
                        log_to_bucket(trace_id, "action_execution", execution_result)
                        
                        # Update response based on execution result
                        if execution_result.get("status") == "success":
                            response_text = f"Successfully sent {action_type} message."
                        elif execution_result.get("status") == "error":
                            if "credentials not configured" in execution_result.get("error", ""):
                                response_text = f"Demo: {action_type.title()} message would be sent (credentials not configured)."
                            else:
                                response_text = f"Failed to execute {action_type} action: {execution_result.get('error')}"
                        elif execution_result.get("status") == "blocked":
                            response_text = "Action was blocked by enforcement policy."
                        else:
                            response_text = f"Demo: {action_type.title()} message processed."
                    else:
                        response_text = f"Could not extract {action_type} parameters from request."
                
                # Direct email/whatsapp detection bypass
                elif "email" in text.lower() or "mailto:" in text.lower():
                    action_data = extract_action_parameters(text, "email")
                    if action_data:
                        logger.info(f"[{trace_id}] Direct email execution detected")
                        execution_result = execution_service.execute_action(
                            action_type="email",
                            action_data=action_data,
                            trace_id=trace_id,
                            enforcement_decision=enforcement_result.get("decision", "ALLOW")
                        )
                        log_to_bucket(trace_id, "action_execution", execution_result)
                        
                        if execution_result.get("status") == "success":
                            response_text = "Successfully sent email message."
                        elif execution_result.get("status") == "error":
                            if "credentials not configured" in execution_result.get("error", ""):
                                response_text = "Demo: Email message would be sent (credentials not configured)."
                            else:
                                response_text = f"Failed to execute email action: {execution_result.get('error')}"
                        else:
                            response_text = "Demo: Email message processed."
                
                elif "whatsapp" in text.lower() or "send message" in text.lower():
                    action_data = extract_action_parameters(text, "whatsapp")
                    if action_data:
                        logger.info(f"[{trace_id}] Direct WhatsApp execution detected")
                        execution_result = execution_service.execute_action(
                            action_type="whatsapp",
                            action_data=action_data,
                            trace_id=trace_id,
                            enforcement_decision=enforcement_result.get("decision", "ALLOW")
                        )
                        log_to_bucket(trace_id, "action_execution", execution_result)
                        
                        if execution_result.get("status") == "success":
                            response_text = "Successfully sent WhatsApp message."
                        elif execution_result.get("status") == "error":
                            if "credentials not configured" in execution_result.get("error", ""):
                                response_text = "Demo: WhatsApp message would be sent (credentials not configured)."
                            else:
                                response_text = f"Failed to execute WhatsApp action: {execution_result.get('error')}"
                        else:
                            response_text = "Demo: WhatsApp message processed."
                            
            except Exception as e:
                logger.warning(f"[{trace_id}] Task building failed: {e}. Using default response.")
                response_text = decision_hub.simple_response(processed_text)
                result_type = "passive"
                task = None
        
        # -------------------------------
        # FINAL RESPONSE & LOGGING
        # -------------------------------
        final_response = success_response(
            result_type=result_type,
            response_text=response_text,
            task=task if 'task' in locals() else None,
            enforcement=enforcement_result,
            safety=safety_result,
            execution=execution_result,
            trace_id=trace_id
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

def success_response(result_type, response_text, task=None, enforcement=None, safety=None, execution=None, trace_id=None):
    return {
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
