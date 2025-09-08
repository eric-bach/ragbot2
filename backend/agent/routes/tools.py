"""
Tools-related routes for the RAGBot agent.
"""
import logging
from fastapi import APIRouter, HTTPException
from services.agent_service import get_base_tools_info, process_mcp_tools_info
from services.mcp_client_manager import mcp_client_manager
from config import get_mcp_config_store

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/tools/{user_id}")
async def get_user_tools(user_id: str):
    """Get list of all available tools including user-configured MCP tools."""
    logger.info(f"▶️ Getting tools for user {user_id}")

    try:
        mcp_config_store = get_mcp_config_store()
        
        # Get user's MCP configuration
        user_config = await mcp_config_store.get_user_config(user_id)
        user_mcp_configs = user_config.servers if user_config else []

        # Start with base tools
        tools_info = get_base_tools_info()

        # Add user-configured MCP server tools with proper resource management
        mcp_errors = []
        if user_mcp_configs:
            try:
                async with mcp_client_manager.get_combined_tools(user_mcp_configs) as (user_tools, clients, errors):
                    logger.debug(f"Retrieved {len(user_tools)} tools from {len(clients)} MCP clients")
                    mcp_errors = errors
                    
                    # Log any MCP errors for debugging
                    if mcp_errors:
                        logger.warning(f"MCP server errors: {mcp_errors}")

                    # Process MCP tools and add to tools_info
                    mcp_tools_info = process_mcp_tools_info(user_tools)
                    tools_info.extend(mcp_tools_info)

            except Exception as e:
                logger.error(f"Failed to get MCP tools: {str(e)}")

        logger.info(f"✅ Found {tools_info.count} tools for user {user_id}: {tools_info}")
        
        return {
            "tools": tools_info,
            "total_count": len(tools_info),
            "mcp_errors": mcp_errors
        }

    except Exception as e:
        logger.error(f"Error getting tools for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving tools: {str(e)}")
