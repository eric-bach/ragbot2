import logging
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

# Configure logging
logger = logging.getLogger(__name__)

class MCPClientManager:
    """Manager for MCP (Model Context Protocol) client connections.
    
    This class handles the initialization and management of MCP clients,
    specifically for AWS documentation services.
    """
    
    def __init__(self):
        self._client = None
        self._initialized = False
        
    def get_client(self):
        """Get the MCP client, initializing it if necessary.
        
        Returns:
            MCPClient: The initialized MCP client instance
            
        Raises:
            Exception: If client initialization fails
        """
        if not self._initialized:
            self._initialize_client()
        return self._client
    
    def _initialize_client(self):
        """Initialize the MCP client with AWS documentation server.
        
        Raises:
            Exception: If client initialization fails
        """
        try:
            self._client = MCPClient(lambda: stdio_client(
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
            with self._client:
                # This ensures the subprocess is started and ready
                pass
            self._initialized = True
            logger.info("MCP client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            self._client = None
            self._initialized = False
            raise
