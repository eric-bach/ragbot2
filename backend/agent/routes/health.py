"""
Health check routes for the RAGBot agent.
"""
import logging
from fastapi import APIRouter
from config import (
    AWS_REGION, 
    KNOWLEDGE_BASE_ID, 
    DATA_BUCKET_NAME, 
    KNOWLEDGE_SOURCE_BUCKET_NAME, 
    LINKUP_API_KEY
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
def home():
    """Root endpoint returning application information."""
    return {"RAGBot": "v2"}

@router.get("/health")
def health():
    """Health check endpoint with configuration information."""
    logger.info(f"✅ Health Check OK")
    return {
        "STATUS": "healthy",
        "AWS_REGION": AWS_REGION,
        "KNOWLEDGE_BASE_ID": KNOWLEDGE_BASE_ID,
        "DATA_BUCKET_NAME": DATA_BUCKET_NAME,
        "KNOWLEDGE_SOURCE_BUCKET_NAME": KNOWLEDGE_SOURCE_BUCKET_NAME,
        "LINKUP_API_KEY": f"***{LINKUP_API_KEY[-3:]}",
    }
