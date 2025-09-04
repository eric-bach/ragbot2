import logging
import json
import boto3
from typing import Dict, List, Optional, Any
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

# Configure logging
logger = logging.getLogger(__name__)

class MCPServerConfig:
    """Configuration for an MCP server."""
    
    def __init__(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None, description: str = ""):
        self.name = name
        self.command = command
        self.args = args
        self.env = env or {}
        self.description = description
    
    def to_dict(self):
        return {
            "name": self.name,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            name=data["name"],
            command=data["command"],
            args=data["args"],
            env=data.get("env", {}),
            description=data.get("description", "")
        )

class MCPClientManager:
    """Manager for MCP (Model Context Protocol) client connections.
    
    This class handles the initialization and management of MCP clients,
    supporting both default AWS documentation and user-specific MCP servers.
    """
    
    def __init__(self, s3_client=None, sessions_bucket_name: Optional[str] = None):
        self._default_client = None
        self._default_initialized = False
        self._user_clients: Dict[str, MCPClient] = {}
        self._user_configs: Dict[str, List[MCPServerConfig]] = {}
        self._s3_client = s3_client
        self._sessions_bucket_name = sessions_bucket_name
        
    def get_client(self, user_id: Optional[str] = None):
        """Get the MCP client for a user, initializing it if necessary.
        
        Args:
            user_id: User ID to get client for. If None, returns default AWS client.
        
        Returns:
            MCPClient: The initialized MCP client instance
            
        Raises:
            Exception: If client initialization fails
        """
        logger.info(f"get_client called with user_id: {user_id}")
        
        if user_id is None:
            logger.info("No user_id provided, returning default client")
            return self._get_default_client()
        
        if user_id not in self._user_clients:
            logger.info(f"No cached client for user {user_id}, initializing...")
            self._initialize_user_client(user_id)
        else:
            logger.info(f"Using cached client for user {user_id}")
        
        client = self._user_clients.get(user_id, self._get_default_client())
        logger.info(f"Returning client for user {user_id}: {client is not None}")
        return client
    
    def _get_default_client(self):
        """Get the default AWS documentation client."""
        if not self._default_initialized:
            self._initialize_default_client()
        return self._default_client
    
    def _initialize_default_client(self):
        """Initialize the default MCP client with AWS documentation server.
        
        Raises:
            Exception: If client initialization fails
        """
        try:
            self._default_client = MCPClient(lambda: stdio_client(
                StdioServerParameters(
                    command="uvx", 
                    args=["awslabs.aws-documentation-mcp-server@latest"],
                    env={
                        "FASTMCP_LOG_LEVEL": "ERROR",
                        "AWS_DOCUMENTATION_PARTITION": "aws"
                    }
                )
            ))
            # Test the connection by entering and exiting context
            with self._default_client:
                # This ensures the subprocess is started and ready
                pass
            self._default_initialized = True
            logger.info("Default MCP client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize default MCP client: {e}")
            self._default_client = None
            self._default_initialized = False
            raise
    
    def _initialize_user_client(self, user_id: str):
        """Initialize MCP client for a specific user based on their configurations."""
        try:
            logger.info(f"Initializing user client for {user_id}")
            
            # Load user configurations from S3
            configs = self._load_user_mcp_configs(user_id)
            logger.info(f"Loaded {len(configs) if configs else 0} configs for user {user_id}")
            
            if not configs:
                # If no user configs, use default client
                logger.info(f"No MCP configs found for user {user_id}, using default client")
                return
            
            # For now, use the first configuration as the primary client
            # TODO: In the future, we could support multiple clients per user
            primary_config = configs[0]
            logger.info(f"Using primary config: {primary_config.name} (command: {primary_config.command})")
            logger.info(f"Command args: {primary_config.args}")
            logger.info(f"Environment: {primary_config.env}")
            
            # Try to create the client with more detailed error handling
            try:
                self._user_clients[user_id] = MCPClient(lambda: stdio_client(
                    StdioServerParameters(
                        command=primary_config.command,
                        args=primary_config.args,
                        env=primary_config.env
                    )
                ))
                logger.info(f"MCPClient created successfully for user {user_id}")
            except Exception as client_error:
                logger.error(f"Failed to create MCPClient: {client_error}")
                logger.error(f"This is likely because the command '{primary_config.command}' is not available in the container")
                raise
            
            # Test the connection
            logger.info(f"Testing MCP client connection for user {user_id}")
            try:
                with self._user_clients[user_id]:
                    logger.info(f"MCP client context entered successfully for user {user_id}")
            except Exception as context_error:
                logger.error(f"Failed to enter MCP client context: {context_error}")
                logger.error(f"This suggests the subprocess failed to start")
                raise
            
            logger.info(f"User MCP client initialized successfully for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize user MCP client for {user_id}: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Fall back to default client
            if user_id in self._user_clients:
                del self._user_clients[user_id]
    
    def _load_user_mcp_configs(self, user_id: str) -> List[MCPServerConfig]:
        """Load MCP server configurations for a user from S3."""
        if not self._s3_client or not self._sessions_bucket_name:
            return []
        
        try:
            key = f"mcp-configs/user_{user_id}/config.json"
            response = self._s3_client.get_object(
                Bucket=self._sessions_bucket_name,
                Key=key
            )
            
            data = json.loads(response['Body'].read().decode('utf-8'))
            configs = [MCPServerConfig.from_dict(config) for config in data.get('servers', [])]
            self._user_configs[user_id] = configs
            return configs
            
        except self._s3_client.exceptions.NoSuchKey:
            logger.info(f"No MCP config found for user {user_id}")
            return []
        except Exception as e:
            logger.error(f"Error loading MCP configs for user {user_id}: {e}")
            return []
    
    def save_user_mcp_configs(self, user_id: str, configs: List[MCPServerConfig]):
        """Save MCP server configurations for a user to S3."""
        logger.info(f"Starting save_user_mcp_configs for user {user_id}")
        logger.info(f"Number of configs to save: {len(configs)}")
        
        if not self._s3_client or not self._sessions_bucket_name:
            logger.error(f"S3 client or bucket name missing: s3_client={self._s3_client is not None}, bucket={self._sessions_bucket_name}")
            raise ValueError("S3 client and bucket name required for saving configs")
        
        try:
            key = f"mcp-configs/user_{user_id}/config.json"
            logger.info(f"S3 key: {key}")
            logger.info(f"S3 bucket: {self._sessions_bucket_name}")
            
            data = {
                'servers': [config.to_dict() for config in configs],
                'updated_at': str(boto3.client('sts').get_caller_identity().get('Account', 'unknown'))
            }
            
            logger.info(f"Data to save: {json.dumps(data, indent=2)}")
            
            self._s3_client.put_object(
                Bucket=self._sessions_bucket_name,
                Key=key,
                Body=json.dumps(data, indent=2),
                ContentType='application/json'
            )
            
            logger.info(f"Successfully saved to S3: s3://{self._sessions_bucket_name}/{key}")
            
            # Update cache
            self._user_configs[user_id] = configs
            
            # Invalidate existing client to force reinitialization
            if user_id in self._user_clients:
                del self._user_clients[user_id]
            
            logger.info(f"MCP configs saved for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error saving MCP configs for user {user_id}: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def get_user_mcp_configs(self, user_id: str) -> List[MCPServerConfig]:
        """Get MCP server configurations for a user."""
        if user_id in self._user_configs:
            return self._user_configs[user_id]
        
        return self._load_user_mcp_configs(user_id)
    
    def delete_user_mcp_configs(self, user_id: str):
        """Delete MCP server configurations for a user."""
        if not self._s3_client or not self._sessions_bucket_name:
            raise ValueError("S3 client and bucket name required for deleting configs")
        
        try:
            key = f"mcp-configs/user_{user_id}/config.json"
            self._s3_client.delete_object(
                Bucket=self._sessions_bucket_name,
                Key=key
            )
            
            # Clear cache
            if user_id in self._user_configs:
                del self._user_configs[user_id]
            
            # Invalidate existing client
            if user_id in self._user_clients:
                del self._user_clients[user_id]
            
            logger.info(f"MCP configs deleted for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error deleting MCP configs for user {user_id}: {e}")
            raise
