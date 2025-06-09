"""
Behavior adaptation for Daneel.

This module provides functionality for adapting agent behavior over time.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid
import json
import asyncio

from Daneel.core.common import JSONSerializable, generate_id
from Daneel.core.agents import Agent, AgentId, AgentStore
from Daneel.core.loggers import Logger
from Daneel.core.async_utils import ReaderWriterLock
from Daneel.core.persistence.document_database import DocumentCollection, DocumentDatabase
from Daneel.core.persistence.common import ItemNotFoundError, ObjectId, UniqueId, Where
from Daneel.core.nlp.service import NLPService
from Daneel.core.nlp.generation_info import GenerationInfo
from Daneel.core.prompts import Prompt, PromptManager

from Daneel.learning.history import (
    InteractionHistoryTracker,
    Interaction,
    InteractionId,
    InteractionSessionId,
    InteractionType,
    FeedbackType,
)
from Daneel.learning.metrics import (
    PerformanceMetricsTracker,
    MetricType,
    MetricValue,
    Evaluation,
)
from Daneel.learning.feedback import (
    FeedbackLearner,
    FeedbackPattern,
    LearningStrategy,
)


class AdaptationType(str, Enum):
    """Types of behavior adaptations."""

    PROMPT_MODIFICATION = "prompt_modification"
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    TOOL_USAGE = "tool_usage"
    RESPONSE_STYLE = "response_style"
    CUSTOM = "custom"


class AdaptationId(str):
    """Adaptation ID."""
    pass


@dataclass
class BehaviorAdaptation:
    """Adaptation to agent behavior."""

    id: AdaptationId
    agent_id: AgentId
    type: AdaptationType
    description: str
    creation_utc: datetime
    applied: bool
    confidence: float
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class _AdaptationDocument(Dict[str, Any]):
    """Adaptation document for storage."""
    pass


class BehaviorAdapter:
    """Adapter for agent behavior."""

    VERSION = "0.1.0"

    def __init__(
        self,
        document_db: DocumentDatabase,
        agent_store: AgentStore,
        interaction_tracker: InteractionHistoryTracker,
        metrics_tracker: PerformanceMetricsTracker,
        feedback_learner: FeedbackLearner,
        prompt_manager: PromptManager,
        nlp_service: NLPService,
        logger: Logger,
    ):
        """Initialize the behavior adapter.

        Args:
            document_db: Document database
            agent_store: Agent store
            interaction_tracker: Interaction history tracker
            metrics_tracker: Performance metrics tracker
            feedback_learner: Feedback learner
            prompt_manager: Prompt manager
            nlp_service: NLP service
            logger: Logger instance
        """
        self._document_db = document_db
        self._agent_store = agent_store
        self._interaction_tracker = interaction_tracker
        self._metrics_tracker = metrics_tracker
        self._feedback_learner = feedback_learner
        self._prompt_manager = prompt_manager
        self._nlp_service = nlp_service
        self._logger = logger

        self._adaptation_collection: Optional[DocumentCollection[_AdaptationDocument]] = None
        self._lock = ReaderWriterLock()

    async def __aenter__(self) -> BehaviorAdapter:
        """Enter the context manager."""
        self._adaptation_collection = await self._document_db.get_or_create_collection(
            name="behavior_adaptations",
            schema=_AdaptationDocument,
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        pass

    def _serialize_adaptation(self, adaptation: BehaviorAdaptation) -> _AdaptationDocument:
        """Serialize a behavior adaptation.

        Args:
            adaptation: Behavior adaptation to serialize

        Returns:
            Serialized adaptation document
        """
        return {
            "id": adaptation.id,
            "version": self.VERSION,
            "agent_id": adaptation.agent_id,
            "type": adaptation.type.value,
            "description": adaptation.description,
            "creation_utc": adaptation.creation_utc.isoformat(),
            "applied": adaptation.applied,
            "confidence": adaptation.confidence,
            "before_state": adaptation.before_state,
            "after_state": adaptation.after_state,
            "metadata": adaptation.metadata,
        }

    def _deserialize_adaptation(self, document: _AdaptationDocument) -> BehaviorAdaptation:
        """Deserialize an adaptation document.

        Args:
            document: Adaptation document

        Returns:
            Deserialized behavior adaptation
        """
        return BehaviorAdaptation(
            id=AdaptationId(document["id"]),
            agent_id=AgentId(document["agent_id"]),
            type=AdaptationType(document["type"]),
            description=document["description"],
            creation_utc=datetime.fromisoformat(document["creation_utc"]),
            applied=document["applied"],
            confidence=document["confidence"],
            before_state=document["before_state"],
            after_state=document["after_state"],
            metadata=document.get("metadata", {}),
        )

    async def generate_adaptations(
        self,
        agent_id: AgentId,
        days: int = 30,
    ) -> List[BehaviorAdaptation]:
        """Generate behavior adaptations based on feedback and metrics.

        Args:
            agent_id: Agent ID
            days: Number of days of data to analyze

        Returns:
            List of generated behavior adaptations
        """
        # Verify that the agent exists
        agent = await self._agent_store.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        self._logger.info(f"Generating behavior adaptations for agent {agent_id}")

        # Get feedback patterns
        patterns = await self._feedback_learner.list_patterns(
            agent_id=agent_id,
            min_confidence=0.7,
        )

        # Get performance metrics
        start_time = datetime.now(timezone.utc) - timedelta(days=days)
        metrics = await self._metrics_tracker.list_metrics(
            agent_id=agent_id,
            start_time=start_time,
            limit=1000,
        )

        # Generate adaptations
        adaptations = []

        # Generate prompt modifications based on feedback patterns
        prompt_adaptations = await self._generate_prompt_adaptations(agent_id, patterns)
        adaptations.extend(prompt_adaptations)

        # Generate parameter adjustments based on metrics
        parameter_adaptations = await self._generate_parameter_adaptations(agent_id, metrics)
        adaptations.extend(parameter_adaptations)

        # Generate response style adaptations
        style_adaptations = await self._generate_style_adaptations(agent_id, patterns)
        adaptations.extend(style_adaptations)

        # Save the adaptations
        for adaptation in adaptations:
            await self.save_adaptation(adaptation)

        return adaptations

    async def _generate_prompt_adaptations(
        self,
        agent_id: AgentId,
        patterns: List[FeedbackPattern],
    ) -> List[BehaviorAdaptation]:
        """Generate prompt modification adaptations.

        Args:
            agent_id: Agent ID
            patterns: Feedback patterns

        Returns:
            List of prompt modification adaptations
        """
        adaptations = []

        if not patterns:
            return adaptations

        # Get the agent's current prompts
        agent = await self._agent_store.get_agent(agent_id)
        if not agent:
            return adaptations

        # TODO: Get the agent's prompts from the prompt manager
        # For now, we'll create a generic prompt adaptation

        # Create a prompt for generating prompt adaptations
        prompt = self._create_prompt_adaptation_prompt(patterns)

        # Generate prompt adaptations
        generator = await self._nlp_service.get_generator()
        generation_result = await generator.generate(prompt)

        # Parse the adaptations
        parsed_adaptations = self._parse_prompt_adaptations(agent_id, generation_result.text)

        adaptations.extend(parsed_adaptations)

        return adaptations

    def _create_prompt_adaptation_prompt(
        self,
        patterns: List[FeedbackPattern],
    ) -> str:
        """Create a prompt for generating prompt adaptations.

        Args:
            patterns: Feedback patterns

        Returns:
            Prompt for generating prompt adaptations
        """
        prompt = """You are an AI assistant tasked with generating prompt modifications based on feedback patterns.
