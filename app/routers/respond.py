from fastapi import APIRouter
from pydantic import BaseModel
from ..core.llm_bridge import llm_bridge
from ..core.bhiv_core import BHIVCore
from ..core.bhiv_reasoner import BHIVReasoner
from ..memory.memory_manager import MemoryManager
from ..agents.planner_agent import PlannerAgent
from ..agents.researcher_agent import ResearcherAgent
from ..agents.analyst_agent import AnalystAgent
from ..agents.executor_agent import ExecutorAgent
from ..agents.evaluator_agent import EvaluatorAgent
from ..tools.search_tool import SearchTool
from ..tools.web_browser_tool import WebBrowserTool
from ..tools.calculator_tool import CalculatorTool
from ..tools.file_tool import FileTool
from ..tools.automation_tool import AutomationTool

router = APIRouter()

# Initialize BHIV components
memory_manager = MemoryManager()
agents = {
    "planner": PlannerAgent(),
    "researcher": ResearcherAgent(),
    "analyst": AnalystAgent(),
    "executor": ExecutorAgent(),
    "evaluator": EvaluatorAgent()
}
tools = {
    "search": SearchTool(),
    "web_browser": WebBrowserTool(),
    "calculator": CalculatorTool(),
    "file": FileTool(),
    "automation": AutomationTool()
}
reasoner = BHIVReasoner()
bhiv = BHIVCore(memory_manager, agents, tools, reasoner)

class RespondRequest(BaseModel):
    query: str
    context: dict = {}
    model: str = "uniguru"
    decision: str = "respond"

@router.post("/respond")
async def generate_response(request: RespondRequest):
    try:
        if request.decision == "bhiv_core":
            return await bhiv.process(request)
        prompt = f"Context: {request.context}\nQuery: {request.query}\nProvide a helpful response."
        response = await llm_bridge.call_llm(request.model, prompt)
        return {"response": response}
    except Exception as e:
        return {"error": f"Failed to generate response: {str(e)}"}
