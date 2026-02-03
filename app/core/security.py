import os
import logging
import time
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

from fastapi import HTTPException, Depends, Request
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

# Environment variables
API_KEY = os.getenv("API_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

# Rate limiting store (in-memory)
# NOTE: For production with multiple instances, use Redis or similar distributed store
rate_limit_store = defaultdict(list)

# Import structured logger
from .logging import get_logger
logger = get_logger(__name__)

class TokenData(BaseModel):
    username: Optional[str] = None

def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    if not api_key or api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> TokenData:
    if not credentials:
        raise HTTPException(status_code=401, detail="Token not provided")
    return verify_token_string(credentials.credentials)

def verify_token_string(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        token_data = TokenData(username=username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token_data

def authenticate_user(api_key: str = Depends(api_key_header), token: TokenData = Depends(verify_token)) -> str:
    if api_key and api_key == API_KEY:
        return "api_key_user"
    if token.username:
        return token.username
    raise HTTPException(status_code=401, detail="Authentication failed")

def rate_limit(request: Request, max_requests: int = 100, window_seconds: int = 60):
    # Handle cases where client info might be missing
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    # Clean old entries
    rate_limit_store[client_ip] = [t for t in rate_limit_store[client_ip] if current_time - t < window_seconds]
    if len(rate_limit_store[client_ip]) >= max_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    rate_limit_store[client_ip].append(current_time)

def audit_log(request: Request, user: str = None):
    """Log security events using structured logging"""
    try:
        logger.info("Security audit event", extra={
            "user": user or "anonymous",
            "method": request.method,
            "endpoint": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "event_type": "api_access"
        })
    except Exception as e:
        # Don't fail the request if logging fails
        print(f"Audit logging error: {e}")