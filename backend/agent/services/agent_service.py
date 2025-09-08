"""
Agent service module containing business logic for building and managing Strands agents.
"""
import json
import logging
from typing import List, Optional
from strands import Agent
from strands.session.s3_session_manager import S3SessionManager
from strands.agent.conversation_manager import SlidingWindowConversationManager
from config import (
    BASE_TOOLS, 
    DATA_BUCKET_NAME, 
    AWS_REGION, 
    get_boto_session, 
    get_bedrock_model
)

logger = logging.getLogger(__name__)

def build_agent_for_session(session_id: str, user_id: str, user_mcp_tools: Optional[List] = None) -> Agent:
    """
    Builds and returns a Strands Agent with conversation management and pre-collected MCP tools.
    
    Args:
        session_id: Unique session identifier
        user_id: User identifier
        user_mcp_tools: List of user-configured MCP tools (default: empty list)
    
    Returns:
        Configured Agent instance
    """
    logger.info(f"⚙️ Building agent for session {session_id}, user {user_id}")

    if user_mcp_tools is None:
        user_mcp_tools = []
        
    session = get_boto_session()
    bedrock_model = get_bedrock_model()
    
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

    for i, tool in enumerate(tools):
        logger.debug(f"Adding tool {i}: {json.dumps({'Type': str(type(tool)), 'Name': getattr(tool, 'name', getattr(tool, 'tool_name', 'unknown')), 'Description': getattr(tool, 'description', getattr(tool, '__doc__', 'no description'))})}")

    # Build dynamic system prompt that includes information about available MCP tools
    system_prompt = build_system_prompt(user_mcp_tools)

    logger.info(f"✅ Agent built successfully with {len(tools)} tools and session id {session_id}")

    return Agent(
        agent_id="ragbot2",
        system_prompt=system_prompt,
        tools=tools,
        model=bedrock_model,
        session_manager=session_manager,
        conversation_manager=conversation_manager,
        callback_handler=None
    )

def build_system_prompt(user_mcp_tools: List) -> str:
    """
    Build a dynamic system prompt that includes information about available MCP tools.
    
    Args:
        user_mcp_tools: List of user-configured MCP tools
    
    Returns:
        Formatted system prompt string
    """
    base_tools_description = """
    - RAG Knowledge Base retrieval (retrieve): Search user-uploaded documents and private knowledge
    - Web search using LinkUp API (web_search): Search current web information
    - Getting the current date and time (current_time): For time-sensitive queries"""
    
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

    system_prompt = f"""You are an AI assistant that helps users answer questions by leveraging multiple information sources.
You have access to the following tools:{base_tools_description}{mcp_tools_description}

**CRITICAL Tool Selection Strategy:**
1. **ALWAYS start with Knowledge Base**: For ANY question that could be answered by user documents, company information, or previously uploaded content, ALWAYS call the 'retrieve' tool FIRST
2. **Knowledge Base Priority**: The retrieve tool contains user-uploaded documents that are likely the most relevant and authoritative source for the user's specific context
3. **Supplement with additional tools**: After checking the knowledge base, use other tools to supplement or verify information:
   - Use web_search for current events, real-time data, or when knowledge base lacks information
   - Use MCP tools for specialized functionality relevant to the query
   - Use current_time for time-sensitive questions
4. **Multi-tool approach**: Combine results from multiple tools when beneficial - knowledge base insights enhanced with web search or MCP tool data often provide the most comprehensive answers

**Instructions:**
    - You MUST call at least one tool for EVERY query - never rely solely on your training data
    - For questions that could relate to user documents: ALWAYS call 'retrieve' first, then supplement with other tools as needed
    - Prioritize user's private knowledge base content over general web information when both are available
    - Use MCP server tools when they provide specialized functionality relevant to the query
    - If knowledge base results are insufficient or empty, explain this and rely more heavily on other tools

**Response Format:**
    - Your response must ALWAYS use the three required tags ONLY, and in Markdown format:
        - <thinking>: Explain your tool selection strategy, why you chose each tool, and how you integrated the results
        - <response>: Provide a comprehensive answer that prioritizes knowledge base findings while incorporating other relevant information
        - <sources>: List ALL tools used and their key contributions, clearly distinguishing between knowledge base and external sources
    - Do NOT output anything except these three tags.
    - Respond in a friendly, Albertan tone.
            
**Example valid output:**
<thinking>
I'll start by searching the knowledge base for any relevant user documents about this topic, then supplement with web search for current information and use the MCP tool for specialized analysis.
</thinking>

<response>
Based on your uploaded documents and current information, here's what I found... [prioritize knowledge base findings, then integrate other sources]
</response>

<sources>
- retrieve: [specific documents/content found in knowledge base]
- web_search: [current web information]
- [mcp_tool_name]: [specialized tool output]
</sources>

Always follow this response structure and tool selection strategy - prioritize user's knowledge base, then enhance with other sources.
        """
    
    return system_prompt

def get_base_tools_info() -> List[dict]:
    """
    Get information about base tools available to all agents.
    
    Returns:
        List of dictionaries containing tool information
    """
    logger.info("⚙️ Getting base tools")

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
    
    logger.info(f"🛠️ Found {len(tools_info)} base tools")

    return tools_info

def process_mcp_tools_info(user_tools: List) -> List[dict]:
    """
    Process MCP tools and extract their information for API responses.
    
    Args:
        user_tools: List of MCP tools
    
    Returns:
        List of dictionaries containing MCP tool information
    """
    tools_info = []
    
    for i, tool in enumerate(user_tools):
        try:
            # Debug logging to understand tool structure
            logger.debug(f"⚙️ Processing MCP tool: {tool}")
            
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

            logger.debug(f"Processed MCP tool: {json.dumps({'name': tool_name, 'description': description, 'source': server_name})}")

            tools_info.append({
                "name": tool_name,
                "description": description,
                "source": server_name
            })
        except Exception as e:
            logger.warning(f"🛑 Could not process MCP tool {tool}: {e}")
            # Add a fallback entry with basic info
            tools_info.append({
                "name": f"Unknown_Tool_{len(tools_info)}",
                "description": "MCP tool",
                "source": "MCP Server"
            })
    
    logger.info(f"Processed {tools_info.count} MCP tools")
    return tools_info
