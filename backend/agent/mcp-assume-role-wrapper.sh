#!/bin/bash
# AWS MCP Server Cross-Account Role Wrapper
# This script assumes a cross-account role before starting the MCP server

set -e

# Check if AWS_ROLE_ARN is provided
if [ -n "$AWS_ROLE_ARN" ]; then
    echo "Assuming role: $AWS_ROLE_ARN"
    
    # Use current timestamp for unique session name
    SESSION_NAME="${AWS_ROLE_SESSION_NAME:-mcp-session-$(date +%s)}"
    
    # Assume the role and get temporary credentials
    CREDS=$(aws sts assume-role \
        --role-arn "$AWS_ROLE_ARN" \
        --role-session-name "$SESSION_NAME" \
        --output json)
    
    # Extract credentials
    export AWS_ACCESS_KEY_ID=$(echo $CREDS | jq -r '.Credentials.AccessKeyId')
    export AWS_SECRET_ACCESS_KEY=$(echo $CREDS | jq -r '.Credentials.SecretAccessKey')
    export AWS_SESSION_TOKEN=$(echo $CREDS | jq -r '.Credentials.SessionToken')
    
    # Unset the role ARN to prevent the MCP server from being confused
    unset AWS_ROLE_ARN
    unset AWS_ROLE_SESSION_NAME
    
    echo "Successfully assumed role. Starting MCP server..."
else
    echo "No AWS_ROLE_ARN provided. Using default credentials..."
fi

# Start the MCP server with the credentials
exec uvx awslabs.billing-cost-management-mcp-server "$@"