I will provide you with a set of feedback patterns. Your task is to suggest modifications to the agent's prompts to improve its behavior.

Feedback patterns:
"""

        for i, pattern in enumerate(patterns):
            prompt += f"\n{i+1}. {pattern.description}\n"

            for before, after in pattern.examples:
                prompt += f"   Before: {before}\n"
                prompt += f"   After: {after}\n"

        prompt += """
Based on these patterns, suggest modifications to the agent's prompts. For each modification, provide:
1. A description of the modification
2. The before state (what the prompt might look like now)
3. The after state (what the prompt should look like after the modification)

Format your response as follows:
MODIFICATION 1:
Description: [Description of the modification]
Before: [Example of the prompt before modification]
After: [Example of the prompt after modification]

MODIFICATION 2:
...
"""

        return prompt

    def _parse_prompt_adaptations(
        self,
        agent_id: AgentId,
        adaptation_text: str,
    ) -> List[BehaviorAdaptation]:
        """Parse prompt adaptations from adaptation text.

        Args:
            agent_id: Agent ID
            adaptation_text: Adaptation text

        Returns:
            List of behavior adaptations
        """
        adaptations = []

        # Split the text into modification sections
        modification_sections = adaptation_text.split("MODIFICATION ")

        for section in modification_sections[1:]:  # Skip the first empty section
            try:
                # Extract modification information
                lines = section.strip().split("\n")

                # Extract description
                description_line = next((line for line in lines if line.startswith("Description:")), "")
                description = description_line.split(":", 1)[1].strip() if description_line else ""

                # Extract before and after states
                before_line_idx = next((i for i, line in enumerate(lines) if line.startswith("Before:")), -1)
                after_line_idx = next((i for i, line in enumerate(lines) if line.startswith("After:")), -1)

                if before_line_idx != -1 and after_line_idx != -1:
                    before_state = {"prompt": lines[before_line_idx].split(":", 1)[1].strip()}
                    after_state = {"prompt": lines[after_line_idx].split(":", 1)[1].strip()}

                    adaptation = BehaviorAdaptation(
                        id=AdaptationId(generate_id()),
                        agent_id=agent_id,
                        type=AdaptationType.PROMPT_MODIFICATION,
                        description=description,
                        creation_utc=datetime.now(timezone.utc),
                        applied=False,
                        confidence=0.7,
                        before_state=before_state,
                        after_state=after_state,
                    )

                    adaptations.append(adaptation)

            except Exception as e:
                self._logger.error(f"Error parsing prompt adaptation section: {e}")

        return adaptations

    async def _generate_parameter_adaptations(
        self,
        agent_id: AgentId,
        metrics: List[MetricValue],
    ) -> List[BehaviorAdaptation]:
        """Generate parameter adjustment adaptations.

        Args:
            agent_id: Agent ID
            metrics: Performance metrics

        Returns:
            List of parameter adjustment adaptations
        """
        adaptations = []

        if not metrics:
            return adaptations

        # Group metrics by type
        metrics_by_type = {}
        for metric in metrics:
            if metric.type not in metrics_by_type:
                metrics_by_type[metric.type] = []

            metrics_by_type[metric.type].append(metric)

        # Generate adaptations based on response time metrics
        if MetricType.RESPONSE_TIME in metrics_by_type:
            response_time_metrics = metrics_by_type[MetricType.RESPONSE_TIME]

            # Calculate average response time
            avg_response_time = sum(metric.value for metric in response_time_metrics) / len(response_time_metrics)

            # If response time is too high, suggest parameter adjustments
            if avg_response_time > 5.0:  # More than 5 seconds
                adaptation = BehaviorAdaptation(
                    id=AdaptationId(generate_id()),
                    agent_id=agent_id,
                    type=AdaptationType.PARAMETER_ADJUSTMENT,
                    description="Reduce response time by adjusting model parameters",
                    creation_utc=datetime.now(timezone.utc),
                    applied=False,
                    confidence=0.8,
                    before_state={"temperature": 0.7, "max_tokens": 1000},
                    after_state={"temperature": 0.5, "max_tokens": 800},
                )

                adaptations.append(adaptation)

        # Generate adaptations based on feedback score metrics
        if MetricType.FEEDBACK_SCORE in metrics_by_type:
            feedback_score_metrics = metrics_by_type[MetricType.FEEDBACK_SCORE]

            # Calculate average feedback score
            avg_feedback_score = sum(metric.value for metric in feedback_score_metrics) / len(feedback_score_metrics)

            # If feedback score is too low, suggest parameter adjustments
            if avg_feedback_score < 0.7:  # Less than 70%
                adaptation = BehaviorAdaptation(
                    id=AdaptationId(generate_id()),
                    agent_id=agent_id,
                    type=AdaptationType.PARAMETER_ADJUSTMENT,
                    description="Improve response quality by adjusting model parameters",
                    creation_utc=datetime.now(timezone.utc),
                    applied=False,
                    confidence=0.7,
                    before_state={"temperature": 0.7, "top_p": 0.9},
                    after_state={"temperature": 0.8, "top_p": 0.95},
                )

                adaptations.append(adaptation)

        return adaptations

    async def _generate_style_adaptations(
        self,
        agent_id: AgentId,
        patterns: List[FeedbackPattern],
    ) -> List[BehaviorAdaptation]:
        """Generate response style adaptations.

        Args:
            agent_id: Agent ID
            patterns: Feedback patterns

        Returns:
            List of response style adaptations
        """
        adaptations = []

        if not patterns:
            return adaptations

        # Create a prompt for generating style adaptations
        prompt = self._create_style_adaptation_prompt(patterns)

        # Generate style adaptations
        generator = await self._nlp_service.get_generator()
        generation_result = await generator.generate(prompt)

        # Parse the adaptations
        parsed_adaptations = self._parse_style_adaptations(agent_id, generation_result.text)

        adaptations.extend(parsed_adaptations)

        return adaptations

    def _create_style_adaptation_prompt(
        self,
        patterns: List[FeedbackPattern],
    ) -> str:
        """Create a prompt for generating style adaptations.

        Args:
            patterns: Feedback patterns

        Returns:
            Prompt for generating style adaptations
        """
        prompt = """You are an AI assistant tasked with generating response style adaptations based on feedback patterns.
