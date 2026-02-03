from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional

# FIXED IMPORT ✔
from ..core.decision_hub import decision_hub

router = APIRouter()

class DecisionRequest(BaseModel):
    input_text: str
    platform: str = "web"
    device_context: str = "desktop"
    voice_input: bool = False

@router.post("/decision_hub")
async def make_decision(
    input_text: str = Form(...),
    platform: str = Form("web"),
    device_context: str = Form("desktop"),
    voice_input: bool = Form(False),
    audio_file: Optional[UploadFile] = File(None)
):
    audio_data = None
    if audio_file:
        audio_data = await audio_file.read()

    decision = await decision_hub.make_decision(
        input_text,
        platform,
        device_context,
        voice_input,
        audio_data
    )
    return decision
