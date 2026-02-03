from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Supported formats
SUPPORTED_MIMETYPES = {
    "audio/wav": "wav",
    "audio/mpeg": "mp3",
    "audio/mp4": "m4a",
    "audio/x-m4a": "m4a"
}

# MAX size 25MB
MAX_FILE_SIZE = 25 * 1024 * 1024

class STTResponse(BaseModel):
    text: str
    language: str
    confidence: float | None = None

@router.post("/voice_stt", response_model=STTResponse)
async def voice_stt(file: UploadFile = File(...)):
    """
    Mock STT implementation - returns placeholder text
    """

    # Check if file exists
    if not file:
        raise HTTPException(status_code=400, detail="No audio file provided")

    # Read bytes
    content = await file.read()
    size = len(content)

    # Check size
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max allowed = {MAX_FILE_SIZE / (1024 * 1024)} MB"
        )

    # Check mimetype
    if file.content_type not in SUPPORTED_MIMETYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Supported: {', '.join(SUPPORTED_MIMETYPES)}"
        )

    # Mock response
    return STTResponse(
        text=f"[Mock STT] Transcribed text from {file.filename}",
        language="en",
        confidence=0.95
    )
