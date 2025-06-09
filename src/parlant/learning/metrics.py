"""
Performance metrics and evaluation for Daneel.

This module provides functionality for measuring agent performance and effectiveness.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid
import json
import statistics
from collections import Counter

from Daneel.core.common import JSONSerializable, generate_id
from Daneel.core.agents import Agent, AgentId, AgentStore
from Daneel.core.loggers import Logger
from Daneel.core.async_utils import ReaderWriterLock
from Daneel.core.persistence.document_database import DocumentCollection, DocumentDatabase
from Daneel.core.persistence.common import ItemNotFoundError, ObjectId, UniqueId, Where

from Daneel.learning.history import (
    InteractionHistoryTracker,
    Interaction,
    InteractionId,
    InteractionSessionId,
    InteractionType,
    FeedbackType,
)


class MetricType(str, Enum):
    """Types of performance metrics."""
    
    RESPONSE_TIME = "response_time"
    FEEDBACK_SCORE = "feedback_score"
    TASK_COMPLETION = "task_completion"
    ACCURACY = "accuracy"
    HELPFULNESS = "helpfulness"
    CONSISTENCY = "consistency"
    CUSTOM = "custom"


class MetricId(str):
    """Metric ID."""
    pass


class EvaluationId(str):
    """Evaluation ID."""
    pass


@dataclass
class MetricValue:
    """Value of a performance metric."""
    
    id: MetricId
    agent_id: AgentId
    type: MetricType
    value: float
    timestamp: datetime
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


@dataclass
class Evaluation:
    """Evaluation of agent performance."""
    
    id: EvaluationId
    agent_id: AgentId
    metrics: List[MetricValue]
    timestamp: datetime
    summary: str
    score: float
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class _MetricDocument(Dict[str, Any]):
    """Metric document for storage."""
    pass


class _EvaluationDocument(Dict[str, Any]):
    """Evaluation document for storage."""
    pass


class PerformanceMetricsTracker:
    """Tracker for agent performance metrics."""
    
    VERSION = "0.1.0"
    
    def __init__(
        self,
        document_db: DocumentDatabase,
        agent_store: AgentStore,
        interaction_tracker: InteractionHistoryTracker,
        logger: Logger,
    ):
        """Initialize the performance metrics tracker.
        
        Args:
            document_db: Document database
            agent_store: Agent store
            interaction_tracker: Interaction history tracker
            logger: Logger instance
        """
        self._document_db = document_db
        self._agent_store = agent_store
        self._interaction_tracker = interaction_tracker
        self._logger = logger
        
        self._metric_collection: Optional[DocumentCollection[_MetricDocument]] = None
        self._evaluation_collection: Optional[DocumentCollection[_EvaluationDocument]] = None
        self._lock = ReaderWriterLock()
        
    async def __aenter__(self) -> PerformanceMetricsTracker:
        """Enter the context manager."""
        self._metric_collection = await self._document_db.get_or_create_collection(
            name="agent_metrics",
            schema=_MetricDocument,
        )
        
        self._evaluation_collection = await self._document_db.get_or_create_collection(
            name="agent_evaluations",
            schema=_EvaluationDocument,
        )
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        pass
        
    def _serialize_metric(self, metric: MetricValue) -> _MetricDocument:
        """Serialize a metric value.
        
        Args:
            metric: Metric value to serialize
            
        Returns:
            Serialized metric document
        """
        return {
            "id": metric.id,
            "version": self.VERSION,
            "agent_id": metric.agent_id,
            "type": metric.type.value,
            "value": metric.value,
            "timestamp": metric.timestamp.isoformat(),
            "metadata": metric.metadata,
        }
        
    def _deserialize_metric(self, document: _MetricDocument) -> MetricValue:
        """Deserialize a metric document.
        
        Args:
            document: Metric document
            
        Returns:
            Deserialized metric value
        """
        return MetricValue(
            id=MetricId(document["id"]),
            agent_id=AgentId(document["agent_id"]),
            type=MetricType(document["type"]),
            value=document["value"],
            timestamp=datetime.fromisoformat(document["timestamp"]),
            metadata=document.get("metadata", {}),
        )
        
    def _serialize_evaluation(self, evaluation: Evaluation) -> _EvaluationDocument:
        """Serialize an evaluation.
        
        Args:
            evaluation: Evaluation to serialize
            
        Returns:
            Serialized evaluation document
        """
        return {
            "id": evaluation.id,
            "version": self.VERSION,
            "agent_id": evaluation.agent_id,
            "metrics": [self._serialize_metric(metric) for metric in evaluation.metrics],
            "timestamp": evaluation.timestamp.isoformat(),
            "summary": evaluation.summary,
            "score": evaluation.score,
            "metadata": evaluation.metadata,
        }
        
    def _deserialize_evaluation(self, document: _EvaluationDocument) -> Evaluation:
        """Deserialize an evaluation document.
        
        Args:
            document: Evaluation document
            
        Returns:
            Deserialized evaluation
        """
        return Evaluation(
            id=EvaluationId(document["id"]),
            agent_id=AgentId(document["agent_id"]),
            metrics=[self._deserialize_metric(metric) for metric in document["metrics"]],
            timestamp=datetime.fromisoformat(document["timestamp"]),
            summary=document["summary"],
            score=document["score"],
            metadata=document.get("metadata", {}),
        )
        
    async def track_metric(
        self,
        agent_id: AgentId,
        type: MetricType,
        value: float,
        metadata: Optional[Dict[str, JSONSerializable]] = None,
    ) -> MetricValue:
        """Track a performance metric.
        
        Args:
            agent_id: Agent ID
            type: Metric type
            value: Metric value
            metadata: Additional metadata
            
        Returns:
            Created metric value
        """
        # Verify that the agent exists
        agent = await self._agent_store.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
            
        async with self._lock.writer_lock:
            metric = MetricValue(
                id=MetricId(generate_id()),
                agent_id=agent_id,
                type=type,
                value=value,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {},
            )
            
            await self._metric_collection.insert_one(
                document=self._serialize_metric(metric)
            )
            
        self._logger.info(f"Tracked metric: {type} = {value} for agent {agent_id}")
        
        return metric
        
    async def get_metric(self, metric_id: MetricId) -> Optional[MetricValue]:
        """Get a metric by ID.
        
        Args:
            metric_id: Metric ID
            
        Returns:
            Metric value if found, None otherwise
        """
        async with self._lock.reader_lock:
            document = await self._metric_collection.find_one(
                filters={"id": {"$eq": metric_id}}
            )
            
            if not document:
                return None
                
            return self._deserialize_metric(document)
            
    async def list_metrics(
        self,
        agent_id: Optional[AgentId] = None,
        type: Optional[MetricType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MetricValue]:
        """List metrics with optional filtering.
        
        Args:
            agent_id: Filter by agent ID
            type: Filter by metric type
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of metrics to return
            offset: Offset for pagination
            
        Returns:
            List of metrics
        """
        async with self._lock.reader_lock:
            filters = {}
            
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
                
            documents = await self._metric_collection.find(
                filters=filters,
                sort=[("timestamp", -1)],
                limit=limit,
                skip=offset,
            )
            
            return [self._deserialize_metric(document) for document in documents]
            
    async def get_metric_stats(
        self,
        agent_id: AgentId,
        type: MetricType,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get statistics for a metric.
        
        Args:
            agent_id: Agent ID
            type: Metric type
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            Metric statistics
        """
        metrics = await self.list_metrics(
            agent_id=agent_id,
            type=type,
            start_time=start_time,
            end_time=end_time,
            limit=1000,
        )
        
        if not metrics:
            return {
                "count": 0,
                "min": None,
                "max": None,
                "mean": None,
                "median": None,
                "std_dev": None,
            }
            
        values = [metric.value for metric in metrics]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
        }
        
    async def create_evaluation(
        self,
        agent_id: AgentId,
        metrics: List[MetricValue],
        summary: str,
        score: float,
        metadata: Optional[Dict[str, JSONSerializable]] = None,
    ) -> Evaluation:
        """Create an evaluation of agent performance.
        
        Args:
            agent_id: Agent ID
            metrics: Metrics to include in the evaluation
            summary: Evaluation summary
            score: Overall evaluation score
            metadata: Additional metadata
            
        Returns:
            Created evaluation
        """
        # Verify that the agent exists
        agent = await self._agent_store.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
            
        async with self._lock.writer_lock:
            evaluation = Evaluation(
                id=EvaluationId(generate_id()),
                agent_id=agent_id,
                metrics=metrics,
                timestamp=datetime.now(timezone.utc),
                summary=summary,
                score=score,
                metadata=metadata or {},
            )
            
            await self._evaluation_collection.insert_one(
                document=self._serialize_evaluation(evaluation)
            )
            
        self._logger.info(f"Created evaluation for agent {agent_id} with score {score}")
        
        return evaluation
        
    async def get_evaluation(self, evaluation_id: EvaluationId) -> Optional[Evaluation]:
        """Get an evaluation by ID.
        
        Args:
            evaluation_id: Evaluation ID
            
        Returns:
            Evaluation if found, None otherwise
        """
        async with self._lock.reader_lock:
            document = await self._evaluation_collection.find_one(
                filters={"id": {"$eq": evaluation_id}}
            )
            
            if not document:
                return None
                
            return self._deserialize_evaluation(document)
            
    async def list_evaluations(
        self,
        agent_id: Optional[AgentId] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Evaluation]:
        """List evaluations with optional filtering.
        
        Args:
            agent_id: Filter by agent ID
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of evaluations to return
            offset: Offset for pagination
            
        Returns:
            List of evaluations
        """
        async with self._lock.reader_lock:
            filters = {}
            
            if agent_id:
                filters["agent_id"] = {"$eq": agent_id}
                
            if start_time or end_time:
                timestamp_filter = {}
                
                if start_time:
                    timestamp_filter["$gte"] = start_time.isoformat()
                    
                if end_time:
                    timestamp_filter["$lte"] = end_time.isoformat()
                    
                filters["timestamp"] = timestamp_filter
                
            documents = await self._evaluation_collection.find(
                filters=filters,
                sort=[("timestamp", -1)],
                limit=limit,
                skip=offset,
            )
            
            return [self._deserialize_evaluation(document) for document in documents]
