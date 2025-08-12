import os
import boto3
import logging
import json
from botocore.config import Config
from dotenv import load_dotenv
from strands import Agent
from strands_tools import http_request, retrieve
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from strands.session.s3_session_manager import S3SessionManager
from strands.agent.conversation_manager import SummarizingConversationManager, SlidingWindowConversationManager
from mcp import stdio_client, StdioServerParameters
from tools.web_search import web_search
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models.mcp_config import MCPConfigRequest, MCPConfigResponse, UserMCPConfig, MCPServerConfig, MCPServerType
from services.mcp_config_store import MCPConfigStore
from services.mcp_client_manager import mcp_client_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you should specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1') # Used by the Bedrock model
BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID') 
KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID') # Used by the retrieve tool
SESSIONS_BUCKET_NAME = os.getenv('SESSIONS_BUCKET_NAME') # Used by Strands Agent sessions
SOURCE_BUCKET_NAME = os.getenv('SOURCE_BUCKET_NAME') # Used by the presigned-url endpoint
LINKUP_API_KEY = os.getenv('LINKUP_API_KEY') # Used by the web_search tool

# Create session without profile for ECS deployment
session = boto3.Session(region_name=AWS_REGION)

# Create S3 client
s3 = boto3.client(
    "s3", 
    endpoint_url=f"https://s3.{AWS_REGION}.amazonaws.com", 
    config=Config(s3={"addressing_style": "virtual"}, 
    region_name=AWS_REGION,
    signature_version="s3v4"))

# Create a Bedrock model with the custom session
bedrock_model = BedrockModel(
    model_id=BEDROCK_MODEL_ID,
    boto_session=session
)

# Initialize MCP config store
mcp_config_store = MCPConfigStore(
    bucket_name=SESSIONS_BUCKET_NAME,
    region_name=AWS_REGION,
    boto_session=session
)

class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    query: str

def build_agent_for_session(session_id: str, user_id: str, user_mcp_configs: list = None) -> Agent:
    """Builds and returns a Strands Agent to a persistent session in S3 
    with conversation management and user-configured MCP servers"""
    session_manager = S3SessionManager(
        session_id=session_id,
        bucket=SESSIONS_BUCKET_NAME,
        prefix=f"sessions/user_{user_id}",
        boto_session=session,
        region_name=AWS_REGION
    )
    conversation_manager = SlidingWindowConversationManager(
        window_size=10
    )
    
    # Start with base tools
    base_tools = [web_search, http_request, retrieve]
    
    # Create all MCP clients and collect tools
    all_mcp_tools = []
    active_clients = []
    
    # Add user-configured MCP servers if provided
    if user_mcp_configs:
        user_clients = mcp_client_manager.create_clients_from_config(user_mcp_configs)
        active_clients.extend(user_clients)
    
    # Collect tools from all MCP clients
    for client in active_clients:
        try:
            client.__enter__()
            tools = client.list_tools_sync()
            all_mcp_tools.extend(tools)
        except Exception as e:
            logger.error(f"Failed to get tools from MCP client: {str(e)}")
    
    # Combine all tools
    all_tools = base_tools + all_mcp_tools

    logger.debug("tools", all_tools)

    return Agent(
        agent_id="ragbot2",
        system_prompt="""
        You are an AI assistant that helps users answer any type of questions with access to multiple tools:
            - Web search using LinkUp API (web_search)
            - User-configured MCP servers with custom capabilities
            - Retrieval-Augmented Generation (RAG) knowledge base (retrieve)
            
        **Instructions:**
        - For EVERY user query, you MUST use at least one tool.
            - The web_search tool is ideal for real-time information (e.g. weather, stock prices, news, anything 
            that can change minute-to-minute).
            - The retrieve tool is used for knowledge base queries (e.g. information about cars). Start with this
             for general knowledge questions.
            - If the retrieve tool cannot find an answer, use any tools from the MCP servers.
        - If you are not sure which tool to use, use the retrieve tool first, then MCP tools, before the web_search tool.
        - NEVER answer based solely on your own knowledge, even if you think you know the answer.
        - Only answer after reviewing results from all relevant tools.
        
        **Response:**
        - Your response must ALWAYS use the three required tags ONLY, and in Markdown format:
            - <thinking>: Explain your approach, reasoning, and tool choices.
            - <response>: Provide a clear, human-readable answer.
            - <sources>: List ALL tool outputs and/or sources used.
        - Do NOT output anything except these three tags.
        - Respond in a friendly, Albertan tone.
        
        **Example valid output:**
        <thinking>
        I used both web_search and retrieve because the user asked about current events and general knowledge.
        </thinking>

        <response>
        Here is the answer to your question based on the latest available sources...
        </response>

        <sources>
        - web_search: [search summary]
        - retrieve: [document snippet]
        </sources>

        Always follow this response structure and do NOT skip tool calls, otherwise your response is considered invalid.
        """,
        tools=all_tools,
        model=bedrock_model,
        session_manager=session_manager,
        conversation_manager=conversation_manager,
        callback_handler=None
    )

