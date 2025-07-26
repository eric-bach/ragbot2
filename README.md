# RAGBot2 - Intelligent RAG Agent with Multi-Source Retrieval

This is an intelligent RAG (Retrieval-Augmented Generation) chatbot that combines multiple information sources to provide comprehensive answers. The agent first searches your knowledge base using AWS Bedrock, evaluates relevance, and falls back to web search when needed.

## Setup

### Quick Setup (Recommended)

Run the interactive setup script:

```bash
python setup.py
```

This will:

- Check and install dependencies
- Prompt you for your LinkUp API key
- Create a `.env` file with your configuration

### Manual Setup

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Configure API Credentials and AWS Resources

**Option A: Create a .env file (Recommended)**
Create a `.env` file in your project root:

```bash
# LinkUp API Configuration
LINKUP_API_KEY=your_actual_linkup_api_key

# AWS Configuration
AWS_PROFILE=bach-dev
AWS_REGION=us-east-1

# Bedrock Knowledge Base Configuration
KNOWLEDGE_BASE_ID=your_knowledge_base_id
```

**Option B: Set Environment Variables**

Linux/macOS:

```bash
export LINKUP_API_KEY=your_linkup_api_key
```

Windows (PowerShell):

```powershell
$env:LINKUP_API_KEY="your_linkup_api_key"
```

Windows (Command Prompt):

```cmd
set LINKUP_API_KEY=your_linkup_api_key
```

#### 3. Configure AWS Resources

**AWS Credentials**: Make sure you have AWS credentials configured for the `bach-dev` profile, or update the profile name in `agent.py`.

**Bedrock Knowledge Base**:

- Create a knowledge base in AWS Bedrock with your documents
- Note the Knowledge Base ID and add it to your `.env` file
- Ensure your AWS profile has permissions to access Bedrock and your knowledge base

## How It Works

The RAGBot2 agent uses an intelligent multi-step approach to answer your questions:

1. **Knowledge Base Search**: First queries your AWS Bedrock knowledge base using the `retrieve` tool
2. **Relevance Evaluation**: Evaluates if the retrieved chunks are relevant to your question
3. **Web Search Fallback**: If knowledge base results aren't relevant, performs web search using LinkUp API
4. **Comprehensive Response**: Combines information from multiple sources to provide complete answers

## Usage

Run the interactive agent:

```bash
python agent.py
```

### Available Tools

1. **retrieve**: Search AWS Bedrock knowledge bases for relevant information

   - Automatically queries your configured knowledge base
   - Returns relevant document chunks with metadata

2. **web_search**: Perform web searches using LinkUp's Web Search API

   - Parameters: query (search query to perform)
   - Returns: Sourced answers with references from LinkUp API
   - Used as fallback when knowledge base doesn't have relevant information

3. **AWS Documentation**: Lookup AWS documentation (from aws-documentation-mcp-server)
   - Access comprehensive AWS service documentation
   - Get up-to-date information about AWS features and APIs

### Example Usage

The agent intelligently handles various types of questions:

**Knowledge Base Questions** (searches your documents first):

- "What does our company policy say about remote work?"
- "How do we handle customer refunds?"
- "What are the technical specifications for our product?"

**Web Search Questions** (when knowledge base lacks information):

- "What's the latest news about artificial intelligence?"
- "Find current Python programming best practices"
- "What is the current price of bitcoin?"

**AWS Documentation Questions**:

- "How do I configure an S3 bucket policy?"
- "What are the latest Lambda runtime versions?"
- "Explain AWS IAM roles and policies"

## Key Features

### RAG (Retrieval-Augmented Generation)

- **Knowledge Base Integration**: Seamlessly searches your AWS Bedrock knowledge base
- **Intelligent Fallback**: Automatically switches to web search when knowledge base lacks relevant information
- **Relevance Evaluation**: Uses advanced scoring to determine if retrieved information is relevant

### LinkUp Web Search API

- **Comprehensive Results**: Access to up-to-date web search results
- **Sourced Answers**: Results include source references for verification
- **Standard Depth**: Provides thorough search coverage
- **Structured Output**: Results formatted for easy consumption by the AI agent

### AWS Integration

- **Bedrock Knowledge Bases**: Query your private document collections
- **AWS Documentation**: Access comprehensive AWS service documentation
- **Multi-Model Support**: Uses Amazon Nova Micro for efficient processing

## Error Handling

The agent includes comprehensive error handling for:

- Missing API credentials (LinkUp and AWS)
- Network timeouts and connection issues
- API rate limits and quota exceeded errors
- Invalid responses from knowledge base or web search
- AWS authentication and permission issues

## Requirements & Notes

### Prerequisites

- **AWS Account**: With Bedrock access and a configured knowledge base
- **LinkUp API Subscription**: Paid subscription required for web search functionality
- **Docker**: Required for AWS documentation MCP server

### Important Notes

- LinkUp API calls are rate-limited based on your subscription plan
- The agent preserves your original questions when querying the knowledge base
- Automatic container cleanup prevents Docker resource leaks
- Results are optimized for AI agent consumption and human readability

## Architecture

The agent uses AWS Strands framework with:

- **BedrockModel**: Amazon Nova Micro for efficient text generation
- **MCP Integration**: Model Context Protocol for AWS documentation access
- **Multi-Tool Orchestration**: Seamless switching between knowledge sources
- **Session Management**: Maintains context across interactions
