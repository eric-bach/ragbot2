import os
import boto3
import logging
import json
from typing import List, Dict, Optional
from botocore.config import Config
from dotenv import load_dotenv
from strands import Agent
from strands_tools import current_time, retrieve
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from strands.session.s3_session_manager import S3SessionManager
from strands.agent.conversation_manager import SummarizingConversationManager, SlidingWindowConversationManager
from tools.web_search import web_search
from mcp_client_manager import MCPClientManager, MCPServerConfig
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

@app.on_event("startup")
async def startup_event():
    """Initialize MCP client on startup"""
    try:
        logger.info("Initializing MCP client on startup...")
        mcp_manager.get_client()  # Initialize default client
        logger.info("MCP client initialized successfully on startup")
    except Exception as e:
        logger.warning(f"Failed to initialize MCP client on startup: {e}")
        logger.info("MCP client will be initialized on first use")

load_dotenv()
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2') # Used by the Bedrock model
BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID') 
KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID') # Used by the retrieve tool
SESSIONS_BUCKET_NAME = os.getenv('SESSIONS_BUCKET_NAME') # Used by Strands Agent sessions
KNOWLEDGE_SOURCE_BUCKET_NAME = os.getenv('KNOWLEDGE_SOURCE_BUCKET_NAME') # Used by the presigned-url endpoint
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

# Global MCP client manager with S3 support
mcp_manager = MCPClientManager(s3_client=s3, sessions_bucket_name=SESSIONS_BUCKET_NAME)

class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    query: str
    selected_tools: Optional[List[str]] = None  # List of tool names to use exclusively

class MCPServerConfigRequest(BaseModel):
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    description: str = ""

