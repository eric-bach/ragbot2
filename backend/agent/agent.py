import os
import boto3
import logging
from botocore.config import Config
from dotenv import load_dotenv
from strands import Agent
from strands_tools import retrieve, current_time
from strands.models import BedrockModel
from strands.session.s3_session_manager import S3SessionManager
from strands.agent.conversation_manager import SlidingWindowConversationManager
from tools.web_search import web_search
from services.mcp_client_manager import mcp_client_manager
from services.mcp_config_store import MCPConfigStore
from models.mcp_config import MCPConfigRequest, MCPConfigResponse, UserMCPConfig
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2') # Used by the Bedrock model
BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID') 
KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID') # Used by the retrieve tool
DATA_BUCKET_NAME = os.getenv('DATA_BUCKET_NAME', '')
KNOWLEDGE_SOURCE_BUCKET_NAME = os.getenv('KNOWLEDGE_SOURCE_BUCKET_NAME') # Used by the presigned-url endpoint
LINKUP_API_KEY = os.getenv('LINKUP_API_KEY', '') # Used by the web_search tool
BASE_TOOLS = [web_search, current_time, retrieve]

if (not BEDROCK_MODEL_ID):
    logger.error("BEDROCK_MODEL_ID environment variable is not set")
    raise Exception("BEDROCK_MODEL_ID environment variable is not set")
if (not DATA_BUCKET_NAME or DATA_BUCKET_NAME == ''):
    logger.error("DATA_BUCKET_NAME environment variable is not set")
    raise Exception("DATA_BUCKET_NAME environment variable is not set")
if (not LINKUP_API_KEY or LINKUP_API_KEY == ''):
    logger.error("LINKUP_API_KEY environment variable is not set")
    raise Exception("LINKUP_API_KEY environment variable is not set")

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
    bucket_name=DATA_BUCKET_NAME,
    region_name=AWS_REGION,
    boto_session=session
)

class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    query: str

