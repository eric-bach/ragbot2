from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class MCPServerType(str, Enum):
    STDIO = "stdio"
    SSE = "sse"
    WEBSOCKET = "websocket"

class MCPServerConfig(BaseModel):
    name: str
    description: Optional[str] = None
    server_type: MCPServerType
    command: Optional[str] = None  # For stdio servers
    args: Optional[List[str]] = None  # For stdio servers
    url: Optional[str] = None  # For SSE/WebSocket servers
    env_vars: Optional[Dict[str, str]] = None  # Environment variables
    enabled: bool = True

class UserMCPConfig(BaseModel):
    user_id: str
    servers: List[MCPServerConfig]

class MCPConfigRequest(BaseModel):
    servers: List[MCPServerConfig]

class MCPConfigResponse(BaseModel):
    success: bool
    message: str
    servers: Optional[List[MCPServerConfig]] = None
