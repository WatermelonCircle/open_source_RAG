"""
Conversation Memory Management for RAG Chat

This module handles:
1. Session-based conversation storage
2. Chat history management 
3. Session expiration and cleanup
4. Context retrieval for conversational AI

Stores conversation history in memory with automatic cleanup.
"""

import time
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from threading import Lock

@dataclass
class ChatTurn:
    """Single turn in a conversation"""
    timestamp: str
    user_message: str
    assistant_response: str
    sources: List[dict] = None
    
    def to_context_string(self) -> str:
        """Convert to string for context inclusion"""
        return f"User: {self.user_message}\nAssistant: {self.assistant_response}"

@dataclass 
class ConversationSession:
    """Complete conversation session"""
    session_id: str
    created_at: str
    last_activity: str
    chat_history: List[ChatTurn]
    
    def add_turn(self, user_message: str, assistant_response: str, sources: List[dict] = None):
        """Add a new turn to the conversation"""
        turn = ChatTurn(
            timestamp=datetime.now().isoformat(),
            user_message=user_message,
            assistant_response=assistant_response,
            sources=sources or []
        )
        self.chat_history.append(turn)
        self.last_activity = datetime.now().isoformat()
    
    def get_recent_context(self, max_turns: int = 5) -> str:
        """Get recent conversation context for AI prompt"""
        if not self.chat_history:
            return ""
        
        recent_turns = self.chat_history[-max_turns:]
        context_parts = [turn.to_context_string() for turn in recent_turns]
        return "\n\n".join(context_parts)
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired"""
        last_activity_time = datetime.fromisoformat(self.last_activity)
        expiry_time = last_activity_time + timedelta(minutes=timeout_minutes)
        return datetime.now() > expiry_time

class ConversationMemory:
    """In-memory conversation storage with session management"""
    
    def __init__(self, session_timeout_minutes: int = 30):
        self.sessions: Dict[str, ConversationSession] = {}
        self.session_timeout = session_timeout_minutes
        self._lock = Lock()  # Thread safety for concurrent requests
    
    def create_session(self) -> str:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        
        with self._lock:
            session = ConversationSession(
                session_id=session_id,
                created_at=datetime.now().isoformat(),
                last_activity=datetime.now().isoformat(),
                chat_history=[]
            )
            self.sessions[session_id] = session
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get existing session or None if not found/expired"""
        with self._lock:
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            
            # Check if session is expired
            if session.is_expired(self.session_timeout):
                del self.sessions[session_id]
                return None
            
            return session
    
    def add_conversation_turn(
        self, 
        session_id: str, 
        user_message: str, 
        assistant_response: str, 
        sources: List[dict] = None
    ) -> bool:
        """Add a turn to existing session"""
        session = self.get_session(session_id)
        
        if not session:
            return False
        
        with self._lock:
            session.add_turn(user_message, assistant_response, sources)
        
        return True
    
    def get_conversation_context(self, session_id: str, max_turns: int = 5) -> str:
        """Get recent conversation context for AI prompt"""
        session = self.get_session(session_id)
        
        if not session:
            return ""
        
        return session.get_recent_context(max_turns)
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions from memory"""
        current_time = datetime.now()
        expired_sessions = []
        
        with self._lock:
            for session_id, session in self.sessions.items():
                if session.is_expired(self.session_timeout):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
        
        return len(expired_sessions)
    
    def get_stats(self) -> Dict[str, int]:
        """Get memory usage statistics"""
        with self._lock:
            total_sessions = len(self.sessions)
            total_turns = sum(len(session.chat_history) for session in self.sessions.values())
            
            return {
                "total_sessions": total_sessions,
                "total_conversation_turns": total_turns,
                "memory_usage_bytes": self._estimate_memory_usage()
            }
    
    def _estimate_memory_usage(self) -> int:
        """Rough estimate of memory usage in bytes"""
        total_chars = 0
        
        for session in self.sessions.values():
            for turn in session.chat_history:
                total_chars += len(turn.user_message) + len(turn.assistant_response)
        
        # Rough estimate: 2 bytes per character + overhead
        return total_chars * 2 + len(self.sessions) * 1000

# Global conversation memory instance
conversation_memory = ConversationMemory(session_timeout_minutes=30)