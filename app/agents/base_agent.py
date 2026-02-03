class BaseAgent:
    name = "base"

    async def run(self, query, context):
        return {"agent": self.name, "output": "not implemented"}