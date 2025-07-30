import os
import boto3
import logging
from dotenv import load_dotenv
from strands import Agent
from strands_tools import http_request, retrieve
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from tools.web_search import web_search
from fastapi import FastAPI, HTTPException
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
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID')

# Create session without profile for ECS deployment
session = boto3.Session(region_name=AWS_REGION)

# Create a Bedrock model with the custom session
bedrock_model = BedrockModel(
    #model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    model_id="amazon.nova-micro-v1:0",
    boto_session=session
)

aws_documentation_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=["awslabs.aws-documentation-mcp-server@latest"]
    )
))

class ChatRequest(BaseModel):
    query: str

@app.get("/")
def home():
    return {"RAGBot": "v2"}

@app.get("/health")
def health():
    return {
        "STATUS": "healthy",
        "AWS_REGION": os.getenv('AWS_REGION'),
        "KNOWLEDGE_BASE_ID": os.getenv('KNOWLEDGE_BASE_ID'),
        "LINKUP_API_KEY": f"***{os.getenv('LINKUP_API_KEY')[-3:]}"
    }

@app.get("/tools")
def get_tools():
    """Get list of available tools for the AI agent"""
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

@app.post('/chat')
def chat(request: ChatRequest):
    async def generate(query: str):
        with aws_documentation_mcp_client:
            tools = aws_documentation_mcp_client.list_tools_sync()
            tools += [web_search, http_request, retrieve]

            agent = Agent(
                system_prompt="""
                You are a chatbot that answers questions with the following capabilities:
                    - Web search using LinkUp API
                    - AWS documentation lookup
                    - Bedrock knowledge bases for specific topics

                When answering questions that request timely, real-world, or dynamic information (such as current
                weather, stock prices, or news), use the web search tool directly, as the knowledge base does not
                contain up-to-date information. Otherwise, always try to use the knowledge base first before using 
                the web search tool.
                For questions about AWS, use the AWS documentation tool.
                
                Your output MUST follow this format, using ONLY these tags:
                    - <thinking>: Reflect on your approach and reasoning.
                    - <response>: Only provide your human-readable answer here. Do NOT include any source links, 
                    citations, URLs, or attribution phrases.
                    - <sources>: List all sources used to answer the question (URLs, document IDs, markdown links, etc).
                    Place all source details ONLY here, and nowhere else.
                Do NOT use any other tags or formats.
                
                Always separate each section (<thinking>, <response>, <sources>) cleanly.
                """,
                tools=tools,
                model=bedrock_model,
                callback_handler=None
            )

            try:
                agent_stream = agent.stream_async(request.query)
                
                chunk_count = 0
                async for event in agent_stream:
                    if "data" in event:
                        # Only stream text chunks to the client
                        chunk_count += 1
                        if chunk_count % 60 == 0:  # Log every 60th chunk
                            logger.info(f"Streamed {chunk_count} chunks so far")
                        yield event['data']
                logger.info(f"Streaming response complete - total chunks: {chunk_count}")
            except Exception as e:
                logger.error(f"Error in agent stream: {str(e)}")
                yield f"Error: {str(e)}"

        if not request.query:
            raise HTTPException(status_code=400, detail="No query provided")
    
    try:
        logger.info(f"Chat request received: {request.query}")

        return StreamingResponse(
            generate(request.query),
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))