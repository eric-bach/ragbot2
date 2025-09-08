"""
Chat-related routes for the RAGBot agent.
"""
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models.chat import ChatRequest
from services.agent_service import build_agent_for_session
from services.mcp_client_manager import mcp_client_manager
from config import get_mcp_config_store

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post('/chat')
async def chat(request: ChatRequest):
    """Handle chat requests with streaming responses."""
    if not request.query:
        raise HTTPException(status_code=400, detail="No query provided")
    if not request.session_id:
        raise HTTPException(status_code=400, detail="No session_id provided")
    if not request.user_id:
        raise HTTPException(status_code=400, detail="No user_id provided")

    async def generate(session_id: str, user_id: str, query: str):
        """Generate streaming response for chat."""
        try:
            mcp_config_store = get_mcp_config_store()
            
            # Get user's MCP configuration
            user_config = await mcp_config_store.get_user_config(user_id)
            user_mcp_configs = user_config.servers if user_config else []
        
            # Handle MCP tools with proper async context management
            if user_mcp_configs:
                # Use the async context manager to get MCP tools
                async with mcp_client_manager.get_combined_tools(user_mcp_configs) as (user_mcp_tools, clients, errors):
                    logger.info(f"Using {len(clients)} MCP clients with {len(user_mcp_tools)} tools for user {user_id}")
                    
                    # Log any MCP errors
                    if errors:
                        logger.warning(f"MCP server errors for user {user_id}: {errors}")
                    
                    # Build agent with the collected MCP tools
                    agent = build_agent_for_session(session_id, user_id, user_mcp_tools)

                    try:
                        agent_stream = agent.stream_async(query)
                        
                        chunk_count = 0
                        async for event in agent_stream:
                            if "data" in event:
                                # Only stream text chunks to the client
                                chunk_count += 1
                                if chunk_count % 60 == 0:  # Log every 60th chunk
                                    logger.info(f"Streamed {chunk_count} chunks so far for session {session_id}")
                                yield event['data']
                        logger.info(f"Streaming response complete - total chunks: {chunk_count}")
                    except Exception as e:
                        logger.error(f"Error in agent stream: {str(e)}")
                        yield f"Error: {str(e)}"
            else:
                # No MCP tools, just use base tools
                logger.info(f"Using base tools only for user {user_id}")
                agent = build_agent_for_session(session_id, user_id, [])

                try:
                    agent_stream = agent.stream_async(query)
                    
                    chunk_count = 0
                    async for event in agent_stream:
                        if "data" in event:
                            # Only stream text chunks to the client
                            chunk_count += 1
                            if chunk_count % 60 == 0:  # Log every 60th chunk
                                logger.info(f"Streamed {chunk_count} chunks so far for session {session_id}")
                            yield event['data']
                    logger.info(f"Streaming response complete - total chunks: {chunk_count}")
                except Exception as e:
                    logger.error(f"Error in agent stream: {str(e)}")
                    yield f"Error: {str(e)}"

        except Exception as e:
            logger.error(f"Error setting up agent: {str(e)}")
            yield f"Error setting up agent: {str(e)}"

    logger.info(f"Chat request received: session_id={request.session_id}, query={request.query}, user_id={request.user_id}")

    return StreamingResponse(
        generate(request.session_id, request.user_id, request.query),
        media_type="text/plain"
    )
