import os
import asyncio
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
        self._tool_cache: Dict[str, List] = {}  # Cache for tools by config hash
        self._cache_ttl: int = 300  # 5 minutes cache TTL
        self._cache_timestamps: Dict[str, float] = {}
    
    def _get_config_hash(self, configs: List[MCPServerConfig]) -> str:
        """Generate a hash for the configuration to use as cache key"""
        import hashlib
        import json
        
        config_data = []
        for config in configs:
            if config.enabled:
                config_data.append({
                    'name': config.name,
                    'command': config.command,
                    'args': config.args,
                    'server_type': config.server_type
                })
        
        config_str = json.dumps(config_data, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        import time
        if cache_key not in self._cache_timestamps:
            return False
        return (time.time() - self._cache_timestamps[cache_key]) < self._cache_ttl
    
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
            
            # Add timeout to prevent hanging connections
            client = MCPClient(lambda: stdio_client(
                StdioServerParameters(
                    command=config.command,
                    args=args,
                    env=env
                )
            ))
            
            # Test the client connection with a short timeout
            logger.info(f"Testing connection to MCP server: {config.name}")
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
        
        # Start all clients with timeout
        active_clients = []
        
        for client in clients:
            try:
                # Use asyncio wait_for to prevent hanging
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, client.__enter__),
                    timeout=10.0  # 10 second timeout
                )
                active_clients.append(client)
                logger.info(f"Successfully started MCP client")
            except asyncio.TimeoutError:
                logger.error(f"Timeout starting MCP client after 10 seconds")
            except Exception as e:
                logger.error(f"Failed to start MCP client: {str(e)}")
        
        try:
            # Combine tools from all active clients with timeout
            all_tools = []
            for client in active_clients:
                try:
                    tools = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, client.list_tools_sync),
                        timeout=5.0  # 5 second timeout for tool listing
                    )
                    all_tools.extend(tools)
                    logger.info(f"Retrieved {len(tools)} tools from MCP client")
                except asyncio.TimeoutError:
                    logger.error(f"Timeout getting tools from MCP client after 5 seconds")
                except Exception as e:
                    logger.error(f"Failed to get tools from MCP client: {str(e)}")
            
            yield all_tools, active_clients
            
        finally:
            # Clean up all clients
            for client in active_clients:
                try:
                    await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, client.__exit__, None, None, None),
                        timeout=5.0  # 5 second timeout for cleanup
                    )
                    logger.debug(f"Successfully closed MCP client")
                except asyncio.TimeoutError:
                    logger.error(f"Timeout closing MCP client after 5 seconds")
                except Exception as e:
                    logger.error(f"Error closing MCP client: {str(e)}")

# Singleton instance
mcp_client_manager = MCPClientManager()
