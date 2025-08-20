#!/usr/bin/env bash

# Script to deploy the RAGBot 2 backend infrastructure
# Usage: 
#   ./deploy.sh [env_name]
#   ENV_NAME=staging ./deploy.sh

set -e  # Exit on any error

# Set environment name from parameter or environment variable, default to 'dev'
ENV_NAME=${1:-${ENV_NAME:-dev}}

echo "🚀 Deploying backend for environment: $ENV_NAME"

echo "Executing .venv/Scripts/activate.bat"
.venv/Scripts/activate.bat

echo "🚀 Deploying backend"
ENV_NAME=$ENV_NAME cdk deploy --all --profile observability2
