"""
Agent communication protocol for Daneel.

This module provides a protocol for communication between agents.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import uuid
import json

from Daneel.core.common import JSONSerializable
from Daneel.core.agents import AgentId


class MessageType(str, Enum):
    """Types of messages in the agent communication protocol."""
    
    # Basic message types
    TEXT = "text"
    COMMAND = "command"
    QUERY = "query"
    RESPONSE = "response"
    
    # Task-related message types
    TASK_REQUEST = "task_request"
    TASK_ASSIGNMENT = "task_assignment"
    TASK_STATUS = "task_status"
    TASK_RESULT = "task_result"
    
    # Coordination message types
    COORDINATION = "coordination"
    CONSENSUS = "consensus"
    VOTE = "vote"
    
    # Knowledge-related message types
    KNOWLEDGE_SHARE = "knowledge_share"
    KNOWLEDGE_REQUEST = "knowledge_request"
    
    # System message types
    SYSTEM = "system"
    ERROR = "error"


class MessagePriority(str, Enum):
    """Priority levels for messages."""
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class AgentMessage:
    """Message in the agent communication protocol."""
    
    id: str
    type: MessageType
    sender_id: AgentId
    receiver_id: Optional[AgentId]
    content: str
    timestamp: datetime
    priority: MessagePriority = MessagePriority.NORMAL
    in_reply_to: Optional[str] = None
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        type: MessageType,
        sender_id: AgentId,
        receiver_id: Optional[AgentId],
        content: str,
        priority: MessagePriority = MessagePriority.NORMAL,
        in_reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, JSONSerializable]] = None,
    ) -> AgentMessage:
        """Create a new message.
        
        Args:
            type: Message type
            sender_id: Sender agent ID
            receiver_id: Receiver agent ID (None for broadcast)
            content: Message content
            priority: Message priority
            in_reply_to: ID of the message this is a reply to
            metadata: Additional metadata
            
        Returns:
            Created message
        """
        return cls(
            id=str(uuid.uuid4()),
            type=type,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            timestamp=datetime.now(timezone.utc),
            priority=priority,
            in_reply_to=in_reply_to,
            metadata=metadata or {},
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        return {
            "id": self.id,
            "type": self.type.value,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "in_reply_to": self.in_reply_to,
            "metadata": self.metadata,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentMessage:
        """Create a message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            Created message
        """
        return cls(
            id=data["id"],
            type=MessageType(data["type"]),
            sender_id=AgentId(data["sender_id"]),
            receiver_id=AgentId(data["receiver_id"]) if data.get("receiver_id") else None,
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            priority=MessagePriority(data["priority"]),
            in_reply_to=data.get("in_reply_to"),
            metadata=data.get("metadata", {}),
        )
        
    def to_json(self) -> str:
        """Convert the message to a JSON string.
        
        Returns:
            JSON string representation of the message
        """
        return json.dumps(self.to_dict())
        
    @classmethod
    def from_json(cls, json_str: str) -> AgentMessage:
        """Create a message from a JSON string.
        
        Args:
            json_str: JSON string representation of the message
            
        Returns:
            Created message
        """
        return cls.from_dict(json.loads(json_str))


class MessageBus:
    """Message bus for agent communication."""
    
    def __init__(self):
        """Initialize the message bus."""
        self._subscribers: Dict[AgentId, List[callable]] = {}
        self._broadcast_subscribers: List[callable] = []
        
    async def publish(self, message: AgentMessage) -> None:
        """Publish a message to the bus.
        
        Args:
            message: Message to publish
        """
        # Handle broadcast messages
        if message.receiver_id is None:
            for callback in self._broadcast_subscribers:
                await callback(message)
            return
            
        # Handle directed messages
        if message.receiver_id in self._subscribers:
            for callback in self._subscribers[message.receiver_id]:
                await callback(message)
                
    def subscribe(
        self,
        agent_id: AgentId,
        callback: callable,
    ) -> None:
        """Subscribe to messages for a specific agent.
        
        Args:
            agent_id: Agent ID to subscribe to
            callback: Callback function to call when a message is received
        """
        if agent_id not in self._subscribers:
            self._subscribers[agent_id] = []
            
        self._subscribers[agent_id].append(callback)
        
    def subscribe_broadcast(self, callback: callable) -> None:
        """Subscribe to broadcast messages.
        
        Args:
            callback: Callback function to call when a broadcast message is received
        """
        self._broadcast_subscribers.append(callback)
        
    def unsubscribe(self, agent_id: AgentId, callback: callable) -> None:
        """Unsubscribe from messages for a specific agent.
        
        Args:
            agent_id: Agent ID to unsubscribe from
            callback: Callback function to remove
        """
        if agent_id in self._subscribers:
            self._subscribers[agent_id].remove(callback)
            
    def unsubscribe_broadcast(self, callback: callable) -> None:
        """Unsubscribe from broadcast messages.
        
        Args:
            callback: Callback function to remove
        """
        self._broadcast_subscribers.remove(callback)


class AgentCommunicator:
    """Communicator for agent-to-agent communication."""
    
    def __init__(
        self,
        agent_id: AgentId,
        message_bus: MessageBus,
    ):
        """Initialize the agent communicator.
        
        Args:
            agent_id: Agent ID
            message_bus: Message bus to use for communication
        """
        self.agent_id = agent_id
        self._message_bus = message_bus
        self._message_handlers: Dict[MessageType, List[callable]] = {}
        
        # Subscribe to messages for this agent
        self._message_bus.subscribe(agent_id, self._handle_message)
        
    async def _handle_message(self, message: AgentMessage) -> None:
        """Handle a received message.
        
        Args:
            message: Received message
        """
        if message.type in self._message_handlers:
            for handler in self._message_handlers[message.type]:
                await handler(message)
                
    def register_handler(
        self,
        message_type: MessageType,
        handler: callable,
    ) -> None:
        """Register a handler for a specific message type.
        
        Args:
            message_type: Message type to handle
            handler: Handler function to call when a message of this type is received
        """
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
            
        self._message_handlers[message_type].append(handler)
        
    def unregister_handler(
        self,
        message_type: MessageType,
        handler: callable,
    ) -> None:
        """Unregister a handler for a specific message type.
        
        Args:
            message_type: Message type to unregister from
            handler: Handler function to remove
        """
        if message_type in self._message_handlers:
            self._message_handlers[message_type].remove(handler)
            
    async def send_message(
        self,
        receiver_id: Optional[AgentId],
        message_type: MessageType,
        content: str,
        priority: MessagePriority = MessagePriority.NORMAL,
        in_reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, JSONSerializable]] = None,
    ) -> AgentMessage:
        """Send a message to another agent.
        
        Args:
            receiver_id: Receiver agent ID (None for broadcast)
            message_type: Message type
            content: Message content
            priority: Message priority
            in_reply_to: ID of the message this is a reply to
            metadata: Additional metadata
            
        Returns:
            Sent message
        """
        message = AgentMessage.create(
            type=message_type,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            content=content,
            priority=priority,
            in_reply_to=in_reply_to,
            metadata=metadata,
        )
        
        await self._message_bus.publish(message)
        
        return message
        
    async def send_text(
        self,
        receiver_id: AgentId,
        text: str,
        priority: MessagePriority = MessagePriority.NORMAL,
        in_reply_to: Optional[str] = None,
    ) -> AgentMessage:
        """Send a text message to another agent.
        
        Args:
            receiver_id: Receiver agent ID
            text: Text content
            priority: Message priority
            in_reply_to: ID of the message this is a reply to
            
        Returns:
            Sent message
        """
        return await self.send_message(
            receiver_id=receiver_id,
            message_type=MessageType.TEXT,
            content=text,
            priority=priority,
            in_reply_to=in_reply_to,
        )
        
    async def broadcast(
        self,
        message_type: MessageType,
        content: str,
        priority: MessagePriority = MessagePriority.NORMAL,
        metadata: Optional[Dict[str, JSONSerializable]] = None,
    ) -> AgentMessage:
        """Broadcast a message to all agents.
        
        Args:
            message_type: Message type
            content: Message content
            priority: Message priority
            metadata: Additional metadata
            
        Returns:
            Sent message
        """
        return await self.send_message(
            receiver_id=None,
            message_type=message_type,
            content=content,
            priority=priority,
            metadata=metadata,
        )
