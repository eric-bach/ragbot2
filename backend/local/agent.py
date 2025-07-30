import boto3
import os
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel
from strands_tools import http_request, retrieve
from strands.tools.mcp import MCPClient
from strands.agent.conversation_manager import SummarizingConversationManager
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

# # For macOS/Linux:
# aws_documentation_mcp_client = MCPClient(lambda: stdio_client(
#     StdioServerParameters(
#         command="uvx", 
#         args=["awslabs.aws-documentation-mcp-server@latest"]
#     )
# ))

# For Windows:
aws_documentation_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=[
            "--from", 
            "awslabs.aws-documentation-mcp-server@latest", 
            "awslabs.aws-documentation-mcp-server.exe"
        ]
    )
))

def interactive_session():
    # create conversation manager
    conversation_manager = SummarizingConversationManager(
        summary_ratio=0.3,
        preserve_recent_messages=10
    )

    with aws_documentation_mcp_client:
        tools = aws_documentation_mcp_client.list_tools_sync()
        tools += [web_search, http_request, retrieve]

        agent = Agent(
            agent_id="ragbot2",
            system_prompt="""
            You are a chatbot that answers questions with the following capabilities:
                - Web search using LinkUp API
                - AWS documentation lookup
                - Bedrock knowledge bases for specific topics

            When answering questions that request timely, real-world, or dynamic information (such as current
            weather, stock prices, or news), use the web search tool directly, as the knowledge base does not
            contain up-to-date information.
            For questions asking about company policies, internal knowledge, procedures, or static information,
            check the knowledge base first.
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
            conversation_manager=conversation_manager
        )

        while True:
            user_input = input("\n\n🤖 How can I help you?\n")
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break

            # Send the input to the agent
            agent(user_input)

if __name__ == "__main__":
    interactive_session()