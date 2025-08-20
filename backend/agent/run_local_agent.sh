#!/usr/bin/env bash

# Script to build and run the RAGBot Docker container locally

set -e  # Exit on any error

# Configuration
IMAGE_NAME="ragbot-agent"
CONTAINER_NAME="ragbot-agent-local"
PORT=8000

echo "🐋 Building Docker image: $IMAGE_NAME"
docker build -t $IMAGE_NAME .

echo "🧹 Stopping and removing existing container if it exists"
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

echo "🚀 Running Docker container: $CONTAINER_NAME"
echo "📍 Application will be available at: http://localhost:$PORT"

# Run the container with:
# - Interactive mode (-it) for logs
# - Remove on exit (--rm)
# - Port mapping
# - Named container for easy management
# - Environment file if it exists
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env file"
    docker run -it --rm \
        --name $CONTAINER_NAME \
        -p $PORT:$PORT \
        --env-file .env \
        -v //c/Users/eric.bach/.aws:/root/.aws \
        $IMAGE_NAME
else
    echo "⚠️ No .env file found. Please create an .env file first."
fi