def build_agent_for_session(session_id: str, user_id: str, mcp_client: MCPClient, selected_tools: Optional[List[str]] = None) -> Agent:
    """Builds and returns a Strands Agent to a persistent session in S3 
    with conversation management"""
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
    
    # Get all available tools
    all_tools = mcp_client.list_tools_sync() + [web_search, current_time, retrieve]
    
    # Filter tools if specific tools are selected
    if selected_tools:
        # Create a map of tool names to tools for easy lookup
        tool_map = {}
        
        # Map base tools
        for tool in [web_search, current_time, retrieve]:
            if hasattr(tool, 'tool_name'):
                tool_map[tool.tool_name] = tool
            elif hasattr(tool, '__name__'):
                tool_map[tool.__name__] = tool
        
        # Map MCP tools
        for tool in mcp_client.list_tools_sync():
            tool_map[tool.tool_name] = tool
        
        # Select only the requested tools
        tools = [tool_map[tool_name] for tool_name in selected_tools if tool_name in tool_map]
        
        # If no valid tools found, fall back to all tools
        if not tools:
            logger.warning(f"No valid tools found from selection {selected_tools}, using all tools")
            tools = all_tools
    else:
        tools = all_tools

    logger.debug("selected tools", [getattr(tool, 'tool_name', getattr(tool, '__name__', str(tool))) for tool in tools])

    # Update system prompt based on selected tools
    if selected_tools:
        tool_names = [getattr(tool, 'tool_name', getattr(tool, '__name__', str(tool))) for tool in tools]
        system_prompt = f"""
        You are an AI assistant that has been instructed to use ONLY the following specific tools: {', '.join(tool_names)}.
        
        **Instructions:**
        - You MUST ONLY use the tools that have been specifically selected: {', '.join(tool_names)}
        - For EVERY user query, you MUST call and use at least one of the selected tools.
        - NEVER answer based solely on your own knowledge, even if you think you know the answer.
        - Only answer after reviewing results from the selected tools.
        - Your response must ALWAYS use the three required tags ONLY, and in Markdown format:
            - <thinking>: Explain your approach, reasoning, and tool choices from the selected tools.
            - <response>: Provide a clear, human-readable answer.
            - <sources>: List ALL tool outputs and/or sources used.
        - Do NOT output anything except these three tags.
        - Respond in a friendly, Albertan tone.
        
        **Example valid output:**
        <thinking>
        I used {tool_names[0] if tool_names else 'the selected tool'} because it was specifically chosen for this query.
        </thinking>

        <response>
        Here is the answer to your question based on the selected tools...
        </response>

        <sources>
        - {tool_names[0] if tool_names else 'selected_tool'}: [tool output summary]
        </sources>

        Always follow this response structure and do NOT skip tool calls, otherwise your response is considered invalid.
        """
    else:
        system_prompt = """
        You are an AI assistant that helps users answer any type of questions with three essential tools:
            - Web search using LinkUp API (web_search)
            - AWS documentation (MCP tools)
            - Retrieval-Augmented Generation (RAG) knowledge base (retrieve)
            
        **Thinking:**
            - For EVERY user query, your default is to use the retrieve tool.
            - If the user question is about a specific AWS service, use the AWS documentation tool.
            - If the user question requires a real-time answer (e.g. weather, stock prices, news, anything that can
            change minute-to-minute), use the web_search tool instead of the retrieve tool.
            - If you are not sure, prefer retrieve unless the query clearly matches on of the special cases above.
            - Only if the retrieve or AWS documentation tool cannot find the answer, use the web_search tool to find the answer.

        **Instructions:**
            - For EVERY user query, you MUST call and use at least one tool.
            - NEVER answer based solely on your own knowledge, even if you think you know the answer.
            - Only answer after reviewing results from all relevant tools.
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
    return {
        "STATUS": "healthy",
        "AWS_REGION": AWS_REGION,
        "KNOWLEDGE_BASE_ID": KNOWLEDGE_BASE_ID,
        "SESSIONS_BUCKET_NAME": SESSIONS_BUCKET_NAME,
        "KNOWLEDGE_SOURCE_BUCKET_NAME": KNOWLEDGE_SOURCE_BUCKET_NAME,
        "LINKUP_API_KEY": f"***{LINKUP_API_KEY[-3:]}" if LINKUP_API_KEY else "None",
    }

@app.get("/tools")
def get_tools(user_id: str = Query(None, description="User ID to get user-specific tools")):
    """Get list of available tools for the AI agent"""
    import time
    
    logger.info(f"Getting tools for user: {user_id}")
    
    base_tools = [web_search, current_time, retrieve]
    tools_info = []

    for tool in base_tools:
        try:
            # For custom tools (web_search)
            if hasattr(tool, 'tool_name'):
                tool_name = tool.tool_name
            # For strands tools (retrieve, current_time)
            elif hasattr(tool, '__name__'):
                tool_name = tool.__name__
            else:
                tool_name = str(tool)
            
            description = getattr(tool, 'description', None)
            if not description and hasattr(tool, '__doc__'):
                description = tool.__doc__
            
            if description:
                description = description.strip().split('\n')[0]  # First line only

            tools_info.append({
                "name": tool_name,
                "description": description,
                "source": "base"
            })
        except Exception as e:
            logger.warning(f"Could not process strands tool {tool}: {e}")

    # Add MCP tools with retry logic
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}: Getting MCP client for user {user_id}")
            mcp_client = mcp_manager.get_client(user_id)  # Get user-specific or default client
            logger.info(f"Got MCP client: {mcp_client is not None}")
            
            if mcp_client:
                logger.info(f"Connecting to MCP client to list tools...")
                with mcp_client:  
                    mcp_tools = mcp_client.list_tools_sync()
                    logger.info(f"Found {len(mcp_tools)} MCP tools")
                    
                    for tool in mcp_tools:
                        try:
                            # Get the tool name, description, and source
                            tool_name = tool.tool_name
                            description = tool.tool_spec["description"].strip().split('\n')[0]
                            source = "user_mcp" if user_id else "aws"
                            
                            logger.info(f"Adding MCP tool: {tool_name} (source: {source})")
                            

                            tools_info.append({
                                "name": tool_name,
                                "description": description,
                                "source": source
                            })
                        except Exception as e:
                            logger.warning(f"Could not process MCP tool {tool}: {e}")
            break  # Success, exit retry loop
            
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed to get MCP tools: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("Failed to get MCP tools after all retries")

    return {
        "tools": tools_info,
        "total_count": len(tools_info)
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

    async def generate(session_id: str, user_id: str, query: str, selected_tools: Optional[List[str]] = None):
        mcp_client = mcp_manager.get_client(user_id)  # Get user-specific client
        
        if mcp_client:
            with mcp_client:
                agent = build_agent_for_session(session_id, user_id, mcp_client=mcp_client, selected_tools=selected_tools)

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
            yield f"Error: No MCP client available for user {user_id}"

    logger.info(f"Chat request received: session_id={request.session_id}, query={request.query}, user_id={request.user_id}, selected_tools={request.selected_tools}")

    return StreamingResponse(
        generate(request.session_id, request.user_id, request.query, request.selected_tools),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx/cloudflare buffering
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )

# MCP Server Configuration Endpoints

@app.get("/mcp-configs/{user_id}")
def get_user_mcp_configs(user_id: str):
    """Get MCP server configurations for a user"""
    try:
        configs = mcp_manager.get_user_mcp_configs(user_id)
        return {
            "user_id": user_id,
            "servers": [config.to_dict() for config in configs]
        }
    except Exception as e:
        logger.error(f"Error getting MCP configs for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting MCP configs: {str(e)}")

@app.post("/mcp-configs/{user_id}")
def save_user_mcp_configs(user_id: str, configs: List[MCPServerConfigRequest]):
    """Save MCP server configurations for a user"""
    try:
        logger.info(f"Received MCP configs save request for user {user_id}")
        logger.info(f"Raw configs data: {configs}")
        
        mcp_configs = [
            MCPServerConfig(
                name=config.name,
                command=config.command,
                args=config.args,
                env=config.env,
                description=config.description
            )
            for config in configs
        ]
        
        logger.info(f"Processed {len(mcp_configs)} MCP configs for user {user_id}")
        for i, config in enumerate(mcp_configs):
            logger.info(f"Config {i+1}: {config.to_dict()}")
        
        mcp_manager.save_user_mcp_configs(user_id, mcp_configs)
        
        return {
            "message": f"MCP configs saved for user {user_id}",
            "count": len(mcp_configs)
        }
    except Exception as e:
        logger.error(f"Error saving MCP configs for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving MCP configs: {str(e)}")

@app.post("/mcp-configs/{user_id}/refresh")
def refresh_user_mcp_client(user_id: str):
    """Refresh MCP client for a user (clear cache and reinitialize)"""
    try:
        logger.info(f"Refreshing MCP client for user {user_id}")
        
        # Clear the cached client
        if hasattr(mcp_manager, '_user_clients') and user_id in mcp_manager._user_clients:
            del mcp_manager._user_clients[user_id]
            logger.info(f"Cleared cached client for user {user_id}")
        
        # Force reinitialization by getting the client
        client = mcp_manager.get_client(user_id)
        
        return {
            "message": f"MCP client refreshed for user {user_id}",
            "has_client": client is not None
        }
    except Exception as e:
        logger.error(f"Error refreshing MCP client for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error refreshing MCP client: {str(e)}")

@app.delete("/mcp-configs/{user_id}")
def delete_user_mcp_configs(user_id: str):
    """Delete MCP server configurations for a user"""
    try:
        mcp_manager.delete_user_mcp_configs(user_id)
        return {"message": f"MCP configs deleted for user {user_id}"}
    except Exception as e:
        logger.error(f"Error deleting MCP configs for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting MCP configs: {str(e)}")
