import boto3
import os
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel
from strands_tools import http_request, retrieve
from strands.tools.mcp import MCPClient
from strands.agent.conversation_manager import SummarizingConversationManager, SlidingWindowConversationManager
from mcp import stdio_client, StdioServerParameters
from tools.web_search import web_search

load_dotenv()
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID')
KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID')

# Create session without profile for ECS deployment
session = boto3.Session(region_name=AWS_REGION)

# Create a Bedrock model with the custom session
bedrock_model = BedrockModel(
    model_id=BEDROCK_MODEL_ID,
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
    conversation_manager = SlidingWindowConversationManager(
        window_size=10
    )

    with aws_documentation_mcp_client:
        tools = aws_documentation_mcp_client.list_tools_sync()
        tools += [web_search, http_request, retrieve]

        agent = Agent(
            agent_id="ragbot2",
            system_prompt="""
            You are an AI assistant that helps users answer any type of questions with three essential tools:
                - Web search using LinkUp API (web_search)
                - AWS documentation (MCP tools)
                - Retrieval-Augmented Generation (RAG) knowledge base (retrieve)
                
            **Instructions:**
            - For EVERY user query, you MUST call and use at least one tool (never answer from your own knowledge, 
            even if you think you know the answer).
            - Only answer after reviewing results from all relevant tools.
            - NEVER answer based solely on your internal knowledge.
            - Your response must ALWAYS use the three required tags ONLY, and in Markdown format:
                - <thinking>: Explain your approach, reasoning, and tool choices.
                - <response>: Provide a clear, human-readable answer.
                - <sources>: List ALL tool outputs and/or sources used.
            - If you cannot get results from any tool, state this honestly IN the <response> tag - do not answer from memory.
            - Do NOT output anything except these three tags.
            
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