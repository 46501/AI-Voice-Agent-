import openai
import json
from app.config import config
from app.tools.registry import TOOLS_SCHEMA, TOOL_FUNCTIONS

client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)

class LLMService:
    async def generate_response(self, messages: list) -> tuple[str, list]:
        """
        Send messages to LLM, handle tool calls if any, and return final text + tool call trace.
        """
        if not config.OPENAI_API_KEY:
            return "Error: OPENAI_API_KEY is not configured.", []
            
        tool_call_trace = []
        
        # First pass
        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # If the LLM wants to call tools
        if response_message.tool_calls:
            messages.append(response_message)
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_call_trace.append({"tool": function_name, "args": function_args})
                
                if function_name in TOOL_FUNCTIONS:
                    function_response = TOOL_FUNCTIONS[function_name](**function_args)
                else:
                    function_response = f"Error: Tool {function_name} not found."
                    
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(function_response),
                })
            
            # Second pass
            second_response = await client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=messages,
            )
            return second_response.choices[0].message.content, tool_call_trace
            
        return response_message.content, tool_call_trace

    async def generate_response_stream(self, messages: list):
        """
        Stream response. Handles tool calls synchronously, then streams the final text.
        Yields (token: str).
        """
        if not config.OPENAI_API_KEY:
            yield "Error: OPENAI_API_KEY is not configured."
            return

        # First pass (non-streaming) to check for tool calls
        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # If the LLM wants to call tools, we handle them fully before streaming the final answer
        if response_message.tool_calls:
            messages.append(response_message)
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name in TOOL_FUNCTIONS:
                    function_response = TOOL_FUNCTIONS[function_name](**function_args)
                else:
                    function_response = f"Error: Tool {function_name} not found."
                    
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(function_response),
                })
        
        # Now stream the final response
        stream = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
