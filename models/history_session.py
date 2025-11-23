from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """
    Represents a single message within a session.
    """
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HistorySession(BaseModel):
    """
    Represents an entire conversation session between the user and the assistant.
    """
    session_id: str = Field(..., description="Unique identifier for this session.")
    user_id: Optional[str] = Field(None, description="ID of the user owning this session.")
    title: Optional[str] = Field(None, description="Optional title (can be generated from first user message).")
    messages: List[ChatMessage] = Field(default_factory=list, description="Ordered list of exchanged messages.")
    model: Optional[str] = Field("gpt-4o-mini", description="The AI model used for this session.")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "session_id": "bochao_20251027_1",
                "user_id": "bochao",
                "title": "Resume optimization for backend role",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hi, can you help me improve my resume?",
                        "timestamp": "2025-10-27T13:00:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "Of course. Please share your resume content or the job description first.",
                        "timestamp": "2025-10-27T13:00:05Z"
                    }
                ],
                "created_at": "2025-10-27T13:00:00Z",
                "updated_at": "2025-10-27T13:00:05Z"
            }
        }

class HistorySessionUpdate(BaseModel):
    title: Optional[str] = None
