#FROM public.ecr.aws/docker/library/python:3.12-slim
FROM nikolaik/python-nodejs:python3.12-nodejs22-slim

# Set Python to run unbuffered for immediate log output
# This ensures print() and logging statements appear immediately in CloudWatch
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies including jq for JSON parsing
RUN apt-get update && apt-get install -y jq awscli && rm -rf /var/lib/apt/lists/*

# Verify Node.js and uv are available
RUN which node && which npm && which npx && which uv
RUN node -v && npm -v && uv --version

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make the MCP wrapper script executable
RUN chmod +x mcp-assume-role-wrapper.sh

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application with Uvicorn
# - port: 8000
# - disable buffering for streaming
# - force Python to run unbuffered for immediate log output
#CMD ["uvicorn", "fast_agent:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log", "--log-level", "info"]
CMD ["python", "-u", "-m", "uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log", "--log-level", "info"]
