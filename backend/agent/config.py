"""
Configuration module for the RAGBot agent.
Contains environment variables, AWS clients, and global configurations.
"""
import os
import boto3
import logging
from botocore.config import Config
from dotenv import load_dotenv
from strands.models import BedrockModel
from strands_tools import retrieve, current_time
from tools.web_search import web_search
from services.mcp_config_store import MCPConfigStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Environment variables
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID')
KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID')
DATA_BUCKET_NAME = os.getenv('DATA_BUCKET_NAME', '')
KNOWLEDGE_SOURCE_BUCKET_NAME = os.getenv('KNOWLEDGE_SOURCE_BUCKET_NAME')
LINKUP_API_KEY = os.getenv('LINKUP_API_KEY', '')

# Base tools available to all agents
BASE_TOOLS = [web_search, current_time, retrieve]

# Validate required environment variables
def validate_environment():
    """Validate that all required environment variables are set."""
    if not BEDROCK_MODEL_ID:
        logger.error("BEDROCK_MODEL_ID environment variable is not set")
        raise Exception("BEDROCK_MODEL_ID environment variable is not set")
    
    if not DATA_BUCKET_NAME or DATA_BUCKET_NAME == '':
        logger.error("DATA_BUCKET_NAME environment variable is not set")
        raise Exception("DATA_BUCKET_NAME environment variable is not set")
    
    if not LINKUP_API_KEY or LINKUP_API_KEY == '':
        logger.error("LINKUP_API_KEY environment variable is not set")
        raise Exception("LINKUP_API_KEY environment variable is not set")

# Validate environment on import
validate_environment()

# AWS Session and Clients
def get_boto_session():
    """Get a boto3 session for the configured region."""
    return boto3.Session(region_name=AWS_REGION)

def get_s3_client():
    """Get an S3 client with proper configuration."""
    return boto3.client(
        "s3", 
        endpoint_url=f"https://s3.{AWS_REGION}.amazonaws.com", 
        config=Config(
            s3={"addressing_style": "virtual"}, 
            region_name=AWS_REGION,
            signature_version="s3v4"
        )
    )

def get_bedrock_model():
    """Get a configured Bedrock model."""
    if not BEDROCK_MODEL_ID:
        raise ValueError("BEDROCK_MODEL_ID is required but not set")
    
    session = get_boto_session()
    return BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        boto_session=session
    )

def get_mcp_config_store():
    """Get an MCP configuration store."""
    session = get_boto_session()
    return MCPConfigStore(
        bucket_name=DATA_BUCKET_NAME,
        region_name=AWS_REGION,
        boto_session=session
    )

# CORS settings
CORS_SETTINGS = {
    "allow_origins": ["*"],  # In production, specify exact origins
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
