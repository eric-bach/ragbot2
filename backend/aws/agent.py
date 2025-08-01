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
    #model_id="us.anthropic.claude-sonnet-4-20250514-v1:0", # Slow, but most accurate
    model_id="amazon.nova-lite-v1:0", # Very fast, but not good enough for production
    #model_id="amazon.nova-pro-v1:0", # Fast and fairly good
    boto_session=session
)

class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    query: str

def build_agent_for_session(session_id: str, user_id: str, mcp_client: MCPClient) -> Agent:
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
    
    tools = mcp_client.list_tools_sync() + [web_search, http_request, retrieve]

    logger.debug("tools", tools)

    return Agent(
        agent_id="ragbot2",
        system_prompt="""
        You are an AI chatbot with three essential tools:
            - Web search using LinkUp API (web_search)
            - AWS documentation (MCP tools)
            - Retrieval-Augmented Generation (RAG) knowledge base (retrieve)
            
        **Instructions:**
        - For EVERY user query, you MUST call and use at least one tool (never answer from your own knowledge, 
        even if you think you know the answer).
        - Do NOT respond until you have attempted to use all relevant tools. Only answer after reviewing tool outputs.
        - NEVER answer from your training data or general world knowledge alone. Every answer MUST reference tool 
        outputs.
        - Your reply must ALWAYS use EXACTLY the following three tags in Markdown format:
            - <thinking>: Briefly explain your approach and reasoning.
            - <response>: Provide a clear, human-readable answer. Do NOT include any links, citations, URLs, or attribution here.
            - <sources>: List ALL tool outputs or sources used.
        - If you cannot get results from any tool, state this honestly IN the <response> tag - do not answer from memory.
        - Do NOT output anything except the three required tags.  Do NOT use your own knowledge in the <response> section.
        
        **Formatting Violations:**
        Incorrect outputs include:
        - Plain text without the three markdown tags.
        - Any direct answer not based on tool usage.
        - Repetition of tag sections or extra formatting/tags.

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

        If you violate any of the above formatting rules or attempt to answer from your knowledge, consider your response invalid.

        Always follow these steps and do NOT skip tool calls or format requirements.
        """,
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
        "SOURCE_BUCKET_NAME": SOURCE_BUCKET_NAME,
        "LINKUP_API_KEY": f"***{LINKUP_API_KEY[-3:]}",
    }

@app.get("/tools")
def get_tools():
    """Get list of available tools for the AI agent"""
    aws_documentation_mcp_client = MCPClient(lambda: stdio_client(
        StdioServerParameters(
            command="uvx", 
            args=["awslabs.aws-documentation-mcp-server@latest"]
        )
    ))

    with aws_documentation_mcp_client:
        aws_tools = aws_documentation_mcp_client.list_tools_sync()
        all_tools = aws_tools + [web_search, http_request, retrieve]
        
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
        aws_documentation_mcp_client = MCPClient(lambda: stdio_client(
            StdioServerParameters(
                command="uvx", 
                args=["awslabs.aws-documentation-mcp-server@latest"]
            )
        ))
        
        with aws_documentation_mcp_client:
            agent = build_agent_for_session(session_id, user_id, mcp_client=aws_documentation_mcp_client)

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

    logger.info(f"Chat request received: session_id={request.session_id}, query={request.query}, user_id={request.user_id}")

    return StreamingResponse(
        generate(request.session_id, request.user_id, request.query),
        media_type="text/plain"
    )
