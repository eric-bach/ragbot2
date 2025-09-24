"""
Session management models for the RAGBot agent.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SessionSummary(BaseModel):
    """Summary information for a user session."""
    session_id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int

class CreateSessionRequest(BaseModel):
    """Request model for creating a new session."""
    user_id: str
    title: Optional[str] = "New Chat"

class CreateSessionResponse(BaseModel):
    """Response model for creating a new session."""
    session_id: str
    user_id: str
    title: str
    created_at: datetime

class ListSessionsResponse(BaseModel):
    """Response model for listing user sessions."""
    sessions: List[SessionSummary]

class GetSessionResponse(BaseModel):
    """Response model for getting a session with its history."""
    session_id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    conversation: List[dict]  # Chat history

class UpdateSessionTitleRequest(BaseModel):
    """Request model for updating a session title."""
    title: str