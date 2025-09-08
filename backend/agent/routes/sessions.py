"""
Session management routes for the RAGBot agent.
"""
import json
import logging
from fastapi import APIRouter
from config import get_s3_client, DATA_BUCKET_NAME

logger = logging.getLogger(__name__)

router = APIRouter()

@router.delete('/session/{user_id}/{session_id}')
async def delete_session(user_id: str, session_id: str):
    """Delete a user session and all associated data."""
    logger.info(f"▶️ Clearing user session: {json.dumps({'userId': user_id, 'sessionId': session_id})}")

    s3 = get_s3_client()
    prefix = f"sessions/{user_id}/session_{session_id}/"
    
    try:
        # List all objects under just the target session folder
        response = s3.list_objects_v2(Bucket=DATA_BUCKET_NAME, Prefix=prefix)
        if 'Contents' in response:
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            s3.delete_objects(
                Bucket=DATA_BUCKET_NAME,
                Delete={'Objects': objects_to_delete}
            )

            logger.info(f"✅ Deleted {len(objects_to_delete)} objects in session {session_id}")
            return {"message": f"Deleted {len(objects_to_delete)} objects in session {session_id}"}
        else:
            return {"message": f"No objects found for session {session_id}"}
    except Exception as e:
        logger.error(f"🛑 Error deleting session {session_id} for user {user_id}: {str(e)}")
        return {"error": str(e)}
