from .base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    name = "planner"

    async def run(self, query, context):
        # Break tasks into steps
        steps = [
            {"type": "research", "description": "Gather information"},
            {"type": "analyze", "description": "Analyze data"},
            {"type": "execute", "description": "Execute actions"},
        ]
        return {"agent": self.name, "output": {"steps": steps}}