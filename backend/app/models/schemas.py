from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime



class ConversationBase(BaseModel):
    title: str

class ConversationResponse(ConversationBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
