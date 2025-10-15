"""A small calculation tool that evaluates simple arithmetic expressions.

It is intentionally limited and uses Python's eval on a restricted namespace.
"""
from __future__ import annotations

from typing import Any, Dict


class CalcTool:
    name = "calc"
    description = "Evaluate a simple arithmetic expression provided as 'expr'"
    parameters = {
        "type": "object",
        "properties": {"expr": {"type": "string", "description": "Arithmetic expression"}},
        "required": ["expr"],
    }

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        expr = input.get("expr")
        if not expr:
            return {"error": "expr is required"}

        # restricted eval
        allowed_names = {"__builtins__": {}}
        try:
            result = eval(expr, allowed_names, {})
        except Exception as e:
            return {"error": str(e)}

        return {"result": result}
