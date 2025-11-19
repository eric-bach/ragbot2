# RAGBot2 - Intelligent RAG Agent with Multi-Source Retrieval

This is an intelligent RAG (Retrieval-Augmented Generation) chatbot that combines multiple tools with MCP support to provide comprehensive answers. The agent allows contextual conversations with Bedrock Knowledge Base or additional tools like web search or supported MCP servers for additional information.

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

### ChatBot

- **User Session Management**: Uses Strands Agents to manage user conversation sessions
- **Streaming Responses**: Fully streaming of chat responses to user

## Architecture

![architecture](/docs/architecture.png)

## Getting Started

The project is structured into 3 folders:

```
/ragbot2/
└── backend/
    ├── agent/                    # Strands Agent server code
        ├── agent.py              # Entry point for the application
        ├── main.py               # FastAPI app configuration and setup
        ├── config.py             # Environment variables and AWS client configuration
        ├── .env                  # Environment file required for running locally
        ├── services/             # Business logic modules
        │   ├── agent_service.py  # Agent building and tool management logic
        │   ├── mcp_client_manager.py  # MCP client management
        │   └── mcp_config_store.py    # MCP configuration storage
        ├── routes/               # API endpoint modules (organized by functionality)
        │   ├── health.py         # Health check and basic info endpoints
        │   ├── chat.py           # Chat streaming endpoints
        │   ├── tools.py          # Tool listing and discovery endpoints
        │   ├── sessions.py       # Session management endpoints
        │   ├── files.py          # File upload and presigned URL endpoints
        │   └── mcp_config.py     # MCP server configuration endpoints
        ├── models/               # Pydantic data models
        └── tools/                # Custom tool implementations
└── frontend/                     # NextJS frontend chatbot UI
    ├── .env.local               # Environment file for frontend client
└── infrastructure/              # CDK code to deploy AWS resources (*Amazon Bedrock Knowledge Bases S3 Vectors is not supported yet so this needs to be manually created)
    ├── .env                     # Environment file required for deploying backend resources
```

### Backend Architecture

The backend follows Python best practices with a modular structure:

- **`agent.py`**: Simple entry point that imports the FastAPI app from `main.py`
- **`main.py`**: Central application setup, FastAPI configuration, and route registration
- **`config.py`**: Centralized configuration management for environment variables and AWS clients
- **`services/`**: Business logic separated from API concerns
  - Agent building, tool processing, and system prompt generation
  - MCP client and configuration management
- **`routes/`**: API endpoints organized by functionality for better maintainability
  - Each route module handles a specific domain (health, chat, tools, etc.)
  - Enables easy testing and modification of individual endpoint groups
- **`models/`**: Pydantic data models for request/response validation
- **`tools/`**: Custom tool implementations for the AI agent

This structure provides:

- **Separation of Concerns**: Each module has a single responsibility
- **Maintainability**: Easy to locate and modify specific functionality
- **Testability**: Individual components can be unit tested in isolation
- **Scalability**: Simple to add new endpoints or modify existing ones

#### Deploying to AWS

The CDK infrastructure will create 2 stacks

- `ragbot2-data` - stateful resources containing VPC, Cognito, S3 buckets
- `ragbot2-app` - stateless resources containing Lambda, ECS, ALB, API GW

1. Run the Python virtual environment

   ```
   cd infrastructure

   python -m venv .venv
   ```

2. Install requirements

   ```
   pip install -r requirements.txt
   ```

3. Deploy the backend

   ```
   ./deploy.sh
   ```

   - or -

   ```
   cdk deploy --all --profile observability2
   ```

4. The frontend is deployed with Vercel (AWS Amplify does not support streaming responses)

#### Cross-Account Billing and Cost Analysis Setup

RAGBot2 includes an AWS MCP server that can query billing, cost data, and resource information. To enable cross-account access (querying billing data from multiple AWS accounts), you need to set up IAM roles in each target account using the provided CloudFormation template.

### Deployment Steps

1. **Log into the target AWS account's console**
2. **Navigate to CloudFormation** → Create Stack → With new resources
3. **Upload template**: Select `infrastructure/cross-account-billing-role.yaml`
4. **Configure parameters**:
   - **Stack name**: `mcp-billing-role` (or your preferred name)
   - **TrustedAccountId**: `761018860881` (replace with your main account ID)
   - **ECSTaskRoleNamePrefix**: `ragbot2-app-ECSTaskRole` (leave as default)
5. **Acknowledge IAM resource creation** (required checkbox)
6. **Deploy the stack**

Repeat these steps for each AWS account you want to query billing data from.

### What Gets Created

The CloudFormation template creates:

- **IAM Role**: `MCPBillingRole-{AccountId}` with cross-account trust relationship
- **Managed Policies**:
  - AmazonEC2ReadOnlyAccess
  - AmazonRDSReadOnlyAccess
  - AWSLambda_ReadOnlyAccess
  - ComputeOptimizerReadOnlyAccess
