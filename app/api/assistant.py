from fastapi import APIRouter, Header, Request
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, Literal, Union
from datetime import datetime
import os

from app.core.assistant_orchestrator import handle_assistant_request

router = APIRouter()

# =========================
# REQUEST SCHEMAS (LOCKED)
# =========================

class AssistantInput(BaseModel):
    message: Optional[str] = None
    summarized_payload: Optional[dict] = None
    audio_data: Optional[bytes] = None
    audio_format: Optional[str] = "mp3"


class AssistantContext(BaseModel):
    platform: str = "web"
    device: str = "desktop"
    session_id: Optional[str] = None
    voice_input: bool = False
    preferred_language: Optional[str] = "auto"
    detected_language: Optional[str] = None
    audio_input_data: Optional[bytes] = None
    audio_output_requested: bool = False


class AssistantRequest(BaseModel):
    version: Literal["3.0.0"]
    input: AssistantInput
    context: AssistantContext


# =========================
# RESPONSE SCHEMAS (LOCKED)
# =========================

class AssistantResult(BaseModel):
    type: Literal["passive", "intelligence", "workflow"]
    response: str
    task: Optional[dict] = None
    enforcement: Optional[dict] = None
    safety: Optional[dict] = None
    language_metadata: Optional[dict] = None
    audio_response: Optional[bytes] = None


class AssistantSuccessResponse(BaseModel):
    version: Literal["3.0.0"]
    status: Literal["success"]
    result: AssistantResult
    processed_at: str


class AssistantErrorResponse(BaseModel):
    version: Literal["3.0.0"]
    status: Literal["error"]
    error: dict
    processed_at: str


# =========================
# SINGLE PUBLIC ENDPOINT
# =========================

@router.options("/api/assistant")
async def assistant_options(request: Request):
    """
    Handle CORS preflight requests for /api/assistant.
    This explicit handler prevents FastAPI from trying to validate OPTIONS requests
    against the POST route handler which requires headers and body.
    """
    # Get allowed origins (same logic as main.py)
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        allowed_origins.append(frontend_url)
        if frontend_url.startswith("https://"):
            allowed_origins.append(frontend_url.replace("https://", "http://"))
        elif frontend_url.startswith("http://"):
            allowed_origins.append(frontend_url.replace("http://", "https://"))
    
    # Add common Render.com frontend URLs (for production deployments)
    render_frontends = [
        "https://ai-assistant-yykb.onrender.com",
        "https://ai-assistant-frontend.onrender.com",
    ]
    allowed_origins.extend(render_frontends)
    
    origin = request.headers.get("origin", "")
    
    # Check if origin is allowed (only ai-assistant Render.com subdomains)
    is_allowed = False
    if origin:
        import re
        # Check explicit list
        if origin in allowed_origins:
            is_allowed = True
        # Allow only ai-assistant Render.com subdomains
        elif re.match(r"https://ai-assistant[-\w]*\.onrender\.com$", origin):
            is_allowed = True
    
    # Determine allowed origin
    if is_allowed and origin:
        allowed_origin = origin
    elif allowed_origins:
        allowed_origin = allowed_origins[0]
    else:
        allowed_origin = "*"
    
    # Return 200 OK with CORS headers for preflight
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-API-Key, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        }
    )

@router.post(
    "/api/assistant",
    response_model=Union[AssistantSuccessResponse, AssistantErrorResponse]
)
async def assistant_endpoint(
    request: AssistantRequest,
    x_api_key: str = Header(...)
):
    """
    SINGLE production entrypoint for AI Assistant.
    Backend is LOCKED and frontend-safe.
    """
    try:
        return await handle_assistant_request(request)
    except Exception as e:
        # Final safety net - catch any unhandled exceptions
        import traceback
        from datetime import datetime
        error_trace = traceback.format_exc()
        print(f"Unhandled exception in assistant endpoint: {e}\n{error_trace}")
        
        # Return error response in expected format
        return {
            "version": "3.0.0",
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while processing your request."
            },
            "processed_at": datetime.utcnow().isoformat() + "Z",
        }
