"""
Interaction history tracking for Parlant.

This module provides functionality for tracking agent interactions and outcomes.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid
import json

from parlant.core.common import JSONSerializable, generate_id
from parlant.core.agents import Agent, AgentId, AgentStore
from parlant.core.loggers import Logger
from parlant.core.async_utils import ReaderWriterLock
from parlant.core.persistence.document_database import DocumentCollection, DocumentDatabase
from parlant.core.persistence.common import ItemNotFoundError, ObjectId, UniqueId, Where


class InteractionType(str, Enum):
    """Types of agent interactions."""
    
    USER_MESSAGE = "user_message"
    AGENT_MESSAGE = "agent_message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FEEDBACK = "feedback"
    ERROR = "error"
    SYSTEM = "system"


class FeedbackType(str, Enum):
    """Types of feedback."""
    
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    RATING = "rating"
    TEXT = "text"
    CORRECTION = "correction"


class InteractionId(str):
    """Interaction ID."""
    pass


class InteractionSessionId(str):
    """Interaction session ID."""
    pass


@dataclass
class Feedback:
    """Feedback for an interaction."""
    
    type: FeedbackType
    value: Union[str, int, float, bool]
    timestamp: datetime
    source: str
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


@dataclass
class Interaction:
    """Agent interaction."""
    
    id: InteractionId
    session_id: InteractionSessionId
    agent_id: AgentId
    type: InteractionType
    content: str
    timestamp: datetime
    feedback: List[Feedback] = field(default_factory=list)
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class _InteractionDocument(Dict[str, Any]):
    """Interaction document for storage."""
    pass


class InteractionHistoryTracker:
    """Tracker for agent interactions."""
    
    VERSION = "0.1.0"
    
    def __init__(
        self,
        document_db: DocumentDatabase,
        agent_store: AgentStore,
        logger: Logger,
    ):
        """Initialize the interaction history tracker.
        
        Args:
            document_db: Document database
            agent_store: Agent store
            logger: Logger instance
        """
        self._document_db = document_db
        self._agent_store = agent_store
        self._logger = logger
        
        self._interaction_collection: Optional[DocumentCollection[_InteractionDocument]] = None
        self._lock = ReaderWriterLock()
        
    async def __aenter__(self) -> InteractionHistoryTracker:
        """Enter the context manager."""
        self._interaction_collection = await self._document_db.get_or_create_collection(
            name="agent_interactions",
            schema=_InteractionDocument,
        )
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        pass
        
    def _serialize(self, interaction: Interaction) -> _InteractionDocument:
        """Serialize an interaction.
        
        Args:
            interaction: Interaction to serialize
            
        Returns:
            Serialized interaction document
        """
        return {
            "id": interaction.id,
            "version": self.VERSION,
            "session_id": interaction.session_id,
            "agent_id": interaction.agent_id,
            "type": interaction.type.value,
            "content": interaction.content,
            "timestamp": interaction.timestamp.isoformat(),
            "feedback": [
                {
                    "type": feedback.type.value,
                    "value": feedback.value,
                    "timestamp": feedback.timestamp.isoformat(),
                    "source": feedback.source,
                    "metadata": feedback.metadata,
                }
                for feedback in interaction.feedback
            ],
            "metadata": interaction.metadata,
        }
        
    def _deserialize(self, document: _InteractionDocument) -> Interaction:
        """Deserialize an interaction document.
        
        Args:
            document: Interaction document
            
        Returns:
            Deserialized interaction
        """
        return Interaction(
            id=InteractionId(document["id"]),
            session_id=InteractionSessionId(document["session_id"]),
            agent_id=AgentId(document["agent_id"]),
            type=InteractionType(document["type"]),
            content=document["content"],
            timestamp=datetime.fromisoformat(document["timestamp"]),
            feedback=[
                Feedback(
                    type=FeedbackType(feedback["type"]),
                    value=feedback["value"],
                    timestamp=datetime.fromisoformat(feedback["timestamp"]),
                    source=feedback["source"],
                    metadata=feedback["metadata"],
                )
                for feedback in document.get("feedback", [])
            ],
            metadata=document.get("metadata", {}),
        )
        
    async def track_interaction(
        self,
        session_id: InteractionSessionId,
        agent_id: AgentId,
        type: InteractionType,
        content: str,
        metadata: Optional[Dict[str, JSONSerializable]] = None,
    ) -> Interaction:
        """Track an agent interaction.
        
        Args:
            session_id: Interaction session ID
            agent_id: Agent ID
            type: Interaction type
            content: Interaction content
            metadata: Additional metadata
            
        Returns:
            Created interaction
        """
        # Verify that the agent exists
        agent = await self._agent_store.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
            
        async with self._lock.writer_lock:
            interaction = Interaction(
                id=InteractionId(generate_id()),
                session_id=session_id,
                agent_id=agent_id,
                type=type,
                content=content,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {},
            )
            
            await self._interaction_collection.insert_one(
                document=self._serialize(interaction)
            )
            
        self._logger.info(f"Tracked interaction: {type} for agent {agent_id} in session {session_id}")
        
        return interaction
        
    async def add_feedback(
        self,
        interaction_id: InteractionId,
        feedback_type: FeedbackType,
        value: Union[str, int, float, bool],
        source: str,
        metadata: Optional[Dict[str, JSONSerializable]] = None,
    ) -> Interaction:
        """Add feedback to an interaction.
        
        Args:
            interaction_id: Interaction ID
            feedback_type: Feedback type
            value: Feedback value
            source: Feedback source
            metadata: Additional metadata
            
        Returns:
            Updated interaction
        """
        async with self._lock.writer_lock:
            # Get the interaction
            document = await self._interaction_collection.find_one(
                filters={"id": {"$eq": interaction_id}}
            )
            
            if not document:
                raise ItemNotFoundError(item_id=UniqueId(interaction_id))
                
            # Create the feedback
            feedback = {
                "type": feedback_type.value,
                "value": value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": source,
                "metadata": metadata or {},
            }
            
            # Add the feedback to the interaction
            if "feedback" not in document:
                document["feedback"] = []
                
            document["feedback"].append(feedback)
            
            # Update the interaction
            await self._interaction_collection.update_one(
                filters={"id": {"$eq": interaction_id}},
                params={"feedback": document["feedback"]},
            )
            
            # Get the updated document
            document = await self._interaction_collection.find_one(
                filters={"id": {"$eq": interaction_id}}
            )
            
        self._logger.info(f"Added {feedback_type} feedback to interaction {interaction_id}")
        
        return self._deserialize(document)
        
    async def get_interaction(self, interaction_id: InteractionId) -> Optional[Interaction]:
        """Get an interaction by ID.
        
        Args:
            interaction_id: Interaction ID
            
        Returns:
            Interaction if found, None otherwise
        """
        async with self._lock.reader_lock:
            document = await self._interaction_collection.find_one(
                filters={"id": {"$eq": interaction_id}}
            )
            
            if not document:
                return None
                
            return self._deserialize(document)
            
    async def list_interactions(
        self,
        session_id: Optional[InteractionSessionId] = None,
        agent_id: Optional[AgentId] = None,
        type: Optional[InteractionType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Interaction]:
        """List interactions with optional filtering.
        
        Args:
            session_id: Filter by session ID
            agent_id: Filter by agent ID
            type: Filter by interaction type
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of interactions to return
            offset: Offset for pagination
            
        Returns:
            List of interactions
        """
        async with self._lock.reader_lock:
            filters = {}
            
            if session_id:
                filters["session_id"] = {"$eq": session_id}
                
            if agent_id:
                filters["agent_id"] = {"$eq": agent_id}
                
            if type:
                filters["type"] = {"$eq": type.value}
                
            if start_time or end_time:
                timestamp_filter = {}
                
                if start_time:
                    timestamp_filter["$gte"] = start_time.isoformat()
                    
                if end_time:
                    timestamp_filter["$lte"] = end_time.isoformat()
                    
                filters["timestamp"] = timestamp_filter
                
            documents = await self._interaction_collection.find(
                filters=filters,
                sort=[("timestamp", -1)],
                limit=limit,
                skip=offset,
            )
            
            return [self._deserialize(document) for document in documents]
            
    async def get_session_interactions(
        self,
        session_id: InteractionSessionId,
    ) -> List[Interaction]:
        """Get all interactions for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of interactions
        """
        return await self.list_interactions(session_id=session_id, limit=1000)
        
    async def get_agent_interactions(
        self,
        agent_id: AgentId,
        limit: int = 100,
    ) -> List[Interaction]:
        """Get recent interactions for an agent.
        
        Args:
            agent_id: Agent ID
            limit: Maximum number of interactions to return
            
        Returns:
            List of interactions
        """
        return await self.list_interactions(agent_id=agent_id, limit=limit)
        
    async def get_feedback_stats(
        self,
        agent_id: AgentId,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get feedback statistics for an agent.
        
        Args:
            agent_id: Agent ID
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            Feedback statistics
        """
        interactions = await self.list_interactions(
            agent_id=agent_id,
            start_time=start_time,
            end_time=end_time,
            limit=1000,
        )
        
        # Count feedback by type
        feedback_counts = {
            FeedbackType.THUMBS_UP.value: 0,
            FeedbackType.THUMBS_DOWN.value: 0,
            FeedbackType.RATING.value: [],
            FeedbackType.TEXT.value: 0,
            FeedbackType.CORRECTION.value: 0,
        }
        
        total_feedback = 0
        
        for interaction in interactions:
            for feedback in interaction.feedback:
                feedback_counts[feedback.type.value] += 1
                
                if feedback.type == FeedbackType.RATING:
                    feedback_counts[FeedbackType.RATING.value].append(float(feedback.value))
                    
                total_feedback += 1
                
        # Calculate average rating
        avg_rating = None
        if feedback_counts[FeedbackType.RATING.value]:
            avg_rating = sum(feedback_counts[FeedbackType.RATING.value]) / len(feedback_counts[FeedbackType.RATING.value])
            
        return {
            "total_feedback": total_feedback,
            "thumbs_up": feedback_counts[FeedbackType.THUMBS_UP.value],
            "thumbs_down": feedback_counts[FeedbackType.THUMBS_DOWN.value],
            "ratings": len(feedback_counts[FeedbackType.RATING.value]),
            "avg_rating": avg_rating,
            "text_feedback": feedback_counts[FeedbackType.TEXT.value],
            "corrections": feedback_counts[FeedbackType.CORRECTION.value],
        }
