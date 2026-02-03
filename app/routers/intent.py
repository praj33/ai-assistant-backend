from fastapi import APIRouter
from pydantic import BaseModel
from ..core.intentflow import intent_flow

router = APIRouter()

class IntentRequest(BaseModel):
    text: str

@router.post("/intent")
async def detect_intent(request: IntentRequest):
    """Process text through IntentFlow for clean intent classification with entity resolution."""
    result = intent_flow.process_text(request.text)
    return result
