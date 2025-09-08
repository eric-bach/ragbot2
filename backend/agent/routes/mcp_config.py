"""
MCP (Model Context Protocol) configuration routes for the RAGBot agent.
"""
import logging
from fastapi import APIRouter, HTTPException
from models.mcp_config import MCPConfigRequest, MCPConfigResponse, UserMCPConfig
from config import get_mcp_config_store

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/mcp-config/{user_id}")
async def get_mcp_config(user_id: str):
    """Get user's MCP server configuration."""
    logger.info(f"▶️ Retrieving MCP config for user: {user_id}")

    try:
        mcp_config_store = get_mcp_config_store()
        config = await mcp_config_store.get_user_config(user_id)
        
        if config:
            logger.info(f"✅ Retrieved MCP config for user: {user_id} with {len(config.servers)} servers")

            return MCPConfigResponse(
                success=True,
                message="Configuration retrieved successfully",
                servers=config.servers
            )
        else:
            logger.info(f"ℹ️ No MCP config found for user: {user_id}")

            return MCPConfigResponse(
                success=True,
                message="No configuration found",
                servers=[]
            )
    except Exception as e:
        logger.error(f"🛑 Error getting MCP config for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving configuration: {str(e)}")
    
@router.post("/mcp-config/{user_id}")
async def save_mcp_config(user_id: str, request: MCPConfigRequest):
    """Save user's MCP server configuration."""
    logger.info(f"▶️ Saving MCP config for user: {user_id} with {len(request.servers)} servers")

    try:
        mcp_config_store = get_mcp_config_store()
        user_config = UserMCPConfig(user_id=user_id, servers=request.servers)
        success = await mcp_config_store.save_user_config(user_id, user_config)

        if success:
            logger.info(f"✅ Saved MCP config for user: {user_id} with {len(request.servers)} servers")

            return MCPConfigResponse(
                success=True,
                message="Configuration saved successfully",
                servers=request.servers
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to save configuration")

    except Exception as e:
        logger.error(f"🛑 Error saving MCP config for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving configuration: {str(e)}")
    
@router.delete("/mcp-config/{user_id}")
async def delete_mcp_config(user_id: str):
    """Delete user's MCP server configuration."""
    logger.info(f"▶️ Deleting MCP config for user: {user_id}")

    try:
        mcp_config_store = get_mcp_config_store()
        success = await mcp_config_store.delete_user_config(user_id)

        if success:
            logger.info(f"✅ Deleted MCP config for user: {user_id}")

            return MCPConfigResponse(
                success=True,
                message="Configuration deleted successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete configuration")

    except Exception as e:
        logger.error(f"🛑 Error deleting MCP config for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting configuration: {str(e)}")
