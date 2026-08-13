from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.agent_service import AgentService

router = APIRouter()
agent_service = AgentService()

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    tool_calls: List[Dict[str, Any]] = []

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response_text, tool_calls = await agent_service.process_message(
            request.session_id, request.message
        )
        return ChatResponse(response=response_text, tool_calls=tool_calls)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
