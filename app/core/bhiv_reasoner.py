class BHIVReasoner:
    async def run(self, query, context, agents, tools):
        steps = []
        # Planner
        plan = await agents["planner"].run(query, context)
        steps.append(plan)

        for task in plan["output"]["steps"]:
            if task["type"] == "research":
                steps.append(await agents["researcher"].run(task, context))
            elif task["type"] == "analyze":
                steps.append(await agents["analyst"].run(task, context))
            elif task["type"] == "execute":
                steps.append(await agents["executor"].run(task, context))

        final = await agents["evaluator"].run(steps, context)
        return final

    def finalize(self, result):
        return result["output"]