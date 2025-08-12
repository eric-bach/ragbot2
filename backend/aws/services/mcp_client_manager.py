import os
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from models.mcp_config import MCPServerConfig, MCPServerType

logger = logging.getLogger(__name__)

class MCPClientManager:
    """Manages multiple MCP clients based on user configuration"""
    
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
    
    def _create_stdio_client(self, config: MCPServerConfig) -> Optional[MCPClient]:
        """Create a stdio MCP client from configuration"""
        try:
            if not config.command:
                logger.error(f"No command specified for stdio server {config.name}")
                return None
            
            # Set environment variables if specified
            env = os.environ.copy()
            if config.env_vars:
                env.update(config.env_vars)
            
            args = config.args or []
            
            client = MCPClient(lambda: stdio_client(
                StdioServerParameters(
                    command=config.command,
                    args=args,
                    env=env
                )
            ))
            
            return client
            
        except Exception as e:
            logger.error(f"Failed to create stdio MCP client for {config.name}: {str(e)}")
            return None
    
    def _create_sse_client(self, config: MCPServerConfig) -> Optional[MCPClient]:
        """Create an SSE MCP client from configuration"""
        # TODO: Implement SSE client creation when available in strands
        logger.warning(f"SSE MCP clients not yet implemented for {config.name}")
        return None
    
    def _create_websocket_client(self, config: MCPServerConfig) -> Optional[MCPClient]:
        """Create a WebSocket MCP client from configuration"""
        # TODO: Implement WebSocket client creation when available in strands
        logger.warning(f"WebSocket MCP clients not yet implemented for {config.name}")
        return None
    
    def create_clients_from_config(self, configs: List[MCPServerConfig]) -> List[MCPClient]:
        """Create MCP clients from a list of configurations"""
        clients = []
        
        for config in configs:
            if not config.enabled:
                logger.info(f"Skipping disabled MCP server: {config.name}")
                continue
                
            client = None
            
            if config.server_type == MCPServerType.STDIO:
                client = self._create_stdio_client(config)
            elif config.server_type == MCPServerType.SSE:
                client = self._create_sse_client(config)
            elif config.server_type == MCPServerType.WEBSOCKET:
                client = self._create_websocket_client(config)
            else:
                logger.error(f"Unknown server type: {config.server_type}")
                continue
            
            if client:
                clients.append(client)
                logger.info(f"Created MCP client for {config.name}")
            else:
                logger.error(f"Failed to create MCP client for {config.name}")
        
        return clients
    
    @asynccontextmanager
    async def get_combined_tools(self, user_configs: List[MCPServerConfig]):
        """Context manager that creates clients and yields combined tools"""
        clients = self.create_clients_from_config(user_configs)
        
        # Start all clients
        active_clients = []
        for client in clients:
            try:
                client.__enter__()
                active_clients.append(client)
            except Exception as e:
                logger.error(f"Failed to start MCP client: {str(e)}")
        
        try:
            # Combine tools from all active clients
            all_tools = []
            for client in active_clients:
                try:
                    tools = client.list_tools_sync()
                    all_tools.extend(tools)
                except Exception as e:
                    logger.error(f"Failed to get tools from MCP client: {str(e)}")
            
            yield all_tools, active_clients
            
        finally:
            # Clean up all clients
            for client in active_clients:
                try:
                    client.__exit__(None, None, None)
                except Exception as e:
                    logger.error(f"Error closing MCP client: {str(e)}")

# Singleton instance
mcp_client_manager = MCPClientManager()
