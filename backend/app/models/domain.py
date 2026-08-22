from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base



class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, index=True) # UUID string
    session_id = Column(String, index=True, nullable=True)
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    

    messages = relationship("Message", back_populates="conversation", order_by="Message.timestamp")
    tool_calls = relationship("ToolCall", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String, nullable=False) # 'user', 'ai', 'system', 'tool'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    conversation = relationship("Conversation", back_populates="messages")

class ToolCall(Base):
    __tablename__ = "tool_calls"
    
    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    turn_id = Column(String)
    tool_name = Column(String, nullable=False)
    input = Column(JSON)
    output = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    execution_time_ms = Column(Integer)
    
    conversation = relationship("Conversation", back_populates="tool_calls")
