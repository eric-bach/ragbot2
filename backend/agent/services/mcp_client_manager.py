import os
import json
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
    
    def _ensure_aws_credentials(self, config: MCPServerConfig, env: Dict[str, str]) -> None:
        """Ensure AWS credentials are available for AWS MCP servers"""
        try:
            # Check if this appears to be an AWS MCP server
            is_aws_server = (
                'aws' in config.name.lower() or
                (config.args and any('aws' in str(arg).lower() for arg in config.args)) or
                (config.command and 'aws' in config.command.lower())
            )
            
            if not is_aws_server:
                return
                
            logger.info(f"Detected AWS MCP server: {config.name}, ensuring AWS credentials are available")
            
            # Check if AWS credentials are already set in config env_vars
            aws_env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'AWS_PROFILE']
            has_aws_credentials = config.env_vars and any(key in config.env_vars for key in aws_env_vars)
            
            if has_aws_credentials:
                logger.info(f"AWS credentials found in MCP server configuration for {config.name}")
                return
                
            # Check if AWS credentials are available in host environment
            host_has_credentials = any(key in os.environ for key in aws_env_vars)
            
            if host_has_credentials:
                logger.info(f"Inheriting AWS credentials from host environment for {config.name}")
                # Copy AWS-related environment variables from host
                for key in aws_env_vars:
                    if key in os.environ:
                        env[key] = os.environ[key]
                        
                # Also copy AWS region if not already set
                if 'AWS_REGION' in os.environ and 'AWS_REGION' not in env:
                    env['AWS_REGION'] = os.environ['AWS_REGION']
                    
                # Copy AWS default region as fallback
                if 'AWS_DEFAULT_REGION' in os.environ and 'AWS_DEFAULT_REGION' not in env:
                    env['AWS_DEFAULT_REGION'] = os.environ['AWS_DEFAULT_REGION']
                    
                # Validate that we have the minimum required credentials
                self._validate_aws_credentials(env, config.name)
                
                # Check SSO status if using AWS profile (skip in containerized environments)
                if not self._is_containerized_environment():
                    self._check_aws_sso_status(config)
            else:
                # Check if we're in a containerized environment (ECS, etc.)
                if self._is_containerized_environment():
                    logger.info(f"Running in containerized environment for {config.name}. "
                              "Assuming AWS credentials are provided via IAM role or container credentials.")
                else:
                    logger.warning(f"No AWS credentials found for AWS MCP server {config.name}. "
                                 "Please configure credentials via environment variables or AWS SSO.")
                             
        except Exception as e:
            logger.error(f"Error ensuring AWS credentials for {config.name}: {str(e)}")
            # Don't fail the entire client creation, just log the error
    
    def _is_containerized_environment(self) -> bool:
        """Check if we're running in a containerized environment like ECS"""
        try:
            # Check for ECS metadata endpoint
            if os.environ.get('AWS_EXECUTION_ENV', '').startswith('AWS_ECS'):
                return True
                
            # Check for ECS task metadata URI
            if os.environ.get('ECS_CONTAINER_METADATA_URI_V4'):
                return True
                
            # Check for general containerization indicators
            if os.path.exists('/.dockerenv'):
                return True
                
            # Check for Kubernetes environment
            if os.environ.get('KUBERNETES_SERVICE_HOST'):
                return True
                
            return False
            
        except Exception:
            return False
    

    
    def _validate_aws_credentials(self, env: Dict[str, str], server_name: str) -> bool:
        """Validate that AWS credentials are properly configured"""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            
            # Check if we have either access keys or a profile
            has_access_keys = (
                env.get('AWS_ACCESS_KEY_ID') and 
                env.get('AWS_SECRET_ACCESS_KEY')
            )
            has_profile = env.get('AWS_PROFILE')
            
            if not has_access_keys and not has_profile:
                logger.warning(f"AWS MCP server {server_name} has no credentials configured")
                return False
            
            # Try to create a simple AWS client to validate credentials
            # We'll use a minimal environment for testing
            test_env = {k: v for k, v in env.items() if k.startswith('AWS_')}
            
            # Temporarily set environment variables for validation
            old_env = {}
            for key, value in test_env.items():
                old_env[key] = os.environ.get(key)
                os.environ[key] = value
            
            try:
                # Create a simple STS client to validate credentials
                session = boto3.Session()
                sts_client = session.client('sts')
                
                # Try to get caller identity - this will fail if credentials are invalid
                response = sts_client.get_caller_identity()
                logger.info(f"AWS credentials validated for {server_name}. "
                           f"Account: {response.get('Account', 'unknown')}, "
                           f"User: {response.get('Arn', 'unknown')}")
                return True
                
            except (ClientError, NoCredentialsError) as e:
                logger.warning(f"AWS credential validation failed for {server_name}: {str(e)}")
                return False
                
            finally:
                # Restore original environment
                for key in test_env.keys():
                    if old_env[key] is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = old_env[key]
                        
        except ImportError:
            logger.info(f"boto3 not available for credential validation for {server_name}")
            return True  # Assume valid if we can't validate
        except Exception as e:
            logger.warning(f"Error validating AWS credentials for {server_name}: {str(e)}")
            return True  # Don't block on validation errors
    
    def _check_aws_sso_status(self, config: MCPServerConfig) -> bool:
        """Check if AWS SSO credentials need refresh"""
        try:
            import subprocess
            import json
            
            # Only check if using AWS_PROFILE
            profile = None
            if config.env_vars and 'AWS_PROFILE' in config.env_vars:
                profile = config.env_vars['AWS_PROFILE']
            elif 'AWS_PROFILE' in os.environ:
                profile = os.environ['AWS_PROFILE']
                
            if not profile:
                return True  # Not using SSO profile
                
            # Check SSO status
            result = subprocess.run(
                ['aws', 'sts', 'get-caller-identity', '--profile', profile],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"AWS SSO credentials are valid for profile {profile}")
                return True
            else:
                logger.warning(f"AWS SSO credentials may need refresh for profile {profile}. "
                             f"Run 'aws sso login --profile {profile}' to refresh.")
                return False
                
        except Exception as e:
            # Handle all exceptions (subprocess errors, import errors, etc.)
            logger.debug(f"Could not check AWS SSO status for {config.name}: {str(e)}")
            return True  # Assume valid if we can't check
    
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
            
            # Automatically inherit AWS credentials if this appears to be an AWS MCP server
            self._ensure_aws_credentials(config, env)
            
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

            logger.info(f"Initializing MCP client: {json.dumps({'command': command, 'args': ' '.join(args), 'env_vars_count': len(env)})}")

            # Enhanced logging for debugging - but still proceed even if command not found locally
            import shutil
            command_path = shutil.which(command)
            if not command_path:
                logger.warning(f"Command '{command}' not found in PATH check (this may be normal in containers)")
                logger.info(f"Proceeding anyway - MCP server process will show actual availability")
            else:
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
            return client

        except Exception as e:
            logger.error(f"🛑 Failed to create stdio MCP client for {config.name}: {str(e)}")
            logger.error(f"🛑 MCP client config details: command='{config.command}', args={config.args}, env_vars={list(config.env_vars.keys()) if config.env_vars else []}")
            
            # Log more details about the error
            import traceback
            logger.error(f"🛑 Full traceback: {traceback.format_exc()}")
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

        logger.info(f"⚙️ Creating {len(configs)} MCP clients from MCP configurations")

        for i, config in enumerate(configs):         
            if not config.enabled:
                continue

            logger.info(f"Initializing MCP client ({i+1}): {json.dumps({
                'name': config.name,
                'command': config.command,
                'args': config.args,
                'enabled': config.enabled
            })}")

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
                logger.info(f"🛠️ Created MCP client for {config.name}")
            else:
                logger.error(f"🛑 Failed to create MCP client for {config.name}")

        return clients
            
    @asynccontextmanager
    async def get_combined_tools(self, user_configs: List[MCPServerConfig]):
        """Context manager that creates clients and yields combined tools"""
        logger.info("⚙️ Getting all tools")

        clients = self.create_clients_from_config(user_configs)
        
        # Track errors for user feedback
        mcp_errors = []

        # Start all clients with timeout
        active_clients = []
        # Track mapping between active clients and their configs
        active_client_configs = []

        # First, get the enabled configs that correspond to the created clients
        enabled_configs = [config for config in user_configs if config.enabled]
        
        for i, client in enumerate(clients):
            try:
                # Get the config for this client from the enabled configs
                config = enabled_configs[i] if i < len(enabled_configs) else None
                server_name = config.name if config else f"Client {i+1}"
                
                logger.info(f"Starting MCP client {i+1}/{len(clients)}: {server_name}")
                if config:
                    logger.info(f"  - Command: {config.command}")
                    logger.info(f"  - Args: {config.args}")
                    logger.info(f"  - Env vars: {list(config.env_vars.keys()) if config.env_vars else []}")

                # Use asyncio wait_for to prevent hanging
                logger.info(f"Calling client.__enter__ for {server_name}")
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, client.__enter__),
                    timeout=10.0  # 10 second timeout
                )
                active_clients.append(client)
                active_client_configs.append(config)

                logger.info(f"🛠️ Successfully started MCP client {i+1}: {server_name}")
            except asyncio.TimeoutError:
                error_msg = f"Timeout starting MCP client {i+1} after 10 seconds"
                logger.error(f"❌ {error_msg}")
                config = enabled_configs[i] if i < len(enabled_configs) else None
                mcp_errors.append({
                    "server_name": config.name if config else f"Client {i+1}",
                    "error": "Connection timeout (10 seconds)",
                    "type": "timeout"
                })
            except Exception as e:
                config = enabled_configs[i] if i < len(enabled_configs) else None
                server_name = config.name if config else f"Client {i+1}"
                
                error_msg = f"Failed to start MCP client {i+1} ({server_name}): {str(e)}"
                logger.error(f"❌ {error_msg}")
                
                if config:
                    logger.error(f"❌ Failed config details: command='{config.command}', args={config.args}")
                
                # Log the full exception for debugging
                import traceback
                logger.error(f"❌ Full exception traceback: {traceback.format_exc()}")
                
                mcp_errors.append({
                    "server_name": server_name,
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

                    # Get the server name for this client using the correct mapping
                    config = active_client_configs[i] if i < len(active_client_configs) else None
                    server_name = config.name if config else "MCP Server"

                    # Debug: Log retrieved tool details and set source
                    for tool in tools:
                        logger.debug(f"Listing tools for: {tool}")
                        if hasattr(tool, '__dict__'):
                            logger.debug(f"Found MCP tool attributes: {tool.__dict__}")
                        
                        # Fix MCPAgentTool attributes if they're not set properly
                        if hasattr(tool, 'mcp_tool') and tool.mcp_tool:
                            if not hasattr(tool, 'name') or not tool.name:
                                tool.name = tool.mcp_tool.name
                                logger.info(f"Found tool: {tool.name}")
                            if not hasattr(tool, 'tool_name') or not tool.tool_name:
                                tool.tool_name = tool.mcp_tool.name
                                logger.info(f"Found tool: {tool.tool_name}")
                            if not hasattr(tool, 'description') or not tool.description:
                                description = tool.mcp_tool.description
                                if description:
                                    tool.description = description.split('\n')[0].strip()
                                    logger.info(f"Found tool description: {tool.description}")
                        # Set the source to the server name
                        tool.source = server_name

                    # Log once per server, not per tool
                    logger.info(f"Found {len(tools)} tools from MCP client {server_name}")
                    all_tools.extend(tools)
                except asyncio.TimeoutError:
                    error_msg = f"Timeout getting tools from MCP client after 5 seconds"
                    logger.error(error_msg)
                    # Get the correct config for this client using the index
                    config = active_client_configs[i] if i < len(active_client_configs) else None
                    mcp_errors.append({
                        "server_name": config.name if config else f"Client {i+1}",
                        "error": "Timeout retrieving tools (5 seconds)",
                        "type": "tools_timeout"
                    })
                except Exception as e:
                    error_msg = f"🛑 Failed to get tools from MCP client: {str(e)}"
                    logger.error(error_msg)
                    # Get the correct config for this client using the index
                    config = active_client_configs[i] if i < len(active_client_configs) else None
                    mcp_errors.append({
                        "server_name": config.name if config else f"Client {i+1}",
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

            logger.info(f"🛠️ Found all tools")

# Singleton instance
mcp_client_manager = MCPClientManager()