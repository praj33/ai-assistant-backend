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
from app.api.webhooks import router as webhook_router

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
# CORS - Allow all origins (frontend is a separate project)
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
            cors_origin = origin if origin else "*"
            
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication failed"},
                headers={
                    "Access-Control-Allow-Origin": cors_origin,
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
app.include_router(webhook_router)

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
