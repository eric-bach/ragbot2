import os
import boto3
import json
from datetime import datetime
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

@app.post('/test-stream')
def test_stream():
    """Simple streaming test without MCP client or Bedrock"""
    def simple_generator():
        import time
        for i in range(5):
            yield f"Chunk {i}: Hello from ECS!\n"
            time.sleep(0.5)  # Small delay to simulate streaming
    
    return StreamingResponse(simple_generator(), media_type="text/plain")

@app.post('/test-bedrock')
def test_bedrock(request: ChatRequest):
    """Test Bedrock model without streaming"""
    try:
        # Test if bedrock model works at all
        client = session.client('bedrock-runtime', region_name=AWS_REGION)
        
        # Correct payload format for Nova models
        payload = {
            "schemaVersion": "messages-v1",
            "messages": [
                {
                    "role": "user", 
                    "content": [
                        {"text": "Who was the 40th president of the United States?"}
                    ]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 300,
                "temperature": 0.5
            }
        }
        
        response = client.invoke_model(
            modelId="amazon.nova-micro-v1:0",
            body=json.dumps(payload),
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response.get('body').read())
        return {"response": result, "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}
    

@app.post('/test-bedrock-stream')
def test_bedrock_stream(request: ChatRequest):
    """Test Bedrock model with streaming"""
    def bedrock_stream_generator():
        try:
            # Test if bedrock model works at all
            client = session.client('bedrock-runtime', region_name=AWS_REGION)
            
            # Correct payload format for Nova models
            payload = {
                "schemaVersion": "messages-v1",
                "messages": [
                    {
                        "role": "user", 
                        "content": [
                            {"text": "Who was the 40th president of the United States?"}
                        ]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 300,
                    "temperature": 0.5
                }
            }

            start_time = datetime.now()
            
            response = client.invoke_model_with_response_stream(
                modelId="amazon.nova-micro-v1:0",
                body=json.dumps(payload)
            )
            
            request_id = response.get("ResponseMetadata").get("RequestId")
            print(f"Request ID: {request_id}")
            print("Awaiting first token...")
            
            chunk_count = 0
            time_to_first_token = None

            # Process the response stream
            stream = response.get("body")
            if stream:
                for event in stream:
                    chunk = event.get("chunk")
                    if chunk:
                        # Print the response chunk
                        chunk_json = json.loads(chunk.get("bytes").decode())
                        content_block_delta = chunk_json.get("contentBlockDelta")
                        if content_block_delta:
                            if time_to_first_token is None:
                                time_to_first_token = datetime.now() - start_time
                                print(f"Time to first token: {time_to_first_token}")

                            chunk_count += 1
                            text_chunk = content_block_delta.get("delta").get("text")
                            print(text_chunk, end="")  # Still print to console for debugging
                            yield text_chunk  # Yield the chunk to the client
                print(f"\nTotal chunks: {chunk_count}")
            else:
                yield "No response stream received."
        except Exception as e:
            print(f"Error in stream: {str(e)}")
            yield f"Error: {str(e)}"
    
    return StreamingResponse(bedrock_stream_generator(), media_type="text/plain")
    

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