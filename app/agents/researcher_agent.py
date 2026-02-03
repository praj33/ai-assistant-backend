from .base_agent import BaseAgent

class ResearcherAgent(BaseAgent):
    name = "researcher"

    async def run(self, query, context):
        # Use LLM + search tools to gather info
        # For now, basic implementation
        info = "Gathered information from query: " + str(query)
        return {"agent": self.name, "output": info}