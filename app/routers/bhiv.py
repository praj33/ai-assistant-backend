from fastapi import APIRouter
from pydantic import BaseModel
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

class BHIVRequest(BaseModel):
    query: str
    context: dict = {}

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

@router.post("/bhiv/run")
async def run_bhiv(request: BHIVRequest):
    result = await bhiv.process(request)
    return {"bhiv_output": result}