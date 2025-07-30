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

- [] BUG: The tabs keep switching when RAGBot is thinking
- [] Add ability to upload document

- [] Add ability to clear chat
- [] Clean up stack resource names

- [] Build architecture diagram

- [] Investigate adding Cognito auth to ALB

- [] Move from ECS Fargate to Lambda Function URLs with auth in Lambda code
- [] Switch frontend to connect to Lambda fURL to compare how streaming works with fURL

##### Running FAST API Docker container locally

RUN LOCALLY w/FRONTEND (STREAMING SUPPORTED)

```
   cd src

   docker build -t fast-agent .

   docker run --rm --interactive --env AWS_PROFILE=bach-dev --env AWS_REGION=us-east-1 -v //c/Users/eric/.aws:/root/.aws -p 8000:8000 fast-agent

   Run frontend

   npm run dev
```

TESTS

```
   curl -X GET http://localhost:8000/health
   curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{"query": "What is the recommended tire pressure of a 07 Camry?"}'
   curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{"query": "What is AWS Lambda?"}'
   curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{"query": "What is the weather like today in Seattle?"}'
```

##### Deploying to AWS

DEPLOY

```
   cd backend

   python -m venv .venv

   pip install -r requirements.txt

   cdk deploy --profile bach-dev
```

TESTS

```
   curl -X GET https://ragbot2-alb.ericbach.dev/health
   curl -X GET https://ragbot2-alb.ericbach.dev/tools
   curl -X POST https://ragbot2-alb.ericbach.dev/chat -H 'Content-Type: application/json' -d '{"query": "What is fuel capacity of a 2007 Camry?"}'
   curl -X POST https://ragbot2-alb.ericbach.dev/chat -H 'Content-Type: application/json' -d '{"query": "How many GSIs can I have in a DynamoDB table?"}'
   curl -X POST https://ragbot2-alb.ericbach.dev/chat -H 'Content-Type: application/json' -d '{"query": "What is the weather like today in Edmonton?"}'
```

##### Questions

```
   What is the recommended PSI for the tires?
   What is the recommended tire pressure for the 2007 Camry?
   What is fuel capacity of the 2007 Camry?

   How is the weather in Seattle today?

   How many GSIs can I have on a DynamoDB table?
```
