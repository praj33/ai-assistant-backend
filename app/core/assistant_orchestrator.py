from datetime import datetime
import hashlib
import traceback
from typing import Dict, Any, Optional
from types import SimpleNamespace

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
from app.external.enforcement.deterministic_trace import (
    generate_trace_id as generate_deterministic_trace_id,
)

logger = get_logger(__name__)

CRISIS_SAFE_RESPONSE = (
    "I'm really glad you shared this. I can't help with harming yourself, "
    "but I want you to have immediate support right now. "
    "If you're in immediate danger, call emergency services now. "
    "In India, call 112 for emergency services or contact AASRA at 9820466726. "
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

def _to_namespace(value):
    if isinstance(value, dict):
        return SimpleNamespace(**{k: _to_namespace(v) for k, v in value.items()})
    if isinstance(value, list):
        return [_to_namespace(v) for v in value]
    return value


def _to_plain(value):
    if isinstance(value, SimpleNamespace):
        return {
            k: _to_plain(v)
            for k, v in value.__dict__.items()
            if k != "dict"
        }
    if isinstance(value, dict):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_plain(v) for v in value]
    return value


def _normalize_request(request):
    """
    Accept both Pydantic-style request objects and raw dict payloads.
    Webhooks and many verification tests pass dicts; the orchestrator must
    still enforce the full pipeline deterministically.
    """
    if not isinstance(request, dict):
        return request

    req = SimpleNamespace()
    req.input = _to_namespace(request.get("input") or {})
    req.context = _to_namespace(request.get("context") or {})

    # Ensure expected fields exist (fail-closed logic later relies on presence).
    if not hasattr(req.input, "message"):
        req.input.message = None
    if not hasattr(req.input, "summarized_payload"):
        req.input.summarized_payload = None
    if not hasattr(req.input, "audio_data"):
        req.input.audio_data = None

    defaults = {
        "platform": "web",
        "device": "unknown",
        "session_id": None,
        "voice_input": False,
        "preferred_language": "auto",
        "detected_language": None,
        "audio_output_requested": False,
        "age_gate_status": False,
        "region_policy": None,
        "platform_policy": None,
        "user_context": None,
        "authenticated_user_context": None,
    }
    for k, v in defaults.items():
        if not hasattr(req.context, k):
            setattr(req.context, k, v)

    # Provide .dict() for logging compatibility
    if not hasattr(req.context, "dict"):
        req.context.dict = lambda: {
            k: _to_plain(getattr(req.context, k))
            for k in req.context.__dict__.keys()
            if k != "dict"
        }

    return req


def _build_authenticated_user_context(context) -> Dict[str, Any]:
    raw_context = getattr(context, "authenticated_user_context", None)
    if raw_context is None:
        raw_context = getattr(context, "user_context", None)

    user_context = _to_plain(raw_context) if raw_context is not None else {}
    if not isinstance(user_context, dict):
        user_context = {"principal": str(user_context)}

    if getattr(context, "session_id", None) and "session_id" not in user_context:
        user_context["session_id"] = context.session_id
    if getattr(context, "platform", None) and "platform" not in user_context:
        user_context["platform"] = context.platform
    if getattr(context, "device", None) and "device" not in user_context:
        user_context["device"] = context.device

    return user_context


