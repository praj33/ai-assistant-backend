from .base_agent import BaseAgent

class EvaluatorAgent(BaseAgent):
    name = "evaluator"

    async def run(self, query, context):
        # Review output → adjust → final improvement
        # query here is steps, context is previous
        evaluation = "Evaluated and improved: " + str(query)
        return {"agent": self.name, "output": evaluation}