"""
Chat schemas for SRM Guide Bot
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.database import MessageRole


class ChatCreate(BaseModel):
    """Create chat request schema"""
    title: Optional[str] = Field(None, max_length=255, description="Chat title")


class ChatResponse(BaseModel):
    """Chat response schema"""
    id: str = Field(..., description="Chat ID")
    title: Optional[str] = Field(None, description="Chat title")
    user_id: str = Field(..., description="User ID")
    is_active: bool = Field(..., description="Chat active status")
    created_at: datetime = Field(..., description="Chat creation date")
    updated_at: datetime = Field(..., description="Chat last update date")

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Create message request schema"""
    content: str = Field(..., min_length=1, max_length=4000, description="Message content")


class MessageResponse(BaseModel):
    """Message response schema"""
    id: str = Field(..., description="Message ID")
    content: str = Field(..., description="Message content")
    role: MessageRole = Field(..., description="Message role (user/assistant)")
    chat_id: str = Field(..., description="Chat ID")
    user_id: Optional[str] = Field(None, description="User ID (null for AI messages)")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Message metadata",
        validation_alias="extra_metadata",
        serialization_alias="metadata",
    )
    created_at: datetime = Field(..., description="Message creation date")

    class Config:
        from_attributes = True


class AIResponse(BaseModel):
    """AI response schema"""
    content: str = Field(..., description="AI response content")
    tokens_used: Dict[str, int] = Field(..., description="Token usage statistics")
    model_used: str = Field(..., description="AI model used")
    category: str = Field(..., description="Message category")
    knowledge_base: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Knowledge base match metadata when the response is grounded in FAQs",
    )


class QuickSuggestion(BaseModel):
    """Quick suggestion schema"""
    title: str = Field(..., description="Suggestion title")
    description: str = Field(..., description="Suggestion description")
    icon: str = Field(..., description="Suggestion icon")
    category: str = Field(..., description="Suggestion category")


class ChatStats(BaseModel):
    """Chat statistics schema"""
    total_messages: int = Field(..., description="Total messages in chat")
    user_messages: int = Field(..., description="User messages count")
    ai_messages: int = Field(..., description="AI messages count")
    total_tokens: int = Field(..., description="Total tokens used")
    average_response_time: float = Field(..., description="Average AI response time")


class ChatExport(BaseModel):
    """Chat export schema"""
    chat_id: str = Field(..., description="Chat ID")
    title: str = Field(..., description="Chat title")
    messages: List[MessageResponse] = Field(..., description="Chat messages")
    stats: ChatStats = Field(..., description="Chat statistics")
    exported_at: datetime = Field(..., description="Export timestamp")
