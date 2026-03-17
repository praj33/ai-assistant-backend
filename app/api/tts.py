"""
TTS API — Dedicated Text-to-Speech Endpoint for Mitra AI

Provides a direct TTS endpoint for frontend voice playback
and TTS engine health monitoring.
"""

import base64
from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.mitra_system_registry import mitra_registry

router = APIRouter()

audio_service = mitra_registry.audio_service


# =========================
# REQUEST / RESPONSE SCHEMAS
# =========================

class TTSRequest(BaseModel):
    text: str
    language: str = "en"


class TTSResponse(BaseModel):
    status: str
    audio_base64: Optional[str] = None
    audio_format: str = "wav"
    language: str = "en"
    text_length: int = 0
    audio_size_bytes: int = 0
    processed_at: str


# =========================
# ENDPOINTS
# =========================

@router.post("/api/tts", response_model=TTSResponse)
async def generate_tts(
    request: TTSRequest,
    x_api_key: str = Header(...),
):
    """
    Generate speech audio from text using XTTS engine.

    Returns base64-encoded WAV audio.
    """
    try:
        if not request.text or not request.text.strip():
            return TTSResponse(
                status="error",
                language=request.language,
                processed_at=datetime.utcnow().isoformat() + "Z",
            )

        audio_bytes = await audio_service.text_to_speech_async(
            request.text, language=request.language
        )

        if audio_bytes and len(audio_bytes) > 0:
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            return TTSResponse(
                status="success",
                audio_base64=audio_b64,
                audio_format="wav",
                language=request.language,
                text_length=len(request.text),
                audio_size_bytes=len(audio_bytes),
                processed_at=datetime.utcnow().isoformat() + "Z",
            )
        else:
            return TTSResponse(
                status="error",
                language=request.language,
                text_length=len(request.text),
                processed_at=datetime.utcnow().isoformat() + "Z",
            )

    except Exception as e:
        return TTSResponse(
            status="error",
            language=request.language,
            processed_at=datetime.utcnow().isoformat() + "Z",
        )


@router.get("/api/tts/status")
async def tts_status():
    """
    Return TTS engine operational status.
    """
    return {
        "tts": audio_service.get_tts_status(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
