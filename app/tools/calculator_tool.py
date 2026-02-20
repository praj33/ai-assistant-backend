import ast
import operator

class CalculatorTool:
    """Safe calculator tool using AST-based expression evaluation."""

    # Supported operators for safe math evaluation
    _OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _safe_eval(self, node):
        """Recursively evaluate an AST node with only arithmetic operations."""
        if isinstance(node, ast.Expression):
            return self._safe_eval(node.body)
        elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self._OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            if op_type == ast.Div and right == 0:
                raise ValueError("Division by zero")
            if op_type == ast.Pow and right > 100:
                raise ValueError("Exponent too large")
            return self._OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self._OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            return self._OPERATORS[op_type](self._safe_eval(node.operand))
        else:
            raise ValueError("Unsupported expression")

    async def run(self, query):
        """Evaluate a math expression safely without using eval()."""
        try:
            if not isinstance(query, str) or len(query) > 200:
                return "Invalid calculation: input must be a string under 200 characters"
            tree = ast.parse(query.strip(), mode='eval')
            result = self._safe_eval(tree)
            return f"Calculated: {result}"
        except (ValueError, SyntaxError, TypeError) as e:
            return f"Invalid calculation: {e}"