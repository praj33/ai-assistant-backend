from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

# FIXED IMPORTS ✔
from ..core.security import verify_api_key, create_access_token

router = APIRouter()

class TokenRequest(BaseModel):
    username: str

@router.post("/auth/token")
async def get_access_token(
    request: TokenRequest,
    api_key: str = Depends(verify_api_key)
):
    access_token = create_access_token(data={"sub": request.username})
    return {"access_token": access_token, "token_type": "bearer"}
