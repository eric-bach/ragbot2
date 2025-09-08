import json
import boto3
import logging
from typing import List, Optional
from botocore.exceptions import ClientError
from models.mcp_config import UserMCPConfig, MCPServerConfig

logger = logging.getLogger(__name__)

class MCPConfigStore:
    """Handles storage and retrieval of user MCP configurations in S3"""

    def __init__(self, bucket_name: str, region_name: str, boto_session: boto3.Session):
        self.bucket_name = bucket_name
        self.s3_client = boto_session.client('s3', region_name=region_name)

    def _get_config_key(self, user_id: str) -> str:
        """Generate S3 key for user's MCP config"""
        return f"mcp_configs/{user_id}/config.json"

    async def save_user_config(self, user_id: str, config: UserMCPConfig) -> bool:
        """Save user's MCP configuration to S3"""
        try:
            key = self._get_config_key(user_id)
            config_json = config.model_dump_json(indent=2)

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=config_json,
                ContentType='application/json'
            )

            logger.info(f"Saved MCP config for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save MCP config for user {user_id}: {str(e)}")
            return False
        
    async def get_user_config(self, user_id: str) -> Optional[UserMCPConfig]:
        """Retrieve user's MCP configuration from S3"""
        try:
            logger.info(f"⚙️ Getting MCP config for: {user_id}")
            key = self._get_config_key(user_id)

            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )

            logger.debug(f"Reading MCP config: {key}")

            config_data = json.loads(response['Body'].read().decode('utf-8'))

            logger.info(f"🛠️ Found MCP config for: {user_id}")
            return UserMCPConfig(**config_data)

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.info(f"No MCP config found for user {user_id}")
                return None
            else:
                logger.error(f"Failed to get MCP config for user {user_id}: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"Failed to parse MCP config for user {user_id}: {str(e)}")
            return None

    async def delete_user_config(self, user_id: str) -> bool:
        """Delete user's MCP configuration from S3"""
        try:
            key = self._get_config_key(user_id)

            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )

            logger.info(f"Deleted MCP config for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete MCP config for user {user_id}: {str(e)}")
            return False