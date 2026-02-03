from fastapi import APIRouter
from pydantic import BaseModel
from ..core.summaryflow import summary_flow

router = APIRouter()

class SummarizeRequest(BaseModel):
    text: str

@router.post("/summarize")
async def summarize_text(request: SummarizeRequest):
    """Generate stable summary JSON schema using SummaryFlow."""
    result = summary_flow.generate_summary(request.text)
    return result
