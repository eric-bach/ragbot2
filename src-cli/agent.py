import boto3
import os
import atexit
import subprocess
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel
from strands_tools import http_request, retrieve
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from tools.web_search import web_search

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

def cleanup_orphaned_containers():
    """Clean up any orphaned AWS documentation MCP containers"""
    try:
        # Find and stop any running containers with our image
        result = subprocess.run(
            ["docker", "ps", "--filter", "ancestor=awslabs/aws-documentation-mcp-server:latest", "--format", "{{.ID}}"],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            container_ids = result.stdout.strip().split('\n')
            for container_id in container_ids:
                if container_id:
                    subprocess.run(["docker", "stop", container_id], 
                                 capture_output=True, timeout=5)
    except:
        pass

# Register cleanup function to run on exit
atexit.register(cleanup_orphaned_containers)

aws_documentation_mcp_client = MCPClient(
    lambda: stdio_client(StdioServerParameters(
        command="docker",
        args=[
            "run",
            "--rm",
            "--interactive",
            "--env", f"AWS_REGION={AWS_REGION}",
            "--env", "FASTMCP_LOG_LEVEL=ERROR",
            "awslabs/aws-documentation-mcp-server:latest"
        ]
    ))
)

def interactive_session():
    with aws_documentation_mcp_client:
        tools = aws_documentation_mcp_client.list_tools_sync()
        tools += [web_search, http_request, retrieve]

        while True:
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
                model=bedrock_model
            )

            # Get user input
            user_input = input("\n\n🤖 How can I help you?\n")

            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break

            # Send the input to the agent
            agent(user_input, )

if __name__ == "__main__":
    interactive_session()