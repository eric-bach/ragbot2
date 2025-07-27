##### Tasks

- [x] Deploy Strands Agent in AWS (ECS Fargate)
- [] Deploy aws-documentation-mcp-server in AWS (ECS Fargate)
- [] Create API GW with Cognito User Pool to front Strands Agent, remove public Fargate IP
- [] Build frontend UI to connect to backend

##### Running FAST API Docker container locally

docker build -t fast-agent .

docker run --rm --interactive --env AWS_PROFILE=bach-dev --env AWS_REGION=us-east-1 -v //c/Users/eric/.aws:/root/.aws -p 8000:8000 fast-agent

curl -X GET http://localhost:8000
curl -X POST http://localhost/chat:8000 -H 'Content-Type: application/json' -d '{"query": "What is the recommended PSI for the tires?"}'

##### Deploying to AWS

cd backend
python -m venv .venv
pip install -r requirements.txt
cdk deploy --profile bach-dev

TESTS

curl -X GET http://<PUBLIC IP>:8000
curl -X POST http://<PUBLIC IP>:8000 -H 'Content-Type: application/json' -d '{"query": "What is the recommended PSI for the tires?"}'

##### Questions

```
   What is the recommended PSI for the tires?
   What is the recommended tire pressure for the 2007 Camry?
   What is fuel capacity of the 2007 Camry?

   How is the weather in Seattle today?

   How many GSIs can I have on a DynamoDB table?
```
