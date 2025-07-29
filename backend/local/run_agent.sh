#!/usr/bin/env bash

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python -m venv .venv
fi

# Activate the virtual environment (Windows Git Bash)
source .venv/Scripts/activate

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the agent
python agent.py