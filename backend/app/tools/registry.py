import json
import datetime
import urllib.request
import urllib.parse
from typing import Dict, Any, Callable

def tool_calculator(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        # VERY DANGEROUS IN PRODUCTION. Using eval for demonstration.
        # A real app should use a safe math parser.
        # We'll allow a restricted set of characters.
        allowed = "0123456789+-*/(). "
        if all(c in allowed for c in expression):
            return str(eval(expression))
        return "Error: Invalid characters in expression."
    except Exception as e:
        return f"Error evaluating: {e}"

def tool_current_time(timezone: str = "UTC") -> str:
    """Return the current time."""
    return f"The current time is {datetime.datetime.now().isoformat()}"

def tool_weather(location: str) -> str:
    """Return mock weather for a location."""
    return f"The weather in {location} is currently 72°F and sunny."

def tool_web_search(query: str) -> str:
    """Perform a simple web search using DuckDuckGo HTML."""
    try:
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8')
            # Very hacky extraction of the first snippet
            start = html.find('class="result__snippet')
            if start != -1:
                end = html.find('</a>', start)
                snippet = html[start:end]
                # Strip tags
                import re
                clean = re.sub('<[^<]+>', '', snippet)
                return clean.strip()
        return "No results found."
    except Exception as e:
        return f"Search failed: {e}"

# Registry mapping function names to Callables
TOOL_FUNCTIONS: Dict[str, Callable] = {
    "calculator": tool_calculator,
    "current_time": tool_current_time,
    "weather": tool_weather,
    "web_search": tool_web_search,
}

# The OpenAI JSON schema for these tools
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Calculate a mathematical expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression (e.g., '2 + 2')"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "current_time",
            "description": "Get the current time",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "Optional timezone"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    }
]
