"""Safe calculator tool using Python's ast module."""
import ast
import operator
from typing import Any

from backend.tools.base import BaseTool

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPS:
            raise ValueError(f"Unsupported operator: {op_type}")
        return _ALLOWED_OPS[op_type](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPS:
            raise ValueError(f"Unsupported operator: {op_type}")
        return _ALLOWED_OPS[op_type](_safe_eval(node.operand))
    raise ValueError(f"Unsupported node type: {type(node)}")


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Evaluate a mathematical expression safely. Input: expression string."

    async def run(self, expression: str) -> dict:
        try:
            tree = ast.parse(expression, mode="eval")
            result = _safe_eval(tree.body)
            return {"expression": expression, "result": result}
        except Exception as e:
            return {"error": str(e), "expression": expression}
