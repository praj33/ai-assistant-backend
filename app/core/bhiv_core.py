class BHIVCore:
    def __init__(self, memory_manager, agents, tools, reasoner):
        self.memory = memory_manager
        self.agents = agents
        self.tools = tools
        self.reasoner = reasoner

    async def process(self, input_data):
        context = self.memory.retrieve_context(input_data)
        reasoning_steps = await self.reasoner.run(input_data, context, self.agents, self.tools)
        final = self.reasoner.finalize(reasoning_steps)
        self.memory.update(input_data, final)
        return final