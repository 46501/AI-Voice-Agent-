from app.tools.registry import Tool, tool_registry
from simpleeval import simple_eval

def calculate(expression: str) -> str:
    """
    Evaluates a mathematical expression safely.
    """
    try:
        # safe evaluation of math strings
        result = simple_eval(expression)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"

calculator_tool = Tool(
    name="calculator",
    description="Calculates the result of a mathematical expression (e.g. '458 * 27', '15 / 100 * 8500').",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate"
            }
        },
        "required": ["expression"]
    },
    callable=calculate
)

tool_registry.register(calculator_tool)
