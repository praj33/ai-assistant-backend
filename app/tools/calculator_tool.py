class CalculatorTool:
    async def run(self, query):
        # Simulate calculation
        try:
            result = eval(query)  # Simple eval for demo
            return f"Calculated: {result}"
        except:
            return "Invalid calculation"