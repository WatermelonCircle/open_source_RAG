"""
WebSocket Connection Manager for Live Chat

This module handles:
1. WebSocket connections between customers and agents
2. Real-time message routing
3. Connection state management
4. Chat session matching
"""

import json
import uuid
from typing import Dict, List, Optional, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)

class UserType(Enum):
    CUSTOMER = "customer"
    AGENT = "agent"

class MessageType(Enum):
    CHAT_MESSAGE = "chat_message"
    TYPING_INDICATOR = "typing_indicator"
    AGENT_JOINED = "agent_joined"
    AGENT_LEFT = "agent_left"
    CUSTOMER_JOINED = "customer_joined"
    CUSTOMER_LEFT = "customer_left"
    CHAT_ENDED = "chat_ended"
    ERROR = "error"
    SYSTEM = "system"

@dataclass
class ChatMessage:
    """Represents a chat message"""
    message_id: str
    chat_id: str
    sender_id: str
    sender_type: UserType
    content: str
    timestamp: str
    message_type: MessageType = MessageType.CHAT_MESSAGE
    
    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "chat_id": self.chat_id,
            "sender_id": self.sender_id,
            "sender_type": self.sender_type.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "message_type": self.message_type.value
        }

@dataclass
class Connection:
    """Represents a WebSocket connection"""
    connection_id: str
    websocket: WebSocket
    user_type: UserType
    user_id: Optional[str] = None
    chat_id: Optional[str] = None
    connected_at: str = None
    
    def __post_init__(self):
        if self.connected_at is None:
            self.connected_at = datetime.now().isoformat()

