from .base_agent import BaseAgent

class AnalystAgent(BaseAgent):
    name = "analyst"

    async def run(self, query, context):
        # Perform logical reasoning + evaluation
        analysis = "Analyzed: " + str(query) + " with reasoning."
        return {"agent": self.name, "output": analysis}