@app.get("/")
def home():
    return {"RAGBot": "v2"}

@app.get("/health")
def health():
    return {
        "STATUS": "healthy",
        "AWS_REGION": AWS_REGION,
        "KNOWLEDGE_BASE_ID": KNOWLEDGE_BASE_ID,
        "SESSIONS_BUCKET_NAME": SESSIONS_BUCKET_NAME,
        "SOURCE_BUCKET_NAME": SOURCE_BUCKET_NAME,
        "LINKUP_API_KEY": f"***{LINKUP_API_KEY[-3:]}",
    }

@app.get("/tools")
def get_tools():
    """Get list of available tools for the AI agent"""
    all_tools = [web_search, http_request, retrieve]
    
    tools_info = []
    for tool in all_tools:
        try:
            # Use your improved logic for getting tool names
            if hasattr(tool, 'tool_name'):
                tool_name = tool.tool_name
            else:
                tool_name = getattr(tool, '__name__', str(tool))
            
            tools_info.append({"name": tool_name})
        except Exception as e:
            logger.warning(f"Could not process tool {tool}: {e}")
            # Add a fallback entry
            tools_info.append({"name": f"Tool_{len(tools_info)}"})
    
    return {
        "tools": tools_info,
        "total_count": len(tools_info)
    }

@app.get("/tools/{user_id}")
async def get_user_tools(user_id: str):
    """Get list of all available tools including user-configured MCP tools"""
    try:
        # Get user's MCP configuration
        user_config = await mcp_config_store.get_user_config(user_id)
        user_mcp_configs = user_config.servers if user_config else []
        
        # Start with base tools
        base_tools = [web_search, http_request, retrieve]
        tools_info = []
        
        # Add base tools
        for tool in base_tools:
            try:
                if hasattr(tool, 'tool_name'):
                    tool_name = tool.tool_name
                else:
                    tool_name = getattr(tool, '__name__', str(tool))
                
                description = getattr(tool, 'description', None) or getattr(tool, '__doc__', None)
                if description:
                    description = description.strip().split('\n')[0]  # First line only
                
                tools_info.append({
                    "name": tool_name,
                    "description": description,
                    "source": "base"
                })
            except Exception as e:
                logger.warning(f"Could not process base tool {tool}: {e}")
        
        # Add user-configured MCP server tools
        if user_mcp_configs:
            try:
                user_clients = mcp_client_manager.create_clients_from_config(user_mcp_configs)
                for i, client in enumerate(user_clients):
                    try:
                        client.__enter__()
                        user_tools = client.list_tools_sync()
                        logger.info(f"Retrieved {len(user_tools)} tools from MCP client")
                        server_name = user_mcp_configs[i].name if i < len(user_mcp_configs) else f"MCP Server {i+1}"
                        
                        for tool in user_tools:
                            try:
                                # Debug logging to understand tool structure
                                logger.info(f"Processing MCP tool: {tool}")
                                logger.info(f"Tool type: {type(tool)}")
                                logger.info(f"Tool attributes: {[attr for attr in dir(tool) if not attr.startswith('_')]}")
                                
                                # Try multiple ways to get the tool name
                                tool_name = None
                                if hasattr(tool, 'name'):
                                    tool_name = tool.name
                                elif hasattr(tool, 'tool_name'):
                                    tool_name = tool.tool_name
                                elif hasattr(tool, '_name'):
                                    tool_name = tool._name
                                elif hasattr(tool, '__name__'):
                                    tool_name = tool.__name__
                                elif hasattr(tool, 'function_name'):
                                    tool_name = tool.function_name
                                elif hasattr(tool, 'schema') and hasattr(tool.schema, 'name'):
                                    tool_name = tool.schema.name
                                else:
                                    # If all else fails, try to get it from the tool's attributes
                                    tool_name = f"Tool_{len(tools_info)}"
                                
                                # Try multiple ways to get the description
                                description = None
                                if hasattr(tool, 'description'):
                                    description = tool.description
                                elif hasattr(tool, '__doc__'):
                                    description = tool.__doc__
                                elif hasattr(tool, '_description'):
                                    description = tool._description
                                elif hasattr(tool, 'schema') and hasattr(tool.schema, 'description'):
                                    description = tool.schema.description
                                
                                if description:
                                    description = str(description).strip().split('\n')[0]  # First line only
                                
                                tools_info.append({
                                    "name": tool_name,
                                    "description": description,
                                    "source": server_name
                                })
                            except Exception as e:
                                logger.warning(f"Could not process user MCP tool {tool}: {e}")
                                # Add a fallback entry with basic info
                                tools_info.append({
                                    "name": f"Unknown Tool {len(tools_info)}",
                                    "description": f"Tool from {server_name}",
                                    "source": server_name
                                })
                    except Exception as e:
                        logger.error(f"Failed to get tools from user MCP client: {str(e)}")
                    finally:
                        try:
                            client.__exit__(None, None, None)
                        except:
                            pass
            except Exception as e:
                logger.error(f"Failed to create user MCP clients: {str(e)}")
        
        return {
            "tools": tools_info,
            "total_count": len(tools_info)
        }
        
    except Exception as e:
        logger.error(f"Error getting tools for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving tools: {str(e)}")