class LiveChatManager:
    """Manages live chat WebSocket connections and message routing"""
    
    def __init__(self):
        # Active WebSocket connections
        self.connections: Dict[str, Connection] = {}
        
        # Chat sessions: chat_id -> {customer_id, agent_id, created_at, status}
        self.chat_sessions: Dict[str, dict] = {}
        
        # Queue of customers waiting for agents
        self.customer_queue: List[str] = []
        
        # Available agents
        self.available_agents: Set[str] = set()
        
        # Agent to customer mapping
        self.agent_assignments: Dict[str, str] = {}  # agent_id -> customer_id
        
    async def connect_user(self, websocket: WebSocket, user_type: UserType, user_id: str = None) -> str:
        """Connect a new user (customer or agent)"""
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        
        if user_id is None:
            user_id = f"{user_type.value}_{connection_id[:8]}"
        
        connection = Connection(
            connection_id=connection_id,
            websocket=websocket,
            user_type=user_type,
            user_id=user_id
        )
        
        self.connections[connection_id] = connection
        
        logger.info(f"{user_type.value} {user_id} connected with connection_id {connection_id}")
        
        if user_type == UserType.AGENT:
            self.available_agents.add(user_id)
            await self._try_match_customers()
        elif user_type == UserType.CUSTOMER:
            await self._handle_customer_connection(connection)
            
        return connection_id
    
    async def disconnect_user(self, connection_id: str):
        """Disconnect a user and clean up"""
        if connection_id not in self.connections:
            return
            
        connection = self.connections[connection_id]
        user_id = connection.user_id
        user_type = connection.user_type
        
        # Clean up based on user type
        if user_type == UserType.AGENT:
            self.available_agents.discard(user_id)
            
            # If agent was in a chat, end the chat
            if user_id in self.agent_assignments:
                customer_id = self.agent_assignments[user_id]
                chat_id = self._find_chat_by_participants(customer_id, user_id)
                if chat_id:
                    await self._end_chat(chat_id, "Agent disconnected")
                del self.agent_assignments[user_id]
                
        elif user_type == UserType.CUSTOMER:
            # Remove from queue if waiting
            if user_id in self.customer_queue:
                self.customer_queue.remove(user_id)
                
            # If customer was in a chat, end the chat
            chat_id = connection.chat_id
            if chat_id and chat_id in self.chat_sessions:
                await self._end_chat(chat_id, "Customer disconnected")
        
        # Remove connection
        del self.connections[connection_id]
        logger.info(f"{user_type.value} {user_id} disconnected")
    
    async def send_message(self, connection_id: str, message_content: str) -> bool:
        """Send a chat message from a user"""
        if connection_id not in self.connections:
            return False
            
        connection = self.connections[connection_id]
        
        if not connection.chat_id:
            await self._send_to_connection(connection_id, {
                "type": MessageType.ERROR.value,
                "content": "You are not in an active chat session"
            })
            return False
        
        # Create message
        message = ChatMessage(
            message_id=str(uuid.uuid4()),
            chat_id=connection.chat_id,
            sender_id=connection.user_id,
            sender_type=connection.user_type,
            content=message_content,
            timestamp=datetime.now().isoformat()
        )
        
        # Send to all participants in the chat
        await self._broadcast_to_chat(connection.chat_id, message.to_dict())
        
        return True
    
    async def _handle_customer_connection(self, connection: Connection):
        """Handle new customer connection"""
        customer_id = connection.user_id
        
        # Check if there are available agents
        if self.available_agents:
            await self._match_customer_with_agent(customer_id)
        else:
            # Add to queue
            self.customer_queue.append(customer_id)
            await self._send_to_connection(connection.connection_id, {
                "type": MessageType.SYSTEM.value,
                "content": "You are in the queue. An agent will be with you shortly.",
                "queue_position": len(self.customer_queue)
            })
    
    async def _try_match_customers(self):
        """Try to match waiting customers with available agents"""
        while self.customer_queue and self.available_agents:
            customer_id = self.customer_queue.pop(0)
            await self._match_customer_with_agent(customer_id)
    
    async def _match_customer_with_agent(self, customer_id: str):
        """Match a customer with an available agent"""
        if not self.available_agents:
            return False
            
        # Get an available agent
        agent_id = self.available_agents.pop()
        
        # Create chat session
        chat_id = str(uuid.uuid4())
        
        self.chat_sessions[chat_id] = {
            "chat_id": chat_id,
            "customer_id": customer_id,
            "agent_id": agent_id,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.agent_assignments[agent_id] = customer_id
        
        # Update connection chat_ids
        customer_connection = self._find_connection_by_user_id(customer_id)
        agent_connection = self._find_connection_by_user_id(agent_id)
        
        if customer_connection:
            customer_connection.chat_id = chat_id
        if agent_connection:
            agent_connection.chat_id = chat_id
        
        # Notify both parties
        await self._send_to_user(customer_id, {
            "type": MessageType.AGENT_JOINED.value,
            "content": f"Agent {agent_id} has joined the chat. How can I help you today?",
            "chat_id": chat_id
        })
        
        await self._send_to_user(agent_id, {
            "type": MessageType.CUSTOMER_JOINED.value,
            "content": f"Customer {customer_id} has been assigned to you.",
            "chat_id": chat_id
        })
        
        logger.info(f"Matched customer {customer_id} with agent {agent_id} in chat {chat_id}")
        return True
    
    async def _end_chat(self, chat_id: str, reason: str = "Chat ended"):
        """End a chat session"""
        if chat_id not in self.chat_sessions:
            return
            
        session = self.chat_sessions[chat_id]
        customer_id = session["customer_id"]
        agent_id = session["agent_id"]
        
        # Notify participants
        await self._broadcast_to_chat(chat_id, {
            "type": MessageType.CHAT_ENDED.value,
            "content": reason,
            "chat_id": chat_id
        })
        
        # Clean up
        self.chat_sessions[chat_id]["status"] = "ended"
        
        # Reset agent availability
        if agent_id in self.agent_assignments:
            del self.agent_assignments[agent_id]
            self.available_agents.add(agent_id)
        
        # Clear chat_id from connections
        customer_connection = self._find_connection_by_user_id(customer_id)
        agent_connection = self._find_connection_by_user_id(agent_id)
        
        if customer_connection:
            customer_connection.chat_id = None
        if agent_connection:
            agent_connection.chat_id = None
            
        # Try to match agent with waiting customers
        await self._try_match_customers()
        
        logger.info(f"Ended chat {chat_id}: {reason}")
    
    async def _broadcast_to_chat(self, chat_id: str, message: dict):
        """Broadcast message to all participants in a chat"""
        if chat_id not in self.chat_sessions:
            return
            
        session = self.chat_sessions[chat_id]
        customer_id = session["customer_id"]
        agent_id = session["agent_id"]
        
        await self._send_to_user(customer_id, message)
        await self._send_to_user(agent_id, message)
    
    async def _send_to_user(self, user_id: str, message: dict):
        """Send message to a specific user"""
        connection = self._find_connection_by_user_id(user_id)
        if connection:
            await self._send_to_connection(connection.connection_id, message)
    
    async def _send_to_connection(self, connection_id: str, message: dict):
        """Send message to a specific connection"""
        if connection_id not in self.connections:
            return
            
        connection = self.connections[connection_id]
        try:
            await connection.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            # Connection might be dead, clean it up
            await self.disconnect_user(connection_id)
    
    def _find_connection_by_user_id(self, user_id: str) -> Optional[Connection]:
        """Find connection by user ID"""
        for connection in self.connections.values():
            if connection.user_id == user_id:
                return connection
        return None
    
    def _find_chat_by_participants(self, customer_id: str, agent_id: str) -> Optional[str]:
        """Find chat ID by participant IDs"""
        for chat_id, session in self.chat_sessions.items():
            if (session["customer_id"] == customer_id and 
                session["agent_id"] == agent_id and 
                session["status"] == "active"):
                return chat_id
        return None
    
    def get_stats(self) -> dict:
        """Get system statistics"""
        active_chats = sum(1 for session in self.chat_sessions.values() 
                          if session["status"] == "active")
        
        return {
            "total_connections": len(self.connections),
            "available_agents": len(self.available_agents),
            "customers_in_queue": len(self.customer_queue),
            "active_chats": active_chats,
            "total_chat_sessions": len(self.chat_sessions)
        }

# Global instance
live_chat_manager = LiveChatManager()