I will provide you with a set of feedback patterns. Your task is to suggest adaptations to the agent's response style to improve its behavior.

Feedback patterns:
"""

        for i, pattern in enumerate(patterns):
            prompt += f"\n{i+1}. {pattern.description}\n"

            for before, after in pattern.examples:
                prompt += f"   Before: {before}\n"
                prompt += f"   After: {after}\n"

        prompt += """
Based on these patterns, suggest adaptations to the agent's response style. For each adaptation, provide:
1. A description of the adaptation
2. The before state (what the response style might look like now)
3. The after state (what the response style should look like after the adaptation)

Format your response as follows:
ADAPTATION 1:
Description: [Description of the adaptation]
Before: [Example of the response style before adaptation]
After: [Example of the response style after adaptation]

ADAPTATION 2:
...
"""

        return prompt

    def _parse_style_adaptations(
        self,
        agent_id: AgentId,
        adaptation_text: str,
    ) -> List[BehaviorAdaptation]:
        """Parse style adaptations from adaptation text.

        Args:
            agent_id: Agent ID
            adaptation_text: Adaptation text

        Returns:
            List of behavior adaptations
        """
        adaptations = []

        # Split the text into adaptation sections
        adaptation_sections = adaptation_text.split("ADAPTATION ")

        for section in adaptation_sections[1:]:  # Skip the first empty section
            try:
                # Extract adaptation information
                lines = section.strip().split("\n")

                # Extract description
                description_line = next((line for line in lines if line.startswith("Description:")), "")
                description = description_line.split(":", 1)[1].strip() if description_line else ""

                # Extract before and after states
                before_line_idx = next((i for i, line in enumerate(lines) if line.startswith("Before:")), -1)
                after_line_idx = next((i for i, line in enumerate(lines) if line.startswith("After:")), -1)

                if before_line_idx != -1 and after_line_idx != -1:
                    before_state = {"style": lines[before_line_idx].split(":", 1)[1].strip()}
                    after_state = {"style": lines[after_line_idx].split(":", 1)[1].strip()}

                    adaptation = BehaviorAdaptation(
                        id=AdaptationId(generate_id()),
                        agent_id=agent_id,
                        type=AdaptationType.RESPONSE_STYLE,
                        description=description,
                        creation_utc=datetime.now(timezone.utc),
                        applied=False,
                        confidence=0.7,
                        before_state=before_state,
                        after_state=after_state,
                    )

                    adaptations.append(adaptation)

            except Exception as e:
                self._logger.error(f"Error parsing style adaptation section: {e}")

        return adaptations

    async def save_adaptation(self, adaptation: BehaviorAdaptation) -> BehaviorAdaptation:
        """Save a behavior adaptation.

        Args:
            adaptation: Behavior adaptation to save

        Returns:
            Saved behavior adaptation
        """
        async with self._lock.writer_lock:
            await self._adaptation_collection.insert_one(
                document=self._serialize_adaptation(adaptation)
            )

        self._logger.info(f"Saved behavior adaptation: {adaptation.type} for agent {adaptation.agent_id}")

        return adaptation

    async def get_adaptation(self, adaptation_id: AdaptationId) -> Optional[BehaviorAdaptation]:
        """Get a behavior adaptation by ID.

        Args:
            adaptation_id: Adaptation ID

        Returns:
            Behavior adaptation if found, None otherwise
        """
        async with self._lock.reader_lock:
            document = await self._adaptation_collection.find_one(
                filters={"id": {"$eq": adaptation_id}}
            )

            if not document:
                return None

            return self._deserialize_adaptation(document)

    async def list_adaptations(
        self,
        agent_id: Optional[AgentId] = None,
        type: Optional[AdaptationType] = None,
        applied: Optional[bool] = None,
        min_confidence: float = 0.0,
        limit: int = 100,
        offset: int = 0,
    ) -> List[BehaviorAdaptation]:
        """List behavior adaptations with optional filtering.

        Args:
            agent_id: Filter by agent ID
            type: Filter by adaptation type
            applied: Filter by applied status
            min_confidence: Minimum confidence threshold
            limit: Maximum number of adaptations to return
            offset: Offset for pagination

        Returns:
            List of behavior adaptations
        """
        async with self._lock.reader_lock:
            filters = {}

            if agent_id:
                filters["agent_id"] = {"$eq": agent_id}

            if type:
                filters["type"] = {"$eq": type.value}

            if applied is not None:
                filters["applied"] = {"$eq": applied}

            if min_confidence > 0:
                filters["confidence"] = {"$gte": min_confidence}

            documents = await self._adaptation_collection.find(
                filters=filters,
                sort=[("creation_utc", -1)],
                limit=limit,
                skip=offset,
            )

            return [self._deserialize_adaptation(document) for document in documents]

    async def apply_adaptation(self, adaptation_id: AdaptationId) -> bool:
        """Apply a behavior adaptation.

        Args:
            adaptation_id: Adaptation ID

        Returns:
            True if the adaptation was applied, False otherwise
        """
        async with self._lock.writer_lock:
            # Get the adaptation
            adaptation = await self.get_adaptation(adaptation_id)
            if not adaptation:
                return False

            # Apply the adaptation based on its type
            if adaptation.type == AdaptationType.PROMPT_MODIFICATION:
                success = await self._apply_prompt_modification(adaptation)
            elif adaptation.type == AdaptationType.PARAMETER_ADJUSTMENT:
                success = await self._apply_parameter_adjustment(adaptation)
            elif adaptation.type == AdaptationType.RESPONSE_STYLE:
                success = await self._apply_response_style(adaptation)
            else:
                success = False

            if success:
                # Update the adaptation status
                await self._adaptation_collection.update_one(
                    filters={"id": {"$eq": adaptation_id}},
                    params={"applied": True},
                )

                self._logger.info(f"Applied behavior adaptation: {adaptation_id}")

            return success

    async def _apply_prompt_modification(self, adaptation: BehaviorAdaptation) -> bool:
        """Apply a prompt modification adaptation.

        Args:
            adaptation: Prompt modification adaptation

        Returns:
            True if the adaptation was applied, False otherwise
        """
        # TODO: Implement prompt modification
        # This would involve updating the agent's prompts in the prompt manager
        return True

    async def _apply_parameter_adjustment(self, adaptation: BehaviorAdaptation) -> bool:
        """Apply a parameter adjustment adaptation.

        Args:
            adaptation: Parameter adjustment adaptation

        Returns:
            True if the adaptation was applied, False otherwise
        """
        # TODO: Implement parameter adjustment
        # This would involve updating the agent's parameters
        return True

    async def _apply_response_style(self, adaptation: BehaviorAdaptation) -> bool:
        """Apply a response style adaptation.

        Args:
            adaptation: Response style adaptation

        Returns:
            True if the adaptation was applied, False otherwise
        """
        # TODO: Implement response style adaptation
        # This would involve updating the agent's response style guidelines
        return True