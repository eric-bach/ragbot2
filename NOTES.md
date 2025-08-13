##### Tasks

- [x] Deploy Strands Agent in AWS (ECS Fargate)
- [x] Deploy aws-documentation-mcp-server in AWS
- [x] Add aws-documentation-mcp-server back to fast_agent.py and test it works in AWS
- [x] Add ALB to AWS ECS Fargate container
- [x] Create Cognito User Pool
- [-] Create Bedrock Knowledge Base with S3 Vectors - NOT SUPPORTED YET
- [x] Add Cognito authentication to ALB - REQUIRES CERTIFICATE
- [x] Build frontend to connect to R53/ALB/ECS to test how streaming works with ECS
- [x] Deploy frontend to Vercel (Amplify doesn't support streaming)
- [x] Improve format of responses from AI agent
- [x] Include references to KB, web links, MCP server for sourced information in responses
- [x] Format markdown responses in UI
- [x] Display tools available in UI
- [x] BUG: Handle when response includes more than once occurrence of a tag
- [x] Add copy text button and thumbs up/down buttons
- [x] Add ability to upload document
- [x] Move user profile to icon
- [x] Include conversational history in a chat session
- [x] Add ability to clear chat session
- [x] Update README and add architecture diagram
- [x] BUG: Upload user documents under the user's id key in the S3 bucket
- [x] Build estimate cost list
- [x] BUG: The first request fails unless you wait a few seconds after loading the page
- [x] Improve the feel of the responsiveness of responses after the message is submitted

- [] Revert back to prior to user configurable MCP servers
- [] Use this prompt
  You are an AI assistant that helps users answer any type of questions with access to multiple tools: - Web search using LinkUp API (web_search) - AWS documentation (MCP tools) - Retrieval-Augmented Generation (RAG) knowledge base (retrieve)

      **Instructions:**
      - For EVERY user query, you MUST use at least one tool.
            - The AWS Documentation MCP server is used for queries about AWS services.
            - The retrieve tool is used for knowledge base queries about cars.
            - The web_search tool is ideal for real-time information (e.g. weather, stock prices, news, anything
            that can change minute-to-minute).
      - If you are not sure which tool to use, use the retrieve tool first, then MCP tools, before the web_search tool.
      - NEVER answer based solely on your own knowledge, even if you think you know the answer.
      - Only answer after reviewing results from all relevant tools.

      **Response:**
      - Your response must ALWAYS use the three required tags ONLY, and in Markdown format:
            - <thinking>: Explain your approach, reasoning, and tool choices.
            - <response>: Provide a clear, human-readable answer.
            - <sources>: List ALL tool outputs and/or sources used.
      - Do NOT output anything except these three tags.
      - Respond in a friendly, Albertan tone.

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

- [] Improve the response message bubbles to be more like Perplexity responses.

- [] Clean up stack resource names
- [] Add checks to check env variables exist
- [] Investigate Strands Observability

- [] Investigate adding Cognito auth to ALB
- [] Add polling on UI to check when Bedrock KB sync is completed
- [] Move from ECS Fargate to Lambda Function URLs with auth in Lambda code
- [] Switch frontend to connect to Lambda fURL to compare how streaming works with fUR

##### Features

- Tool capabiities
  - RAG w/ability for users to upload documents
  - Built in Web search tool
  - Additional MCP servers support
- Streaming responses from LLM
  - Broken down into response, sources, thinking
- Conversational History retained for each session
  - Managed at the server-side, no additional tokens
  - MISSING: No ability for the user to select from a previous session yet
- MISSING: Authentication to backend

##### Running FAST API Docker container locally

RUN AWS BUILD LOCALLY (STREAMING SUPPORTED)

```
   Populate the .env file

   cd backend/aws
   docker build -t fast-agent .
   docker run --rm --interactive --env-file .env -v //c/Users/eric/.aws:/root/.aws -p 8000:8000 fast-agent
   docker run --rm --interactive --env-file .env -v //c/Users/eric.bach/.aws:/root/.aws -p 8000:8000 fast-agent

   cd frontend
   npm run dev
```

TESTS

```
   curl -X GET http://localhost:8000/health
   curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{"query": "What is the recommended tire pressure of a 07 Camry?", "session_id": "1", "user_id": "1"}'
   curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{"query": "What is AWS Lambda?", "session_id": "1", "user_id": "1"}'
   curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{"query": "What is the weather like today in Seattle?", "session_id": "1", "user_id": "1"}'
```

##### Deploying to AWS

DEPLOY

```
   cd infrastructure

   python -m venv .venv

   pip install -r requirements.txt

   cdk deploy --profile bach-prod
```

TESTS

```
   curl -X GET https://ragbot2-public.ericbach.dev/health
   curl -X GET https://ragbot2-public.ericbach.dev/tools
   curl -X POST https://ragbot2-public.ericbach.dev/chat -H 'Content-Type: application/json' -d '{"query": "What is fuel capacity of a 2007 Camry?", "session_id": "1", "user_id": "1"}'
   curl -X POST https://ragbot2-public.ericbach.dev/chat -H 'Content-Type: application/json' -d '{"query": "How many GSIs can I have in a DynamoDB table?", "session_id": "1", "user_id": "1"}'
   curl -X POST https://ragbot2-public.ericbach.dev/chat -H 'Content-Type: application/json' -d '{"query": "What is the weather like today in Edmonton?", "session_id": "1", "user_id": "1"}'
```

##### Cloudflare

Check what headers Cloudflare is returning

```
# Get the Cloudflare proxy IP addresses
nslookup ragbot2-public.ericbach.dev 8.8.8.8

# Check what headers Cloudflare is returning using one of the proxy IP addresses
curl -v https://ragbot2-public.ericbach.dev/health --resolve ragbot2-public.ericbach.dev:443:172.67.210.169 2>&1 | grep -E "(CF-|X-|>|<)"
```

##### Questions

```
   What is the recommended PSI for the tires?
   What is the recommended tire pressure for the 2007 Camry?
   What is fuel capacity of the 2007 Camry?

   How is the weather in Seattle today?

   What is AWS Lambda?
   How many GSIs can I have on a DynamoDB table?

   I like to drink green tea in the the afternoons, what are the health benefits?
   What do I like to drink in the afternoon?
```