@app.get("/mcp-config/{user_id}")
async def get_mcp_config(user_id: str):
    """Get user's MCP server configuration"""
    try:
        config = await mcp_config_store.get_user_config(user_id)
        if config:
            return MCPConfigResponse(
                success=True,
                message="Configuration retrieved successfully",
                servers=config.servers
            )
        else:
            return MCPConfigResponse(
                success=True,
                message="No configuration found",
                servers=[]
            )
    except Exception as e:
        logger.error(f"Error getting MCP config for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving configuration: {str(e)}")

@app.post("/mcp-config/{user_id}")
async def save_mcp_config(user_id: str, request: MCPConfigRequest):
    """Save user's MCP server configuration"""
    try:
        user_config = UserMCPConfig(user_id=user_id, servers=request.servers)
        success = await mcp_config_store.save_user_config(user_id, user_config)
        
        if success:
            return MCPConfigResponse(
                success=True,
                message="Configuration saved successfully",
                servers=request.servers
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
            
    except Exception as e:
        logger.error(f"Error saving MCP config for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving configuration: {str(e)}")

@app.delete("/mcp-config/{user_id}")
async def delete_mcp_config(user_id: str):
    """Delete user's MCP server configuration"""
    try:
        success = await mcp_config_store.delete_user_config(user_id)
        
        if success:
            return MCPConfigResponse(
                success=True,
                message="Configuration deleted successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete configuration")
            
    except Exception as e:
        logger.error(f"Error deleting MCP config for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting configuration: {str(e)}")

@app.get("/mcp-server-types")
def get_mcp_server_types():
    """Get available MCP server types"""
    return {
        "server_types": [
            {
                "value": MCPServerType.STDIO,
                "label": "Standard Input/Output",
                "description": "Servers that communicate via stdin/stdout"
            },
            {
                "value": MCPServerType.SSE,
                "label": "Server-Sent Events",
                "description": "Servers that communicate via HTTP SSE (coming soon)"
            },
            {
                "value": MCPServerType.WEBSOCKET,
                "label": "WebSocket",
                "description": "Servers that communicate via WebSocket (coming soon)"
            }
        ]
    }

@app.get("/presigned-url")
def generate_presigned_url(user_id: str = Query(..., description="User ID"), file_name: str = Query(..., description="Name of the file to upload")):
    """Generate a presigned URL for S3 file upload"""
    try:
        file_name_full = file_name
        if not file_name_full.endswith('.pdf'):
            file_name_full = f"{file_name}.pdf"
        
        file_name_clean = file_name_full.split(".pdf")[0]

        # Always use the original filename - will overwrite if exists
        key = f"{user_id}/{file_name_clean}.pdf"

        logger.info(
            {
                "user_id": user_id,
                "file_name_full": file_name_full,
                "file_name_clean": file_name_clean,
                "key": key,
            }
        )

        presigned_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": SOURCE_BUCKET_NAME,
                "Key": key,
                "ContentType": "application/pdf",
            },
            ExpiresIn=300,
            HttpMethod="PUT",
        )

        return {
            "presignedurl": presigned_url,
            "key": key,
            "bucket": SOURCE_BUCKET_NAME
        }
        
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating presigned URL: {str(e)}")

@app.delete('/session/{user_id}/{session_id}')
async def delete_session(user_id: str, session_id: str):
    prefix = f"sessions/user_{user_id}/session_{session_id}/"
    try:
        # List all objects under just the target session folder
        response = s3.list_objects_v2(Bucket=SESSIONS_BUCKET_NAME, Prefix=prefix)
        if 'Contents' in response:
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            s3.delete_objects(
                Bucket=SESSIONS_BUCKET_NAME,
                Delete={'Objects': objects_to_delete}
            )
            return {"message": f"Deleted {len(objects_to_delete)} objects in session {session_id}"}
        else:
            return {"message": f"No objects found for session {session_id}"}
    except Exception as e:
        return {"error": str(e)}

@app.post('/chat')
async def chat(request: ChatRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="No query provided")
    if not request.session_id:
        raise HTTPException(status_code=400, detail="No session_id provided")
    if not request.user_id:
        raise HTTPException(status_code=400, detail="No user_id provided")

    async def generate(session_id: str, user_id: str, query: str):
        try:
            # Get user's MCP configuration
            user_config = await mcp_config_store.get_user_config(user_id)
            user_mcp_configs = user_config.servers if user_config else []
            
            # Build agent with user's MCP configurations
            agent = build_agent_for_session(session_id, user_id, user_mcp_configs)

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
