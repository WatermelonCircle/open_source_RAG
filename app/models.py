from typing import List, Optional
from pydantic import BaseModel

class DocumentMetadata(BaseModel):
    """Metadata for uploaded documents"""
    filename: str
    page_count: int
    upload_timestamp: str
    file_size: int

class TextChunk(BaseModel):
    """Text chunk with source information"""
    text: str
    filename: str
    page_number: int
    chunk_index: int
    metadata: dict = {}

class ChatMessage(BaseModel):
    """Chat message model"""
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    """Chat response with sources"""
    response: str
    sources: List[dict]
    timestamp: str
    session_id: Optional[str] = None
    requires_email: bool = False

class SessionRequest(BaseModel):
    """Request to create a new session"""
    user_id: Optional[str] = "default"

class SessionResponse(BaseModel):
    """Response with new session information"""
    session_id: str
    created_at: str