import sys
import os
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv

# -------------------------------------------------
# Path setup
# -------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

# -------------------------------------------------
# Load environment variables
# -------------------------------------------------
load_dotenv()  # Load from current directory

# -------------------------------------------------
# Optional Sentry
# -------------------------------------------------
if os.getenv("SENTRY_DSN"):
    import sentry_sdk
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        environment=os.getenv("ENV", "production"),
    )

# -------------------------------------------------
# Local imports
# -------------------------------------------------
from app.core.logging import setup_logging, get_logger
from app.core.database import create_tables
from app.core.security import rate_limit, audit_log
from app.api.assistant import router as assistant_router

# -------------------------------------------------
# Logging
# -------------------------------------------------
setup_logging()
logger = get_logger(__name__)

# -------------------------------------------------
# App lifespan
# -------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    try:
        await create_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        # Don't fail startup if database is read-only - app can still run
        # but database features won't work
        logger.warning("Continuing startup without database initialization")
    yield

# -------------------------------------------------
# FastAPI app
# -------------------------------------------------
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

app = FastAPI(
    title="AI Assistant Backend",
    description="Production-locked Assistant Backend",
    version="3.0.0",
    lifespan=lifespan,
)

# -------------------------------------------------
# CORS
# -------------------------------------------------
# Note: Cannot use allow_origins=["*"] with allow_credentials=True
# Must specify exact origins for localhost development and production
# Support production frontend URL via environment variable

# Base allowed origins for localhost development
base_allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

# Add production frontend URL from environment variable if set
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    base_allowed_origins.append(frontend_url)
    # Also add without protocol if needed
    if frontend_url.startswith("https://"):
        base_allowed_origins.append(frontend_url.replace("https://", "http://"))
    elif frontend_url.startswith("http://"):
        base_allowed_origins.append(frontend_url.replace("http://", "https://"))

# Add known Render.com frontend URLs
known_render_origins = [
    "https://ai-assistant-yykb.onrender.com",
    "https://ai-assistant-frontend.onrender.com",
]
base_allowed_origins.extend(known_render_origins)

# Function to check if origin is allowed (supports dynamic checking)
def is_origin_allowed(origin: str) -> bool:
    """Check if an origin is allowed, including Render.com subdomains"""
    if not origin:
        return False
    
    # Check against explicit list
    if origin in base_allowed_origins:
        return True
    
    # Allow ai-assistant Render.com subdomains (for production deployments)
    import re
    if re.match(r"https://ai-assistant[-\w]*\.onrender\.com$", origin):
        return True
    
    return False

# Combine explicit origins and Render.com pattern
# FastAPI CORSMiddleware supports allow_origin_regex OR allow_origins, not both
# So we'll use allow_origins with a function approach via allow_origin_regex pattern
# Pattern matches: localhost, 127.0.0.1, and all Render.com subdomains
# Only allow ai-assistant-related Render.com subdomains, not ALL onrender.com subdomains
cors_regex_pattern = r"(http://localhost:\d+|http://127\.0\.0\.1:\d+|https://ai-assistant[-\w]*\.onrender\.com)"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=cors_regex_pattern,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# -------------------------------------------------
# Security Middleware
# -------------------------------------------------
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Allow health check and root without auth
    if request.url.path in ["/health", "/"]:
        response = await call_next(request)
        return response

    # Allow OPTIONS requests (CORS preflight) without auth
    # CORS middleware handles OPTIONS, but we need to ensure it passes through
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response

    if request.url.path.startswith("/api"):
        from fastapi import HTTPException
        try:
            rate_limit(request)
        except HTTPException as e:
            if e.status_code == 429:
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
            logger.warning(f"Rate limit check failed: {e}. Allowing request.")
        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}. Allowing request.")
        
        api_key = request.headers.get("X-API-Key")
        expected_api_key = os.getenv("API_KEY")
        
        # Check API key (handle None cases gracefully)
        if not expected_api_key:
            logger.error("API_KEY environment variable is not set! Authentication will fail.")
        if not api_key or api_key != expected_api_key:
            # Get origin from request for CORS headers
            origin = request.headers.get("origin", "")
            # Return JSON response with CORS headers manually added
            # Determine CORS origin for error response
            # Check if origin matches allowed pattern (localhost, 127.0.0.1, or render.com)
            cors_origin = "*"
            if origin:
                import re
                cors_pattern = r"(http://localhost:\d+|http://127\.0\.0\.1:\d+|https://ai-assistant[-\w]*\.onrender\.com)"
                if re.match(cors_pattern, origin):
                    cors_origin = origin
                elif origin in base_allowed_origins:
                    cors_origin = origin
                elif base_allowed_origins:
                    cors_origin = base_allowed_origins[0]
            
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication failed"},
                headers={
                    "Access-Control-Allow-Origin": cors_origin,
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                }
            )

        try:
            audit_log(request, "api_key_user")
        except Exception as e:
            logger.warning(f"Audit logging failed: {e}. Continuing with request.")

    response = await call_next(request)
    return response

# -------------------------------------------------
# ONLY PUBLIC ROUTER (LOCKED)
# -------------------------------------------------
app.include_router(assistant_router)

# -------------------------------------------------
# System Endpoints
# -------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "AI Assistant Backend API v3.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "assistant": "/api/assistant"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "3.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
