"""
File upload and management routes for the RAGBot agent.
"""
import json
import logging
from fastapi import APIRouter, HTTPException, Query
from config import get_s3_client, KNOWLEDGE_SOURCE_BUCKET_NAME

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/presigned-url")
def generate_presigned_url(
    user_id: str = Query(..., description="User ID"), 
    file_name: str = Query(..., description="Name of the file to upload")
):
    """Generate a presigned URL for S3 file upload."""
    try:
        logger.info(f"▶️ Generating presigned URL: {json.dumps({'userId': user_id, 'file': file_name})}")

        s3 = get_s3_client()

        file_name_full = file_name
        if not file_name_full.endswith('.pdf'):
            file_name_full = f"{file_name}.pdf"
        
        file_name_clean = file_name_full.split(".pdf")[0]

        # Always use the original filename - will overwrite if exists
        key = f"{user_id}/{file_name_clean}.pdf"

        logger.info({
            "user_id": user_id,
            "file_name_full": file_name_full,
            "file_name_clean": file_name_clean,
            "key": key,
        })

        presigned_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": KNOWLEDGE_SOURCE_BUCKET_NAME,
                "Key": key,
                "ContentType": "application/pdf",
            },
            ExpiresIn=300,
            HttpMethod="PUT",
        )

        logger.info(f"✅ Generated presigned URL: {json.dumps({'presignedUrl': presigned_url, 'key': key, 'bucket': KNOWLEDGE_SOURCE_BUCKET_NAME})}")

        return {
            "presignedurl": presigned_url,
            "key": key,
            "bucket": KNOWLEDGE_SOURCE_BUCKET_NAME
        }
        
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating presigned URL: {str(e)}")
