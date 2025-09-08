import os
import asyncio
import logging
from typing import List, Dict, Optional
from contextlib import asynccontextmanager
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from models.mcp_config import MCPServerConfig, MCPServerType

# Configure logging
logger = logging.getLogger(__name__)

class MCPClientManager:
    """Manages multiple MCP clients based on user configuration"""
    
    def __init__(self):
        self._clients: Dict[str, MCPClient] = {}
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
                logger.warning(f"No command specified for stdio server {config.name}, skipping")
                return None

            # At this point, config.command is guaranteed to be not None
            command: str = config.command.strip()  # Remove any leading/trailing whitespace

            # Set environment variables if specified
            env = os.environ.copy()
            if config.env_vars:
                env.update(config.env_vars)

            # Parse arguments properly - handle both list and string formats
            args = config.args or []
            if args and isinstance(args, list) and len(args) == 1 and isinstance(args[0], str):
                # If we have a single string argument, it might need to be split
                import shlex
                try:
                    # Use shlex to properly split shell-like arguments
                    args = shlex.split(args[0])
                except ValueError:
                    # If shlex fails, fallback to simple split
                    args = args[0].split()

            logger.info(f"Creating stdio MCP client for {config.name} with command: '{command}' and args: {args}")
            logger.info(f"Full command line would be: {command} {' '.join(args)}")
            logger.info(f"Environment variables for {config.name}: {env}")

            # Verify command exists before creating client
            import shutil
            command_path = shutil.which(command)
            if not command_path:
                logger.error(f"Command '{command}' not found in PATH for MCP server {config.name}")
                logger.info(f"Available commands in PATH: {[shutil.which(cmd) for cmd in ['python', 'python3', 'node', 'npm', 'npx', 'uvx'] if shutil.which(cmd)]}")
                return None
                
            logger.info(f"Command '{command}' found at: {command_path}")

            # Add timeout to prevent hanging connections
            client = MCPClient(lambda: stdio_client(
                StdioServerParameters(
                    command=command,
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

        logger.info(f"Processing {len(configs)} MCP server configurations")

        for i, config in enumerate(configs):
            logger.info(f"Processing config {i+1}: name={config.name}, enabled={config.enabled}, command={config.command}, args={config.args}")
            
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
        
        # Track errors for user feedback
        mcp_errors = []

        # Start all clients with timeout
        active_clients = []

        for i, client in enumerate(clients):
            try:
                logger.info(f"⏳ Starting MCP client {i+1}/{len(clients)}: {client}")

                # Use asyncio wait_for to prevent hanging
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, client.__enter__),
                    timeout=10.0  # 10 second timeout
                )
                active_clients.append(client)
                logger.info(f"✅ Successfully started MCP client {i+1}")
            except asyncio.TimeoutError:
                error_msg = f"Timeout starting MCP client {i+1} after 10 seconds"
                logger.error(f"❌ {error_msg}")
                mcp_errors.append({
                    "server_name": user_configs[i].name if i < len(user_configs) else f"Client {i+1}",
                    "error": "Connection timeout (10 seconds)",
                    "type": "timeout"
                })
            except Exception as e:
                error_msg = f"Failed to start MCP client {i+1}: {str(e)}"
                logger.error(f"❌ {error_msg}", exc_info=True)
                mcp_errors.append({
                    "server_name": user_configs[i].name if i < len(user_configs) else f"Client {i+1}",
                    "error": str(e),
                    "type": "startup_error"
                })

        try:
            # Combine tools from all active clients with timeout
            all_tools = []
            for i, client in enumerate(active_clients):
                try:
                    tools = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, client.list_tools_sync),
                        timeout=5.0  # 5 second timeout for tool listing
                    )

                    # Get the server name for this client
                    server_name = "MCP Server"
                    if i < len(user_configs):
                        server_name = user_configs[i].name

                    # Debug: Log retrieved tool details and set source
                    for tool in tools:
                        logger.info(f"Retrieved MCP Tool - Type: {type(tool)}, Name: {getattr(tool, 'name', 'unknown')}, Description: {getattr(tool, 'description', 'no description')}")
                        if hasattr(tool, '__dict__'):
                            logger.info(f"MCP Tool attributes: {tool.__dict__}")
                        
                        # Fix MCPAgentTool attributes if they're not set properly
                        if hasattr(tool, 'mcp_tool') and tool.mcp_tool:
                            if not hasattr(tool, 'name') or not tool.name:
                                tool.name = tool.mcp_tool.name
                                logger.info(f"Set tool name to: {tool.name}")
                            if not hasattr(tool, 'description') or not tool.description:
                                # Use first line of description for brevity
                                description = tool.mcp_tool.description
                                if description:
                                    tool.description = description.split('\n')[0].strip()
                                    logger.info(f"Set tool description to: {tool.description}")
                            if not hasattr(tool, 'tool_name') or not tool.tool_name:
                                tool.tool_name = tool.mcp_tool.name
                                logger.info(f"Set tool_name to: {tool.tool_name}")
                        
                        # Set the source to the server name
                        tool.source = server_name
                        logger.info(f"Set tool source to: {server_name}")

                    all_tools.extend(tools)
                    logger.info(f"Retrieved {len(tools)} tools from MCP client")
                except asyncio.TimeoutError:
                    error_msg = f"Timeout getting tools from MCP client after 5 seconds"
                    logger.error(error_msg)
                    # Find the corresponding config for this client
                    client_index = active_clients.index(client)
                    if client_index < len(user_configs):
                        mcp_errors.append({
                            "server_name": user_configs[client_index].name,
                            "error": "Timeout retrieving tools (5 seconds)",
                            "type": "tools_timeout"
                        })
                except Exception as e:
                    error_msg = f"Failed to get tools from MCP client: {str(e)}"
                    logger.error(error_msg)
                    # Find the corresponding config for this client
                    client_index = active_clients.index(client)
                    if client_index < len(user_configs):
                        mcp_errors.append({
                            "server_name": user_configs[client_index].name,
                            "error": str(e),
                            "type": "tools_error"
                        })

            yield all_tools, active_clients, mcp_errors

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