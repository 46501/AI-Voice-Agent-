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
            # Add the assistant's tool calls to the conversation history
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                tool_call_trace.append({"tool": function_name, "args": function_args})
                
                if function_name in TOOL_FUNCTIONS:
                    function_to_call = TOOL_FUNCTIONS[function_name]
                    # Execute tool
                    function_response = function_to_call(**function_args)
                else:
                    function_response = f"Error: Tool {function_name} not found."
                    
                # Add tool response to messages
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(function_response),
                })
            
            # Second pass to get final answer
            second_response = await client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=messages,
            )
            return second_response.choices[0].message.content, tool_call_trace
            
        return response_message.content, tool_call_trace
