from pydantic import BaseModel

class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    query: str