def _build_platform_policy(context, authenticated_user_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    raw_policy = getattr(context, "platform_policy", None)
    platform_policy = _to_plain(raw_policy) if raw_policy is not None else {}
    if platform_policy and not isinstance(platform_policy, dict):
        platform_policy = {"platform_policy": platform_policy}
    if not platform_policy:
        platform_policy = {}

    if getattr(context, "platform", None):
        platform_policy.setdefault("platform", context.platform)
    if getattr(context, "device", None):
        platform_policy.setdefault("device", context.device)
    if authenticated_user_context:
        platform_policy["authenticated_user_context"] = authenticated_user_context

    return platform_policy or None

def _audio_fingerprint(audio_data: Any) -> Optional[str]:
    if isinstance(audio_data, (bytes, bytearray)) and audio_data:
        return hashlib.sha256(audio_data).hexdigest()
    return None


def _canonical_request_trace_payload(
    *,
    request: Any,
    authenticated_user_context: Dict[str, Any],
    platform_policy: Optional[Dict[str, Any]],
    audio_fingerprint: Optional[str],
) -> Dict[str, Any]:
    input_payload = getattr(request, "input", SimpleNamespace())
    context = getattr(request, "context", SimpleNamespace())

    summarized_payload = _to_plain(getattr(input_payload, "summarized_payload", None))
    region_policy = _to_plain(getattr(context, "region_policy", None))

    return {
        "version": getattr(request, "version", "3.0.0") or "3.0.0",
        "input": {
            "message": getattr(input_payload, "message", None) or "",
            "summarized_payload": summarized_payload if summarized_payload else None,
            "audio_fingerprint": audio_fingerprint,
        },
        "context": {
            "platform": getattr(context, "platform", None) or "web",
            "device": getattr(context, "device", None) or "unknown",
            "session_id": getattr(context, "session_id", None) or "",
            "voice_input": bool(getattr(context, "voice_input", False)),
            "preferred_language": getattr(context, "preferred_language", None) or "auto",
            "age_gate_status": bool(getattr(context, "age_gate_status", False)),
            "region_policy": region_policy,
            "platform_policy": platform_policy or {},
            "authenticated_user_context": authenticated_user_context or {},
        },
    }


def generate_trace_id(canonical_payload: Dict[str, Any]) -> str:
    """Generate a deterministic request trace from the canonical runtime payload."""
    return generate_deterministic_trace_id(
        input_payload=canonical_payload,
        enforcement_category="REQUEST",
    )

def extract_action_parameters(text: str, action_type: str) -> Dict[str, Any]:
    """Extract action parameters from user text for all supported platforms"""
    import re
    
    if action_type == "email":
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
        phone_match = re.search(r'(\+?\d[\d\s\-\(\)]{7,}\d)', text)
        message_match = re.search(r"""(?:saying|message)\s+['"](.*?)['"]""", text, re.IGNORECASE)
        if not message_match:
            message_match = re.search(r'(?:saying|message)\s+(.+?)$', text, re.IGNORECASE)
        if phone_match:
            return {
                "to": phone_match.group(1).strip(),
                "message": message_match.group(1).strip() if message_match else text
            }
    
    elif action_type == "telegram":
        # Extract @username or chat_id
        username_match = re.search(r'(?:to|@)\s*(@?[\w]+)', text, re.IGNORECASE)
        message_match = re.search(r"(?:saying|message)\s+['\"](.*?)['\"]", text, re.IGNORECASE)
        if not message_match:
            message_match = re.search(r'(?:saying|message)\s+(.+?)$', text, re.IGNORECASE)
        if username_match:
            return {
                "to": username_match.group(1).strip(),
                "message": message_match.group(1).strip() if message_match else text
            }
    
    elif action_type == "calendar":
        # Extract event details
        title_match = re.search(r'(?:called|titled|named)\s+[\'\"](.*?)[\'\"]', text, re.IGNORECASE)
        if not title_match:
            title_match = re.search(r'(?:called|titled|named)\s+(.+?)(?:\s+(?:at|on|for|tomorrow)|$)', text, re.IGNORECASE)
        time_match = re.search(r'(?:at|from)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)', text, re.IGNORECASE)
        date_match = re.search(r'(?:on|for)\s+(tomorrow|today|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text, re.IGNORECASE)
        
        title = title_match.group(1).strip() if title_match else "New Event"
        start_time = datetime.utcnow().isoformat()
        return {
            "action": "create_event",
            "title": title,
            "start_time": start_time,
            "description": text
        }
    
    elif action_type == "reminder":
        message_match = re.search(r'(?:remind.*?to|reminder.*?to|remind.*?about)\s+(.+?)(?:\s+(?:at|in|tomorrow)|$)', text, re.IGNORECASE)
        time_match = re.search(r'(?:at|in)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)', text, re.IGNORECASE)
        return {
            "action": "create_reminder",
            "message": message_match.group(1).strip() if message_match else text,
            "remind_at": None
        }
    
    elif action_type == "ems":
        title_match = re.search(r'(?:task|create task)\s+[\'\"](.*?)[\'\"]', text, re.IGNORECASE)
        if not title_match:
            title_match = re.search(r'(?:task|create task)\s+(.+?)(?:\s+(?:assign|priority|for)|$)', text, re.IGNORECASE)
        assignee_match = re.search(r'(?:assign.*?to|for)\s+([\w\s]+?)(?:\s+(?:with|priority)|$)', text, re.IGNORECASE)
        priority_match = re.search(r'(?:priority)\s+(high|medium|low)', text, re.IGNORECASE)
        return {
            "action": "create_task",
            "title": title_match.group(1).strip() if title_match else "New Task",
            "assignee": assignee_match.group(1).strip() if assignee_match else "",
            "priority": priority_match.group(1).lower() if priority_match else "medium",
            "description": text
        }
    
    return None


def _detect_platform(text_lower: str, intent: Dict[str, Any]) -> str:
    """Detect which platform to route to based on user input text."""
    # Check explicit platform keywords (order matters — more specific first)
    if "telegram" in text_lower:
        return "telegram"
    if "whatsapp" in text_lower:
        return "whatsapp"
    if "instagram" in text_lower or "insta " in text_lower:
        return "instagram"
    if "email" in text_lower or "mail" in text_lower:
        return "email"
    if any(kw in text_lower for kw in ["calendar", "schedule", "meeting", "appointment", "event"]):
        return "calendar"
    if any(kw in text_lower for kw in ["remind", "reminder", "alert me"]):
        return "reminder"
    if any(kw in text_lower for kw in ["ems task", "create task", "assign task"]):
        return "ems"
    if any(kw in text_lower for kw in ["device", "desktop", "mobile", "tablet", "xr"]):
        return "device_gateway"
    
    # Fall back to intent classification
    intent_name = intent.get("intent", "general")
    if intent_name in ["email", "calendar", "reminder"]:
        return intent_name
    
    return "general"


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

def call_safety_service(text: str, trace_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Call Aakansha's safety validation service"""
    result = safety_service.validate_content(
        content=text,
        trace_id=trace_id,
        context=context,
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
    request = _normalize_request(request)

    # Validate request structure first
    if not hasattr(request, 'input') or not hasattr(request, 'context'):
        trace_id = generate_trace_id({"invalid_request": _to_plain(request)})
        return error_response(
            "INVALID_REQUEST_STRUCTURE",
            "Request must have input and context fields",
            trace_id
        )

    authenticated_user_context = _build_authenticated_user_context(request.context)
    platform_policy = _build_platform_policy(request.context, authenticated_user_context)
    trace_id = generate_trace_id(
        _canonical_request_trace_payload(
            request=request,
            authenticated_user_context=authenticated_user_context,
            platform_policy=platform_policy,
            audio_fingerprint=_audio_fingerprint(getattr(request.input, "audio_data", None)),
        )
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
        safety_context = {
            "age_gate_status": bool(getattr(request.context, "age_gate_status", False)),
            "region_rule_status": getattr(request.context, "region_policy", None),
            "platform_policy_state": platform_policy,
        }
        
        # -------------------------------
        # STEP 1: SAFETY GATE (Aakansha)
        # -------------------------------
        logger.info(f"[{trace_id}] Calling Safety Service")
        safety_result = call_safety_service(text, trace_id, safety_context)
        
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
        raw_risk_flags = intelligence_result.get("risk_flags", [])
        if isinstance(raw_risk_flags, str):
            raw_risk_flags = [raw_risk_flags]
        elif not isinstance(raw_risk_flags, list):
            raw_risk_flags = [raw_risk_flags] if raw_risk_flags else []

        raw_karma_score = intelligence_result.get("karma_score")
        karma_score = int(raw_karma_score) if isinstance(raw_karma_score, (int, float)) else 50

        enforcement_payload = {
            "safety": safety_result,
            "intelligence": intelligence_result,
            "user_input": text,
            "emotional_output": text,
            "intent": intelligence_result.get("intent") or "general",
            "trace_id": trace_id,
            "age_gate_status": bool(getattr(request.context, "age_gate_status", False)),
            "region_policy": getattr(request.context, "region_policy", None),
            "platform_policy": platform_policy,
            "karma_score": karma_score,
            "risk_flags": raw_risk_flags,
            "authenticated_user_context": authenticated_user_context,
            "user_context": authenticated_user_context,
        }
        enforcement_result = call_enforcement_service(enforcement_payload, trace_id)
        
        # Handle enforcement decisions
        if enforcement_result.get("decision") == "TERMINATE":
            log_to_bucket(trace_id, "request_terminated", {
                "reason": "enforcement_terminate",
                "enforcement_result": enforcement_result
            })
            return terminated_response(
                enforcement=enforcement_result,
                trace_id=trace_id,
            )

        if enforcement_result.get("decision") == "BLOCK":
            log_to_bucket(trace_id, "request_blocked", {
                "reason": "enforcement_block",
                "enforcement_result": enforcement_result
            })
            return success_response(
                result_type="passive",
                response_text=(
                    CRISIS_SAFE_RESPONSE
                    if safety_result.get("decision") == "hard_deny"
                    else safety_result.get("safe_output") or CRISIS_SAFE_RESPONSE
                ),
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
        
        # ─── Detect platform from text ───
        text_lower = text.lower()
        detected_platform = _detect_platform(text_lower, intent)
        
        if enforcement_result.get("decision") == "REWRITE":
            response_text = (
                enforcement_result.get("safe_output")
                or enforcement_result.get("rewritten_output")
                or safety_result.get("safe_output")
                or "I understand. Let me help you with that in a different way."
            )
            result_type = "passive"
        
        elif detected_platform in ["whatsapp", "email", "telegram", "instagram",
                                     "calendar", "reminder", "ems", "device_gateway"]:
            # ─── UNIVERSAL EXECUTION PATH ───
            result_type = "workflow"
            action_data = extract_action_parameters(text, detected_platform)
            
            if action_data:
                logger.info(f"[{trace_id}] Executing {detected_platform} action")
                execution_result = execution_service.execute_action(
                    action_type=detected_platform,
                    action_data=action_data,
                    trace_id=trace_id,
                    enforcement_decision=enforcement_result
                )
                log_to_bucket(trace_id, "action_execution", execution_result)
                
                platform_labels = {
                    "whatsapp": "WhatsApp message",
                    "email": "email message",
                    "telegram": "Telegram message",
                    "instagram": "Instagram message",
                    "calendar": "calendar event",
                    "reminder": "reminder",
                    "ems": "EMS task",
                    "device_gateway": "device command"
                }
                label = platform_labels.get(detected_platform, detected_platform)
                
                if execution_result.get("status") == "success":
                    response_text = f"Successfully processed {label}."
                    task = {"task_type": detected_platform, "status": "completed", "execution": execution_result}
                    saved_trace_id = await save_task_to_db(task, trace_id)
                    if saved_trace_id:
                        task["trace_id"] = saved_trace_id
                elif execution_result.get("status") == "error":
                    response_text = f"Failed to process {label}: {execution_result.get('error')}"
                    task = {"task_type": detected_platform, "status": "failed", "error": execution_result.get('error')}
                else:
                    response_text = f"{label.capitalize()} action processed."
                    task = {"task_type": detected_platform, "status": "processed"}
            else:
                response_text = f"Could not extract {detected_platform} parameters from request."
                task = {"task_type": detected_platform, "status": "failed", "error": "missing_parameters"}
                result_type = "passive"
        
        elif intent.get("intent") == "general":
            response_text = decision_hub.simple_response(processed_text)
            result_type = "passive"
        else:
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


def terminated_response(enforcement: Dict[str, Any], trace_id: str):
    return {
        "version": "3.0.0",
        "status": "error",
        "error": {
            "code": "ENFORCEMENT_TERMINATED",
            "message": "Request terminated by enforcement runtime.",
            "enforcement": enforcement,
        },
        "processed_at": datetime.utcnow().isoformat() + "Z",
        "trace_id": trace_id,
    }

# Fixed audio_data handling for Swagger UI compatibility