def build_agent_for_session(session_id: str, user_id: str, user_mcp_tools: list = []) -> Agent:
    """Builds and returns a Strands Agent with conversation management and pre-collected MCP tools"""
    session_manager = S3SessionManager(
        session_id=session_id,
        bucket=DATA_BUCKET_NAME,
        prefix=f"sessions/{user_id}",
        boto_session=session,
        region_name=AWS_REGION
    )
    conversation_manager = SlidingWindowConversationManager(
        window_size=10
    )

    # Combine all tools (base tools + pre-collected MCP tools)
    tools = BASE_TOOLS + user_mcp_tools

    logger.info(f"Final combined tools count: {len(tools)} (base: {len(BASE_TOOLS)}, MCP: {len(user_mcp_tools)})")
    for i, tool in enumerate(tools):
        logger.info(f"Final Tool {i}: Type: {type(tool)}, Name: {getattr(tool, 'name', getattr(tool, 'tool_name', 'unknown'))}, Description: {getattr(tool, 'description', getattr(tool, '__doc__', 'no description'))}")

    logger.debug("tools", tools)

    # Build dynamic system prompt that includes information about available MCP tools
    base_tools_description = """
    - Web search using LinkUp API (web_search)
    - Getting the current date and time (current_time)
    - Retrieval-Augmented Generation (RAG) knowledge base (retrieve)"""
    
    mcp_tools_description = ""
    if user_mcp_tools:
        mcp_tools_description = "\n\nAdditionally, you have access to the following MCP server tools:"
        for tool in user_mcp_tools:
            tool_name = getattr(tool, 'name', getattr(tool, 'tool_name', 'unknown'))
            tool_description = getattr(tool, 'description', getattr(tool, '__doc__', 'no description'))
            tool_source = getattr(tool, 'source', 'MCP Server')
            
            # Clean up description - take first line only
            if tool_description and tool_description != 'no description':
                tool_description = tool_description.strip().split('\n')[0]
            else:
                tool_description = "MCP tool"
            
            mcp_tools_description += f"\n    - {tool_name} (from {tool_source}): {tool_description}"

    system_prompt = f"""You are an AI assistant that helps users answer any type of questions.
You have access to the following base tools:{base_tools_description}{mcp_tools_description}

**Instructions:**
    - For EVERY user query, select one or more tools to use based on the user's question.
    - Prioritize MCP server tools when they are relevant to the user's query, as they provide specialized functionality.
    - You MUST call and use at least one tool.
    - NEVER answer based solely on your own knowledge, even if you think you know the answer.
    - Only answer after reviewing results from all relevant tools.

**Response Format:**
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
        """

    return Agent(
        agent_id="ragbot2",
        system_prompt=system_prompt,
        tools=tools,
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
    logger.info(f"✅ Health Check OK")
    return {
        "STATUS": "healthy",
        "AWS_REGION": AWS_REGION,
        "KNOWLEDGE_BASE_ID": KNOWLEDGE_BASE_ID,
        "DATA_BUCKET_NAME": DATA_BUCKET_NAME,
        "KNOWLEDGE_SOURCE_BUCKET_NAME": KNOWLEDGE_SOURCE_BUCKET_NAME,
        "LINKUP_API_KEY": f"***{LINKUP_API_KEY[-3:]}",
    }

@app.get("/tools")
def get_tools():
    """Get list of available tools for the AI agent"""
    logger.info(f"🏁 Getting all tools")

    tools_info = []
    for tool in BASE_TOOLS:
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
            logger.warning(f"Could not process tool {tool}: {e}")
            # Add a fallback entry
            tools_info.append({"name": f"Tool_{len(tools_info)}"})
    
    logger.info(f"✅ Found tools: {tools_info}")
    return {
        "tools": tools_info,
        "total_count": len(tools_info)
    }

@app.get("/tools/{user_id}")
async def get_user_tools(user_id: str):
    """Get list of all available tools including user-configured MCP tools"""
    logger.info(f"🏁 Getting tools for user {user_id}")

    try:
        # Get user's MCP configuration
        user_config = await mcp_config_store.get_user_config(user_id)
        user_mcp_configs = user_config.servers if user_config else []

        # Start with base tools
        tools_info = []

        # Add base tools
        for tool in BASE_TOOLS:
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

        # Add user-configured MCP server tools with proper resource management
        mcp_errors = []
        if user_mcp_configs:
            try:
                async with mcp_client_manager.get_combined_tools(user_mcp_configs) as (user_tools, clients, errors):
                    logger.info(f"Retrieved {len(user_tools)} tools from {len(clients)} MCP clients")
                    mcp_errors = errors
                    
                    # Log any MCP errors for debugging
                    if mcp_errors:
                        logger.warning(f"MCP server errors: {mcp_errors}")

                    for i, tool in enumerate(user_tools):
                        try:
                            # Debug logging to understand tool structure
                            logger.debug(f"Processing MCP tool: {tool}")
                            
                            tool_name = None
                            # For custom tools (web_search)
                            if hasattr(tool, 'tool_name'):
                                tool_name = tool.tool_name
                            # For strands tools (http_request, retrieve)
                            elif hasattr(tool, '__name__'):
                                tool_name = tool.__name__
                            else:
                                tool_name = str(tool)

                            description = getattr(tool, 'description', None)
                            if not description and hasattr(tool, '__doc__'):
                                description = tool.__doc__
                            
                            if description:
                                description = description.strip().split('\n')[0]  # First line only

                            # Use the source attribute if it was set, otherwise fallback
                            server_name = getattr(tool, 'source', 'MCP Server')

                            tools_info.append({
                                "name": tool_name,
                                "description": description,
                                "source": server_name
                            })
                        except Exception as e:
                            logger.warning(f"Could not process MCP tool {tool}: {e}")
                            # Add a fallback entry with basic info
                            tools_info.append({
                                "name": f"Unknown_Tool_{len(tools_info)}",
                                "description": "MCP tool",
                                "source": "MCP Server"
                            })

            except Exception as e:
                logger.error(f"Failed to get MCP tools: {str(e)}")

        logger.info(f"✅ Found tools for user {user_id}: {tools_info}")
        return {
            "tools": tools_info,
            "total_count": len(tools_info),
            "mcp_errors": mcp_errors
        }

    except Exception as e:
        logger.error(f"Error getting tools for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving tools: {str(e)}")

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
                "Bucket": KNOWLEDGE_SOURCE_BUCKET_NAME,
                "Key": key,
                "ContentType": "application/pdf",
            },
            ExpiresIn=300,
            HttpMethod="PUT",
        )

        return {
            "presignedurl": presigned_url,
            "key": key,
            "bucket": KNOWLEDGE_SOURCE_BUCKET_NAME
        }
        
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating presigned URL: {str(e)}")

@app.delete('/session/{user_id}/{session_id}')
async def delete_session(user_id: str, session_id: str):
    prefix = f"sessions/user_{user_id}/session_{session_id}/"
    try:
        # List all objects under just the target session folder
        response = s3.list_objects_v2(Bucket=DATA_BUCKET_NAME, Prefix=prefix)
        if 'Contents' in response:
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            s3.delete_objects(
                Bucket=DATA_BUCKET_NAME,
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
        
            # Handle MCP tools with proper async context management
            if user_mcp_configs:
                # Use the async context manager to get MCP tools
                async with mcp_client_manager.get_combined_tools(user_mcp_configs) as (user_mcp_tools, clients, errors):
                    logger.info(f"Using {len(clients)} MCP clients with {len(user_mcp_tools)} tools for user {user_id}")
                    
                    # Log any MCP errors
                    if errors:
                        logger.warning(f"MCP server errors for user {user_id}: {errors}")
                    
                    # Build agent with the collected MCP tools
                    agent = build_agent_for_session(session_id, user_id, user_mcp_tools)

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
            else:
                # No MCP tools, just use base tools
                logger.info(f"Using base tools only for user {user_id}")
                agent = build_agent_for_session(session_id, user_id, [])

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