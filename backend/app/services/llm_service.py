import json
from openai import AsyncOpenAI
from app.config import config
from app.tools.registry import tool_registry

client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are VoxAI, an advanced, intelligent voice assistant. 
Because this is a voice conversation, your responses will be spoken aloud via TTS.

RULES:
- Be conversational, natural, and concise.
- Avoid unnecessary long explanations unless specifically asked for details.
- Avoid markdown-heavy formatting (no lists like 1. 2. 3. unless necessary, speak them naturally).
- Don't read URLs aloud unnecessarily.
- Don't say "as an AI language model".
- Use natural pauses by structuring your sentences well.
- Ask follow-up questions when required.
- You have access to various tools (weather, time, calculator, search, notes). Use them when appropriate!
- DO NOT pretend you have searched the web or checked the weather if you haven't used the tool.
"""

class LLMService:
    async def generate_response_stream(self, messages: list):
        """
        Stream response. Handles tool calls asynchronously, then streams the final text.
        Yields tokens.
        """
        if not config.OPENAI_API_KEY:
            yield "Error: OPENAI_API_KEY is not configured."
            return

        # Ensure system prompt is present
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

        tools_schema = tool_registry.get_schema_list()

        # First pass (non-streaming) to check for tool calls
        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            tools=tools_schema,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # If the LLM wants to call tools, we handle them fully before streaming the final answer
        if response_message.tool_calls:
            messages.append(response_message)
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                try:
                    function_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    function_args = {}
                
                # Notify frontend that we are calling a tool
                yield {"type": "tool_call", "name": function_name, "args": function_args}
                
                # Execute tool using the registry
                function_response = await tool_registry.execute(function_name, function_args)
                    
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
