from fastapi import APIRouter
from pydantic import BaseModel

# FIXED IMPORT ✔
from ..core.rl_selector import RLActionSelector

router = APIRouter()

class RLActionRequest(BaseModel):
    state: dict
    actions: list

selector = RLActionSelector()

@router.post("/rl_action")
async def select_rl_action(request: RLActionRequest):
    selected_action, probabilities, ranking = selector.select_action(
        request.state, 
        request.actions
    )
    return {
        "selected_action": selected_action,
        "probabilities": probabilities,
        "ranking": ranking
    }
