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
    ├── aws/            # Strands Agent server code
         ├── .env       # .env file required for running locally
    └── local/          # Local Strands Agent for local testing
         ├── .env       # .env file required for running locally
└── frontend/           # NextJS frontend chatbot UI
    ├── .env.local      # .env file for frontend client
└── infrastructure/     # CDK code to deploy AWS resources (*Amazon Bedrock Knowledge Bases S3 Vectors is not supported yet so this needs to be manually created)
    ├── .env            # .env file required for deploying backend resources
```

### Backend

1. Install Dependencies

```bash
cd infrastructure
pip install -r requirements.txt
```

2. Configure Backend Environment Variables

Create a `.env` file in the `infrastructure/` folder:

```bash
# AWS Configuration
AWS_REGION=your_aws_region

# Bedrock Knowledge Base Configuration (this needs to be manually created in the AWS Console outside of CDK since it's not supported yet)
KNOWLEDGE_BASE_ID=your_knowledge_base_id
KNOWLEDGE_BASE_DATA_SOURCE_ID=your_knowledge_base_data_source_id

# SSL Certificate for ALB
CERTIFICATE_ARN=your_certificate_arn

# LinkUp API Configuration
LINKUP_API_KEY=your_actual_linkup_api_key
```

3. Deploy Backend

```bash
cdk deploy --profile AWS_PROFILE
```

### Frontend

4. Configure Frontend Environment Variables

Create a `.env` file in the `frontend/` folder and set the values from the CDK stack outputs:

```bash
NEXT_PUBLIC_COGNITO_USER_POOL_ID=
NEXT_PUBLIC_COGNITO_CLIENT_ID=
NEXT_PUBLIC_ALB_DNS_NAME=
```

5. The frontend is deployed via Vercel (AWS Amplify does not support streaming responses)

### Local Testing

To test the Strands Agent locally

1. Configure the Environment Variables

Create a `.env` file in the `backend/local/` folder:

```bash
# AWS Configuration
AWS_REGION=your_aws_region
AWS_PROFILE=your_aws_profile_name

# Bedrock Knowledge Base Configuration (this needs to be manually created in the AWS Console outside of CDK since it's not supported yet)
KNOWLEDGE_BASE_ID=your_knowledge_base_id

# LinkUp API Configuration
LINKUP_API_KEY=your_actual_linkup_api_key
```

2. Run the script

```bash
./run_agent.sh
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

| Service               | Rate (us-west-2)           | Quantity | Estimated cost    |
| --------------------- | -------------------------- | -------- | ----------------- |
| Elastic Load Balacing | $0.0225 per hour           | 720      | $16.20            |
| VPC public IPv4       | $0.005 per hour            | 720      | $3.60             |
| ECS Fargate (Memory)  | $0.00356 per hour          | 280      | $1.00 (estimated) |
| Route 53              | $0.50 per Hosted Zone      | 1        | $0.50             |
| ECS Fargate (vCPU)    | $0.03238 per hour          | 75       | $2.50 (estimated) |
| Bedrock (Nova Lite)   | $0.035 per 1M input tokens | 10       | $0.50 (estimated) |
| Bedrock (Nova Lite)   | $0.14 per 1M output tokens | 2        | $0.20 (estimated) |
| S3                    | $0.023 per GB              | 2        | $0.05 (estimated) |
| **TOTAL (estimated)** |                            |          | **$24.55**        |

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
