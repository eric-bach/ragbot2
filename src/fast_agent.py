import os
import boto3
from dotenv import load_dotenv
from strands import Agent
from strands_tools import http_request, retrieve
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from tools.web_search import web_search
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    query: str

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

@app.get("/")
def home():
    return {"RAGBot": "v2"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/debug")
def debug_env():
    return {
        "AWS_REGION": os.getenv('AWS_REGION'),
        "KNOWLEDGE_BASE_ID": os.getenv('KNOWLEDGE_BASE_ID'),
        "LINKUP_API_KEY": "***" if os.getenv('LINKUP_API_KEY') else None
    }

async def chat_stream_response(query: str):
    with aws_documentation_mcp_client:
        tools = aws_documentation_mcp_client.list_tools_sync()
        tools += [web_search, http_request, retrieve]

        agent = Agent(
            system_prompt="""
            You are a chatbot with RAG capabilities that can answer questions and help with tasks. 
            
            When a user asks you a question, you will first check it in your knowledge base. 
            You will evaluate if the returned chunks are relevant using a relevance score tool.

            You have access to:
                - Web search capabilities through LinkUp API
                - Lookup AWS documentation
                - Retrieve information from Bedrock knowledge bases

            Use the retrieve tool to search Bedrock knowledge bases about information on Cars
            Use the aws-documentation-mcp-server to get information on AWS documentation
            Use the web_search tool for web searches
            """,
            tools=tools,
            model=bedrock_model,
            callback_handler=None
        )

        async for item in agent.stream_async(query):
            if "data" in item:
                yield item['data']

@app.post('/chat')
def chat(request: ChatRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="No query provided")
    
    try:
        return StreamingResponse(
            chat_stream_response(request.query),
            media_type="text/plain"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))