- **Inline Policy**: Additional permissions for:
  - Cost Explorer (ce:\*) - billing and cost data
  - Cost Optimization Hub - cost optimization recommendations
  - Budgets - budget viewing
  - Pricing API - AWS service pricing
  - Trusted Advisor - optimization checks
  - CloudFormation - stack information

#### Running the agent locally

1. Create a `.env` file in the `/backend/agent` folder

   ```
   AWS_PROFILE=
   AWS_REGION=
   BEDROCK_MODEL_ID=
   KNOWLEDGE_BASE_ID=
   DATA_BUCKET_NAME=
   KNOWLEDGE_SOURCE_BUCKET_NAME=
   LINKUP_API_KEY=
   ```

2. Build and run the docker container

   ```
   cd `/backend/agent`

   ./run_local_agent.sh
   ```

   - or -

   ```
   docker build -t ragbot-agent .
   docker run --rm --interactive --env-file .env -v //c/Users/eric.bach/.aws:/root/.aws -p 8000:8000 ragbot-agent
   ```

3. Create a `.env.local` file in the `/frontend` folder

   ```
   NEXT_PUBLIC_COGNITO_USER_POOL_ID=
   NEXT_PUBLIC_COGNITO_CLIENT_ID=
   NEXT_PUBLIC_BACKEND_URL=
   NEXT_PUBLIC_TURNSTILE_SITE_KEY=
   ```

4. Run the frontend

   ```
   cd frontend

   npm run dev
   ```

#### Testing the backend API

**Testing the backend API running locally**

Backend

```
curl -X GET http://localhost:8000/health
curl -X GET http://localhost:8000/tools
curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{"query": "What is AWS Lambda?", "session_id": "1", "user_id": "1"}'
curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{"query": "What is the weather like today in Seattle?", "session_id": "1", "user_id": "1"}'
```

Frontend

```
curl -X POST http://localhost:3000/api/chat -H 'Content-Type: application/json' -d '{"query": "What is the weather like in Paris", "session_id": "test", "user_id": "test"}' --no-buffer
```

**Testing the backend API running in AWS**

Backend

```
curl -X GET https://ragbot2-public.ericbach.dev/health
curl -X GET https://ragbot2-public.ericbach.dev/tools
curl -X POST https://ragbot2-public.ericbach.dev/chat -H 'Content-Type: application/json' -d '{"query": "How many GSIs can I have in a DynamoDB table?", "session_id": "1", "user_id": "1"}'
curl -X POST https://ragbot2-public.ericbach.dev/chat -H 'Content-Type: application/json' -d '{"query": "What is the weather like today in Edmonton?", "session_id": "1", "user_id": "1"}'
```

Frontend

```
curl -X POST https://ragbot2-public.ericbach.dev/chat -H 'Content-Type: application/json' -d '{"query": "What is the weather like in Paris", "session_id": "test", "user_id": "test"}' --no-buffer
```

## Troubleshooting

**Check what headers Cloudflare is returning**

```
# Get the Cloudflare proxy IP addresses
nslookup ragbot2-public.ericbach.dev 8.8.8.8

# Check what headers Cloudflare is returning using one of the proxy IP addresses
curl -v https://ragbot2-public.ericbach.dev/health --resolve ragbot2-public.ericbach.dev:443:172.67.210.169 2>&1 | grep -E "(CF-|X-|>|<)"
```

## How It Works

RAGBot 2 agent uses an intelligent multi-step approach to answer your questions:

1. **Knowledge Base Search**: First queries your AWS Bedrock knowledge base using the `retrieve` tool
2. **Relevance Evaluation**: Evaluates if the retrieved chunks are relevant to your question
3. **Web Search**: If knowledge base results aren't relevant, performs `web search` using LinkUp API
4. **MCP Servers**: If query is related to AWS, performs a lookup in the `AWS Documentation MCP Server`
5. **Comprehensive Response**: Combines information from multiple sources to provide complete answers

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

## Pricing

Estimated monthly costs (USD) for running in an AWS account:

| Service                   | Rate (us-west-2)            | Quantity | Estimated cost     |
| ------------------------- | --------------------------- | -------- | ------------------ |
| Elastic Load Balacing     | $0.0225 per hour            | 720      | $16.20             |
| VPC public IPv4           | $0.005 per hour             | 720      | $3.60              |
| ECS Fargate (Memory)      | $0.00356 per hour           | 280      | $1.00 (estimated)  |
| Route 53                  | $0.50 per Hosted Zone       | 1        | $0.50              |
| ECS Fargate (vCPU)        | $0.03238 per hour           | 75       | $2.50 (estimated)  |
| Bedrock (Claude 4 Sonnet) | $3.00 per 1M input tokens   | 1        | $3.00 (estimated)  |
| Bedrock (Claude 4 Sonnet) | $15.00 per 1M output tokens | 1        | $15.00 (estimated) |
| S3                        | $0.023 per GB               | 2        | $0.05 (estimated)  |
| **TOTAL (estimated)**     |                             |          | **$41.85**         |

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
