"""
Session service module containing business logic for session management.
"""
import json
import logging
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from models.session import SessionSummary, CreateSessionResponse, GetSessionResponse
from config import get_s3_client, DATA_BUCKET_NAME

logger = logging.getLogger(__name__)

class SessionService:
    """Service class for managing user sessions."""
    
    def __init__(self):
        self.s3 = get_s3_client()
        self.bucket = DATA_BUCKET_NAME

    def _get_session_prefix(self, user_id: str, session_id: Optional[str] = None) -> str:
        """Get S3 prefix for session storage."""
        if session_id:
            return f"sessions/{user_id}/session_{session_id}/"
        return f"sessions/{user_id}/"

    def _get_metadata_key(self, user_id: str, session_id: str) -> str:
        """Get S3 key for session metadata."""
        return f"{self._get_session_prefix(user_id, session_id)}metadata.json"

    def _get_conversation_key(self, user_id: str, session_id: str) -> str:
        """Get S3 key for conversation history."""
        return f"{self._get_session_prefix(user_id, session_id)}conversation.json"

    async def create_session(self, user_id: str, title: str = "New Chat") -> CreateSessionResponse:
        """Create a new session and return session details."""
        session_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        
        # Create session metadata
        metadata = {
            "session_id": session_id,
            "user_id": user_id,
            "title": title,
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
            "message_count": 0
        }
        
        try:
            # Store metadata in S3
            metadata_key = self._get_metadata_key(user_id, session_id)
            self.s3.put_object(
                Bucket=self.bucket,
                Key=metadata_key,
                Body=json.dumps(metadata),
                ContentType='application/json'
            )
            
            # Initialize empty conversation history
            conversation_key = self._get_conversation_key(user_id, session_id)
            self.s3.put_object(
                Bucket=self.bucket,
                Key=conversation_key,
                Body=json.dumps([]),
                ContentType='application/json'
            )
            
            logger.info(f"✅ Created new session {session_id} for user {user_id}")
            
            return CreateSessionResponse(
                session_id=session_id,
                user_id=user_id,
                title=title,
                created_at=created_at
            )
            
        except Exception as e:
            logger.error(f"🛑 Error creating session for user {user_id}: {str(e)}")
            raise Exception(f"Failed to create session: {str(e)}")

    async def list_user_sessions(self, user_id: str) -> List[SessionSummary]:
        """List all sessions for a user with metadata."""
        try:
            prefix = self._get_session_prefix(user_id)
            
            # List all session folders
            response = self.s3.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                Delimiter='/'
            )
            
            sessions = []
            
            # Process each session folder
            if 'CommonPrefixes' in response:
                for folder in response['CommonPrefixes']:
                    folder_prefix = folder['Prefix']
                    # Extract session_id from folder name (sessions/user_id/session_uuid/)
                    session_folder = folder_prefix.rstrip('/').split('/')[-1]
                    if session_folder.startswith('session_'):
                        session_id = session_folder.replace('session_', '')
                        
                        try:
                            # Try to load metadata
                            metadata_key = self._get_metadata_key(user_id, session_id)
                            metadata_obj = self.s3.get_object(Bucket=self.bucket, Key=metadata_key)
                            metadata = json.loads(metadata_obj['Body'].read())
                            
                            sessions.append(SessionSummary(
                                session_id=session_id,
                                user_id=user_id,
                                title=metadata.get('title', 'Untitled Chat'),
                                created_at=datetime.fromisoformat(metadata['created_at']),
                                updated_at=datetime.fromisoformat(metadata['updated_at']),
                                message_count=metadata.get('message_count', 0)
                            ))
                            
                        except ClientError as e:
                            if e.response['Error']['Code'] == 'NoSuchKey':
                                # Metadata doesn't exist, create it from existing session data
                                logger.warning(f"No metadata found for session {session_id}, attempting to create from existing data")
                                await self._create_metadata_from_existing_session(user_id, session_id)
                                # Try again to load metadata
                                try:
                                    reload_metadata_key = self._get_metadata_key(user_id, session_id)
                                    metadata_obj = self.s3.get_object(Bucket=self.bucket, Key=reload_metadata_key)
                                    metadata = json.loads(metadata_obj['Body'].read())
                                    sessions.append(SessionSummary(
                                        session_id=session_id,
                                        user_id=user_id,
                                        title=metadata.get('title', 'Untitled Chat'),
                                        created_at=datetime.fromisoformat(metadata['created_at']),
                                        updated_at=datetime.fromisoformat(metadata['updated_at']),
                                        message_count=metadata.get('message_count', 0)
                                    ))
                                except Exception:
                                    logger.error(f"Failed to create metadata for session {session_id}")
                                    continue
                            else:
                                logger.error(f"Error loading metadata for session {session_id}: {str(e)}")
                                continue            # Sort sessions by updated_at (most recent first)
            sessions.sort(key=lambda x: x.updated_at, reverse=True)
            
            logger.info(f"✅ Listed {len(sessions)} sessions for user {user_id}")
            return sessions
            
        except Exception as e:
            logger.error(f"🛑 Error listing sessions for user {user_id}: {str(e)}")
            raise Exception(f"Failed to list sessions: {str(e)}")

    async def get_session_with_history(self, user_id: str, session_id: str) -> GetSessionResponse:
        """Get session details with full chat history."""
        try:
            session_prefix = self._get_session_prefix(user_id, session_id)
            logger.info(f"🔍 Looking for session at prefix: {session_prefix}")
            
            # Load metadata
            metadata_key = self._get_metadata_key(user_id, session_id)
            metadata = None
            
            try:
                metadata_obj = self.s3.get_object(Bucket=self.bucket, Key=metadata_key)
                metadata = json.loads(metadata_obj['Body'].read())
                logger.info(f"✅ Found metadata for session {session_id}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    logger.info(f"📝 No metadata found, will create from existing session data")
                    # Try to create metadata from existing session
                    await self._create_metadata_from_existing_session(user_id, session_id)
                    metadata_obj = self.s3.get_object(Bucket=self.bucket, Key=metadata_key)
                    metadata = json.loads(metadata_obj['Body'].read())
                else:
                    raise
            
            # Load conversation history from individual message files
            messages = []
            try:
                # Look for messages in agents/agent_ragbot2/messages/ directory
                messages_prefix = f"{session_prefix}agents/agent_ragbot2/messages/"
                logger.info(f"🔍 Looking for messages at prefix: {messages_prefix}")
                
                response = self.s3.list_objects_v2(
                    Bucket=self.bucket,
                    Prefix=messages_prefix
                )
                
                if 'Contents' in response:
                    logger.info(f"📨 Found {len(response['Contents'])} message files")
                    
                    # Sort message files by name to maintain order
                    message_files = sorted(response['Contents'], key=lambda x: x['Key'])
                    
                    # Parse and filter messages
                    raw_messages = []
                    for obj in message_files:
                        if obj['Key'].endswith('.json'):
                            try:
                                message_obj = self.s3.get_object(Bucket=self.bucket, Key=obj['Key'])
                                message_data = json.loads(message_obj['Body'].read())
                                raw_messages.append((obj['Key'], message_data))
                            except Exception as e:
                                logger.warning(f"⚠️ Failed to load message from {obj['Key']}: {str(e)}")
                                continue
                    
                    # Process messages using role changes to separate conversations
                    conversation_messages = []
                    current_message_parts = []
                    current_role = None
                    current_timestamp = None
                    current_message_id = None
                    
                    for file_key, message_data in raw_messages:
                        if 'message' in message_data:
                            message_content = message_data['message']
                            role = message_content.get('role', 'user')
                            content_parts = message_content.get('content', [])
                            message_id = message_content.get('message_id', message_data.get('message_id'))
                            timestamp = message_data.get('created_at', message_data.get('updated_at', ''))
                            
                            # Skip toolResult-only messages
                            if isinstance(content_parts, list):
                                if len(content_parts) == 1 and 'toolResult' in content_parts[0]:
                                    logger.debug(f"⏭️ Skipping toolResult-only message from {file_key}")
                                    continue
                            
                            # If role changed or message_id changed, flush previous message
                            if (current_role is not None and 
                                (role != current_role or 
                                 (message_id and current_message_id and message_id != current_message_id))):
                                
                                # Flush accumulated content
                                if current_message_parts:
                                    final_content = '\n\n'.join(current_message_parts).strip()
                                    if final_content:
                                        conversation_messages.append({
                                            'role': current_role,
                                            'content': final_content,
                                            'timestamp': current_timestamp
                                        })
                                        logger.debug(f"📄 Flushed {current_role} message with {len(current_message_parts)} parts")
                                
                                # Reset for new message
                                current_message_parts = []
                                current_timestamp = None  # Reset timestamp for new message
                            
                            # Update current context
                            current_role = role
                            current_message_id = message_id
                            # Set timestamp for this message (use first timestamp encountered for this message)
                            if current_timestamp is None:
                                current_timestamp = timestamp
                            
                            # Extract text content from this file
                            text_parts = []
                            if isinstance(content_parts, list):
                                for part in content_parts:
                                    if 'text' in part:
                                        text_content = part['text'].strip()
                                        if text_content:
                                            text_parts.append(text_content)
                                    elif 'toolUse' in part:
                                        tool_name = part['toolUse'].get('name', 'unknown')
                                        logger.debug(f"🔧 {role} message includes tool use: {tool_name}")
                            
                            # Add text parts to current message
                            if text_parts:
                                current_message_parts.extend(text_parts)
                                logger.debug(f"📄 Added {len(text_parts)} parts to {role} message from {file_key}")
                        
                        else:
                            # Fallback for messages that don't have the nested structure
                            conversation_messages.append(message_data)
                            logger.debug(f"📄 Loaded legacy message from {file_key}")
                    
                    # Flush any remaining content
                    if current_message_parts and current_role:
                        final_content = '\n\n'.join(current_message_parts).strip()
                        if final_content:
                            conversation_messages.append({
                                'role': current_role,
                                'content': final_content,
                                'timestamp': current_timestamp
                            })
                            logger.debug(f"📄 Final {current_role} message with {len(current_message_parts)} parts")
                    
                    messages = conversation_messages
                else:
                    logger.info(f"📭 No message files found in {messages_prefix}")
                    
                # Also check for legacy conversation.json format as fallback
                if not messages:
                    conversation_key = self._get_conversation_key(user_id, session_id)
                    try:
                        conversation_obj = self.s3.get_object(Bucket=self.bucket, Key=conversation_key)
                        messages = json.loads(conversation_obj['Body'].read())
                        logger.info(f"📜 Loaded {len(messages)} messages from legacy conversation.json")
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'NoSuchKey':
                            logger.info(f"📭 No legacy conversation.json found either")
                        else:
                            raise
                            
            except Exception as e:
                logger.error(f"🛑 Error loading messages: {str(e)}")
                messages = []
            
            # Sort messages by timestamp to ensure chronological order
            if messages:
                messages.sort(key=lambda msg: msg.get('timestamp', ''))
                logger.info(f"📅 Sorted {len(messages)} messages by timestamp")
            
            logger.info(f"✅ Retrieved session {session_id} for user {user_id} with {len(messages)} messages")
            
            return GetSessionResponse(
                session_id=session_id,
                user_id=user_id,
                title=metadata.get('title', 'Untitled Chat'),
                created_at=datetime.fromisoformat(metadata['created_at']),
                updated_at=datetime.fromisoformat(metadata['updated_at']),
                conversation=messages
            )
            
        except Exception as e:
            logger.error(f"🛑 Error getting session {session_id} for user {user_id}: {str(e)}")
            raise Exception(f"Failed to get session: {str(e)}")

    async def update_session_title(self, user_id: str, session_id: str, title: str):
        """Update session title."""
        try:
            metadata_key = self._get_metadata_key(user_id, session_id)
            
            # Load existing metadata
            try:
                metadata_obj = self.s3.get_object(Bucket=self.bucket, Key=metadata_key)
                metadata = json.loads(metadata_obj['Body'].read())
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    # Create metadata if it doesn't exist
                    await self._create_metadata_from_existing_session(user_id, session_id)
                    metadata_obj = self.s3.get_object(Bucket=self.bucket, Key=metadata_key)
                    metadata = json.loads(metadata_obj['Body'].read())
                else:
                    raise
            
            # Update title and timestamp
            metadata['title'] = title
            metadata['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Save updated metadata
            self.s3.put_object(
                Bucket=self.bucket,
                Key=metadata_key,
                Body=json.dumps(metadata),
                ContentType='application/json'
            )
            
            logger.info(f"✅ Updated title for session {session_id} to '{title}'")
            return {"message": f"Session title updated to '{title}'"}
            
        except Exception as e:
            logger.error(f"🛑 Error updating title for session {session_id}: {str(e)}")
            raise Exception(f"Failed to update session title: {str(e)}")

    async def update_session_metadata(self, user_id: str, session_id: str, message_count_delta: int = 1):
        """Update session metadata after new messages."""
        try:
            metadata_key = self._get_metadata_key(user_id, session_id)
            
            try:
                # Load existing metadata
                metadata_obj = self.s3.get_object(Bucket=self.bucket, Key=metadata_key)
                metadata = json.loads(metadata_obj['Body'].read())
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    # Create metadata if it doesn't exist
                    await self._create_metadata_from_existing_session(user_id, session_id)
                    metadata_obj = self.s3.get_object(Bucket=self.bucket, Key=metadata_key)
                    metadata = json.loads(metadata_obj['Body'].read())
                else:
                    raise
            
            # Update metadata
            metadata['message_count'] = metadata.get('message_count', 0) + message_count_delta
            metadata['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Save updated metadata
            self.s3.put_object(
                Bucket=self.bucket,
                Key=metadata_key,
                Body=json.dumps(metadata),
                ContentType='application/json'
            )
            
            logger.debug(f"Updated metadata for session {session_id}")
            
        except Exception as e:
            logger.error(f"🛑 Error updating metadata for session {session_id}: {str(e)}")
            # Don't raise exception for metadata updates as it's not critical

    async def _create_metadata_from_existing_session(self, user_id: str, session_id: str):
        """Create metadata for an existing session that doesn't have metadata yet."""
        try:
            session_prefix = self._get_session_prefix(user_id, session_id)
            logger.info(f"🔧 Creating metadata for existing session at prefix: {session_prefix}")
            
            # Find the earliest object in the session (approximation of creation time)
            response = self.s3.list_objects_v2(
                Bucket=self.bucket,
                Prefix=session_prefix,
                MaxKeys=1
            )
            
            created_at = datetime.now(timezone.utc)
            if 'Contents' in response and response['Contents']:
                # Use the first object's last modified time as creation time
                created_at = response['Contents'][0]['LastModified'].replace(tzinfo=timezone.utc)
                logger.info(f"📅 Using creation time from first object: {created_at}")
            
            # Initialize title - will be updated if we find a better one
            title = "Untitled Chat"
            
            # Try to count messages from the messages directory
            message_count = 0
            try:
                # Count message files in agents/agent_ragbot2/messages/
                messages_prefix = f"{session_prefix}agents/agent_ragbot2/messages/"
                messages_response = self.s3.list_objects_v2(
                    Bucket=self.bucket,
                    Prefix=messages_prefix
                )
                
                if 'Contents' in messages_response:
                    json_files = [obj for obj in messages_response['Contents'] if obj['Key'].endswith('.json')]
                    total_files = len(json_files)
                    logger.info(f"📊 Found {total_files} message files")
                    
                    # Count conversation messages (user messages + assistant conversation groups)
                    user_message_count = 0
                    assistant_conversation_count = 0
                    in_assistant_sequence = False
                    
                    for obj in json_files:
                        try:
                            message_obj = self.s3.get_object(Bucket=self.bucket, Key=obj['Key'])
                            message_data = json.loads(message_obj['Body'].read())
                            
                            if 'message' in message_data:
                                message_content = message_data['message']
                                role = message_content.get('role', 'user')
                                content_parts = message_content.get('content', [])
                                
                                # Skip toolResult-only messages
                                if isinstance(content_parts, list):
                                    if len(content_parts) == 1 and 'toolResult' in content_parts[0]:
                                        continue
                                
                                # Check if message has text content
                                has_text = False
                                if isinstance(content_parts, list):
                                    for part in content_parts:
                                        if 'text' in part and part['text'].strip():
                                            has_text = True
                                            break
                                
                                if has_text:
                                    if role == 'user':
                                        user_message_count += 1
                                        if in_assistant_sequence:
                                            # End of assistant sequence
                                            assistant_conversation_count += 1
                                            in_assistant_sequence = False
                                    elif role == 'assistant':
                                        if not in_assistant_sequence:
                                            # Start of new assistant sequence
                                            in_assistant_sequence = True
                                    
                        except Exception as e:
                            logger.debug(f"Failed to parse message file {obj['Key']}: {str(e)}")
                            continue
                    
                    # Handle case where messages end with assistant sequence
                    if in_assistant_sequence:
                        assistant_conversation_count += 1
                    
                    message_count = user_message_count + assistant_conversation_count
                    logger.info(f"📊 Counted {message_count} conversation messages ({user_message_count} user + {assistant_conversation_count} assistant) out of {total_files} total files")
                    
                    # Try to extract title from the first user message if available
                    if message_count > 0 and title == "Untitled Chat":
                        try:
                            first_message_key = json_files[0]['Key']
                            first_message_obj = self.s3.get_object(Bucket=self.bucket, Key=first_message_key)
                            first_message_data = json.loads(first_message_obj['Body'].read())
                            
                            if 'message' in first_message_data:
                                message_content = first_message_data['message']
                                if message_content.get('role') == 'user':
                                    content_parts = message_content.get('content', [])
                                    if isinstance(content_parts, list) and len(content_parts) > 0:
                                        first_text = content_parts[0].get('text', '')
                                        if first_text:
                                            # Use first 50 characters as title
                                            title = first_text[:50].strip()
                                            if len(first_text) > 50:
                                                title += "..."
                                            logger.info(f"🏷️ Generated title from first message: {title}")
                        except Exception as e:
                            logger.debug(f"Failed to extract title from first message: {str(e)}")
                            pass
                
                # Also check legacy conversation.json as fallback
                if message_count == 0:
                    try:
                        conversation_key = self._get_conversation_key(user_id, session_id)
                        conversation_obj = self.s3.get_object(Bucket=self.bucket, Key=conversation_key)
                        messages = json.loads(conversation_obj['Body'].read())
                        message_count = len(messages)
                        logger.info(f"📊 Found {message_count} messages in legacy conversation.json")
                    except Exception:
                        pass
                        
            except Exception as e:
                logger.warning(f"⚠️ Failed to count messages: {str(e)}")
                pass
            
            # Try to extract title from session.json if it exists (overrides title from first message)
            try:
                session_json_key = f"{session_prefix}session.json"
                session_obj = self.s3.get_object(Bucket=self.bucket, Key=session_json_key)
                session_data = json.loads(session_obj['Body'].read())
                if 'title' in session_data:
                    title = session_data['title']
                    logger.info(f"📝 Found title in session.json: {title}")
            except Exception as e:
                logger.debug(f"No session.json found or no title: {str(e)}")
            
            # Create metadata
            metadata = {
                "session_id": session_id,
                "user_id": user_id,
                "title": title,
                "created_at": created_at.isoformat(),
                "updated_at": created_at.isoformat(),
                "message_count": message_count
            }
            
            metadata_key = self._get_metadata_key(user_id, session_id)
            self.s3.put_object(
                Bucket=self.bucket,
                Key=metadata_key,
                Body=json.dumps(metadata),
                ContentType='application/json'
            )
            
            logger.info(f"✅ Created metadata for existing session {session_id} with {message_count} messages")
            
        except Exception as e:
            logger.error(f"🛑 Failed to create metadata for existing session {session_id}: {str(e)}")
            raise

    async def delete_session(self, user_id: str, session_id: str):
        """Delete a session and all associated data."""
        try:
            prefix = self._get_session_prefix(user_id, session_id)
            
            # List all objects in the session
            response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            
            if 'Contents' in response:
                objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                
                # Delete all objects
                self.s3.delete_objects(
                    Bucket=self.bucket,
                    Delete={'Objects': objects_to_delete}
                )
                
                logger.info(f"✅ Deleted session {session_id} with {len(objects_to_delete)} objects")
                return {"message": f"Deleted session {session_id} with {len(objects_to_delete)} objects"}
            else:
                logger.info(f"No objects found for session {session_id}")
                return {"message": f"No objects found for session {session_id}"}
                
        except Exception as e:
            logger.error(f"🛑 Error deleting session {session_id} for user {user_id}: {str(e)}")
            raise Exception(f"Failed to delete session: {str(e)}")

    async def auto_generate_session_title(self, user_id: str, session_id: str, query: str):
        """Auto-generate a title for a session based on the first user message."""
        try:
            # Check if this session already has a custom title
            session_response = await self.get_session_with_history(user_id, session_id)
            
            # Only auto-generate if title is still "New Chat" and message count is low
            if session_response.title == "New Chat" and len(session_response.conversation) <= 2:
                # Generate a title from the first few words of the query
                words = query.strip().split()
                if len(words) > 6:
                    title = " ".join(words[:6]) + "..."
                else:
                    title = " ".join(words)
                
                # Limit title length and clean it up
                title = title[:50].strip()
                if not title:
                    title = "New Chat"
                
                await self.update_session_title(user_id, session_id, title)
                logger.info(f"Auto-generated title for session {session_id}: '{title}'")
                
        except Exception as e:
            logger.warning(f"Failed to auto-generate title for session {session_id}: {str(e)}")