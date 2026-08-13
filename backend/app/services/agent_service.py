from typing import Dict, List, Any
from app.services.llm_service import LLMService

SYSTEM_PROMPT = """You are VoxAI, a helpful, intelligent and conversational AI voice assistant.
Speak naturally and concisely.
Since you are communicating through voice:
* Avoid unnecessarily long answers
* Avoid excessive markdown
* Avoid reading code formatting aloud
* Use natural conversational language
* Ask clarifying questions when required
* Remember previous messages in the current conversation
* Never claim to have performed an action unless the action actually succeeded
* If you don't know something, clearly say so
* Prioritize accuracy and usefulness
* Be friendly but professional.
"""

class AgentService:
    def __init__(self):
        self.llm_service = LLMService()
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        if session_id not in self.sessions:
            self.sessions[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
        return self.sessions[session_id]

    def clear_session(self, session_id: str):
        self.sessions[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    async def process_message(self, session_id: str, user_message: str) -> tuple[str, list]:
        """
        Add user message to history, get LLM response, add AI response to history.
        Returns the final AI text and tool trace.
        """
        history = self.get_session_history(session_id)
        
        # We append a new dictionary so we don't mutate unexpectedly
        history.append({"role": "user", "content": user_message})
        
        # Pass a copy to LLMService in case it mutates with tool calls
        messages_copy = list(history)
        
        final_text, tool_trace = await self.llm_service.generate_response(messages_copy)
        
        # The LLM Service might have appended tool call messages to messages_copy
        # We should update our history to match the resolved state.
        self.sessions[session_id] = messages_copy
        
        # Finally, append the final AI response
        self.sessions[session_id].append({"role": "assistant", "content": final_text})
        
        return final_text, tool_trace
