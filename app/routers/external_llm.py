from fastapi import APIRouter
from pydantic import BaseModel

# FIXED IMPORT ✔
from ..core.llm_bridge import llm_bridge

router = APIRouter()

class LLMRequest(BaseModel):
    prompt: str
    model: str = "uniguru"  # uniguru, chatgpt, groq, gemini, mistral

@router.post("/external_llm")
async def call_external_llm(request: LLMRequest):
    response = await llm_bridge.call_llm(request.model, request.prompt)
    return {"response": response}
