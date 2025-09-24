"""
Session management routes for the RAGBot agent.
"""
import json
import logging
from fastapi import APIRouter, HTTPException
from models.session import (
    CreateSessionRequest, 
    CreateSessionResponse, 
    ListSessionsResponse, 
    GetSessionResponse,
    UpdateSessionTitleRequest
)
from services.session_service import SessionService
from config import get_s3_client, DATA_BUCKET_NAME

logger = logging.getLogger(__name__)

router = APIRouter()
session_service = SessionService()

@router.post('/session', response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """Create a new session for a user."""
    logger.info(f"▶️ Creating new session for user: {request.user_id}")
    
    try:
        title = request.title or "New Chat"
        response = await session_service.create_session(request.user_id, title)
        return response
    except Exception as e:
        logger.error(f"🛑 Error creating session for user {request.user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/sessions/{user_id}', response_model=ListSessionsResponse)
async def list_user_sessions(user_id: str):
    """List all sessions for a user."""
    logger.info(f"▶️ Listing sessions for user: {user_id}")
    
    try:
        sessions = await session_service.list_user_sessions(user_id)
        return ListSessionsResponse(sessions=sessions)
    except Exception as e:
        logger.error(f"🛑 Error listing sessions for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/session/{user_id}/{session_id}', response_model=GetSessionResponse)
async def get_session(user_id: str, session_id: str):
    """Get a specific session with its chat history."""
    logger.info(f"▶️ Getting session {session_id} for user: {user_id}")
    
    try:
        response = await session_service.get_session_with_history(user_id, session_id)
        return response
    except Exception as e:
        logger.error(f"🛑 Error getting session {session_id} for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put('/session/{user_id}/{session_id}/title')
async def update_session_title(user_id: str, session_id: str, request: UpdateSessionTitleRequest):
    """Update session title."""
    logger.info(f"▶️ Updating title for session {session_id} to: {request.title}")
    
    try:
        response = await session_service.update_session_title(user_id, session_id, request.title)
        return response
    except Exception as e:
        logger.error(f"🛑 Error updating title for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete('/session/{user_id}/{session_id}')
async def delete_session(user_id: str, session_id: str):
    """Delete a user session and all associated data."""
    logger.info(f"▶️ Deleting session {session_id} for user: {user_id}")
    
    try:
        response = await session_service.delete_session(user_id, session_id)
        return response
    except Exception as e:
        logger.error(f"🛑 Error deleting session {session_id} for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
