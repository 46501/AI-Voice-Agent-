from typing import Dict, Any, Callable
from pydantic import BaseModel
import asyncio
import inspect

class Tool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    callable: Callable

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        
    def register(self, tool: Tool):
        self._tools[tool.name] = tool
        
    def get_tool(self, name: str) -> Tool | None:
        return self._tools.get(name)
        
    def get_all_tools(self) -> Dict[str, Tool]:
        return self._tools
        
    def get_schema_list(self) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in self._tools.values()
        ]

    async def execute(self, name: str, args: dict) -> Any:
        tool = self.get_tool(name)
        if not tool:
            return f"Error: Tool {name} not found."
            
        try:
            if inspect.iscoroutinefunction(tool.callable):
                return await tool.callable(**args)
            else:
                return tool.callable(**args)
        except Exception as e:
            return f"Error executing {name}: {str(e)}"

tool_registry = ToolRegistry()
