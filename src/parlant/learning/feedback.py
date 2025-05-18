"""
Feedback-based learning for Parlant.

This module provides functionality for improving agent responses based on user feedback.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid
import json
import asyncio

from parlant.core.common import JSONSerializable, generate_id
from parlant.core.agents import Agent, AgentId, AgentStore
from parlant.core.loggers import Logger
from parlant.core.async_utils import ReaderWriterLock
from parlant.core.persistence.document_database import DocumentCollection, DocumentDatabase
from parlant.core.persistence.common import ItemNotFoundError, ObjectId, UniqueId, Where
from parlant.core.nlp.service import NLPService
from parlant.core.nlp.generation_info import GenerationInfo

from parlant.learning.history import (
    InteractionHistoryTracker,
    Interaction,
    InteractionId,
    InteractionSessionId,
    InteractionType,
    FeedbackType,
    Feedback,
)


class LearningStrategy(str, Enum):
    """Strategies for feedback-based learning."""

    EXAMPLE_BASED = "example_based"
    RULE_BASED = "rule_based"
    MODEL_BASED = "model_based"
    HYBRID = "hybrid"


class FeedbackPatternId(str):
    """Feedback pattern ID."""
    pass


@dataclass
class FeedbackPattern:
    """Pattern identified from feedback."""

    id: FeedbackPatternId
    agent_id: AgentId
    pattern_type: str
    description: str
    examples: List[Tuple[str, str]]  # (before, after) pairs
    creation_utc: datetime
    confidence: float
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class _FeedbackPatternDocument(Dict[str, Any]):
    """Feedback pattern document for storage."""
    pass


class FeedbackLearner:
    """Learner for feedback-based improvement."""

    VERSION = "0.1.0"

    def __init__(
        self,
        document_db: DocumentDatabase,
        agent_store: AgentStore,
        interaction_tracker: InteractionHistoryTracker,
        nlp_service: NLPService,
        logger: Logger,
        strategy: LearningStrategy = LearningStrategy.HYBRID,
    ):
        """Initialize the feedback learner.

        Args:
            document_db: Document database
            agent_store: Agent store
            interaction_tracker: Interaction history tracker
            nlp_service: NLP service
            logger: Logger instance
            strategy: Learning strategy
        """
        self._document_db = document_db
        self._agent_store = agent_store
        self._interaction_tracker = interaction_tracker
        self._nlp_service = nlp_service
        self._logger = logger
        self._strategy = strategy

        self._pattern_collection: Optional[DocumentCollection[_FeedbackPatternDocument]] = None
        self._lock = ReaderWriterLock()

    async def __aenter__(self) -> FeedbackLearner:
        """Enter the context manager."""
        self._pattern_collection = await self._document_db.get_or_create_collection(
            name="feedback_patterns",
            schema=_FeedbackPatternDocument,
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        pass

    def _serialize_pattern(self, pattern: FeedbackPattern) -> _FeedbackPatternDocument:
        """Serialize a feedback pattern.

        Args:
            pattern: Feedback pattern to serialize

        Returns:
            Serialized pattern document
        """
        return {
            "id": pattern.id,
            "version": self.VERSION,
            "agent_id": pattern.agent_id,
            "pattern_type": pattern.pattern_type,
            "description": pattern.description,
            "examples": [{"before": before, "after": after} for before, after in pattern.examples],
            "creation_utc": pattern.creation_utc.isoformat(),
            "confidence": pattern.confidence,
            "metadata": pattern.metadata,
        }

    def _deserialize_pattern(self, document: _FeedbackPatternDocument) -> FeedbackPattern:
        """Deserialize a feedback pattern document.

        Args:
            document: Feedback pattern document

        Returns:
            Deserialized feedback pattern
        """
        return FeedbackPattern(
            id=FeedbackPatternId(document["id"]),
            agent_id=AgentId(document["agent_id"]),
            pattern_type=document["pattern_type"],
            description=document["description"],
            examples=[(example["before"], example["after"]) for example in document["examples"]],
            creation_utc=datetime.fromisoformat(document["creation_utc"]),
            confidence=document["confidence"],
            metadata=document.get("metadata", {}),
        )

    async def learn_from_feedback(
        self,
        agent_id: AgentId,
        days: int = 30,
    ) -> List[FeedbackPattern]:
        """Learn patterns from recent feedback.

        Args:
            agent_id: Agent ID
            days: Number of days of feedback to analyze

        Returns:
            List of identified feedback patterns
        """
        # Verify that the agent exists
        agent = await self._agent_store.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        # Get recent interactions with feedback
        start_time = datetime.now(timezone.utc) - timedelta(days=days)
        interactions = await self._interaction_tracker.list_interactions(
            agent_id=agent_id,
            start_time=start_time,
            limit=1000,
        )

        # Filter interactions with feedback
        interactions_with_feedback = [
            interaction for interaction in interactions
            if interaction.feedback
        ]

        if not interactions_with_feedback:
            self._logger.info(f"No feedback found for agent {agent_id} in the last {days} days")
            return []

        self._logger.info(f"Analyzing {len(interactions_with_feedback)} interactions with feedback for agent {agent_id}")

        # Learn patterns based on the selected strategy
        if self._strategy == LearningStrategy.EXAMPLE_BASED:
            patterns = await self._learn_example_based(agent_id, interactions_with_feedback)
        elif self._strategy == LearningStrategy.RULE_BASED:
            patterns = await self._learn_rule_based(agent_id, interactions_with_feedback)
        elif self._strategy == LearningStrategy.MODEL_BASED:
            patterns = await self._learn_model_based(agent_id, interactions_with_feedback)
        else:  # HYBRID
            patterns = await self._learn_hybrid(agent_id, interactions_with_feedback)

        # Save the patterns
        for pattern in patterns:
            await self.save_pattern(pattern)

        return patterns

    async def _learn_example_based(
        self,
        agent_id: AgentId,
        interactions: List[Interaction],
    ) -> List[FeedbackPattern]:
        """Learn patterns using example-based approach.

        Args:
            agent_id: Agent ID
            interactions: Interactions with feedback

        Returns:
            List of identified feedback patterns
        """
        patterns = []

        # Group interactions by feedback type
        correction_interactions = []

        for interaction in interactions:
            for feedback in interaction.feedback:
                if feedback.type == FeedbackType.CORRECTION:
                    correction_interactions.append((interaction, feedback))

        # Process correction feedback
        if correction_interactions:
            examples = []

            for interaction, feedback in correction_interactions:
                if interaction.type == InteractionType.AGENT_MESSAGE:
                    # Get the original response and the correction
                    original = interaction.content
                    correction = str(feedback.value)

                    examples.append((original, correction))

            if examples:
                pattern = FeedbackPattern(
                    id=FeedbackPatternId(generate_id()),
                    agent_id=agent_id,
                    pattern_type="correction",
                    description="Corrections to agent responses",
                    examples=examples,
                    creation_utc=datetime.now(timezone.utc),
                    confidence=0.8,
                )

                patterns.append(pattern)

        return patterns

    async def _learn_rule_based(
        self,
        agent_id: AgentId,
        interactions: List[Interaction],
    ) -> List[FeedbackPattern]:
        """Learn patterns using rule-based approach.

        Args:
            agent_id: Agent ID
            interactions: Interactions with feedback

        Returns:
            List of identified feedback patterns
        """
        # TODO: Implement rule-based learning
        return []

    async def _learn_model_based(
        self,
        agent_id: AgentId,
        interactions: List[Interaction],
    ) -> List[FeedbackPattern]:
        """Learn patterns using model-based approach.

        Args:
            agent_id: Agent ID
            interactions: Interactions with feedback

        Returns:
            List of identified feedback patterns
        """
        patterns = []

        # Group interactions by feedback type
        positive_interactions = []
        negative_interactions = []

        for interaction in interactions:
            for feedback in interaction.feedback:
                if feedback.type == FeedbackType.THUMBS_UP:
                    positive_interactions.append(interaction)
                elif feedback.type == FeedbackType.THUMBS_DOWN:
                    negative_interactions.append(interaction)

        # Use NLP to analyze patterns in positive and negative feedback
        if positive_interactions and negative_interactions:
            # Generate a prompt for pattern analysis
            prompt = self._create_pattern_analysis_prompt(positive_interactions, negative_interactions)

            # Generate pattern analysis
            generator = await self._nlp_service.get_generator()
            generation_result = await generator.generate(prompt)

            # Parse the patterns from the generation result
            parsed_patterns = self._parse_pattern_analysis(agent_id, generation_result.text)

            patterns.extend(parsed_patterns)

        return patterns

    async def _learn_hybrid(
        self,
        agent_id: AgentId,
        interactions: List[Interaction],
    ) -> List[FeedbackPattern]:
        """Learn patterns using hybrid approach.

        Args:
            agent_id: Agent ID
            interactions: Interactions with feedback

        Returns:
            List of identified feedback patterns
        """
        # Combine patterns from different approaches
        example_patterns = await self._learn_example_based(agent_id, interactions)
        model_patterns = await self._learn_model_based(agent_id, interactions)

        return example_patterns + model_patterns

    def _create_pattern_analysis_prompt(
        self,
        positive_interactions: List[Interaction],
        negative_interactions: List[Interaction],
    ) -> str:
        """Create a prompt for pattern analysis.

        Args:
            positive_interactions: Interactions with positive feedback
            negative_interactions: Interactions with negative feedback

        Returns:
            Prompt for pattern analysis
        """
        prompt = """You are an AI assistant tasked with analyzing patterns in user feedback for an agent.
I will provide you with examples of agent responses that received positive feedback and examples that received negative feedback.
Your task is to identify patterns and suggest improvements based on the feedback.

Positive examples:
"""

        # Add positive examples
        for i, interaction in enumerate(positive_interactions[:5]):
            prompt += f"\n{i+1}. {interaction.content}\n"

        prompt += "\nNegative examples:\n"

        # Add negative examples
        for i, interaction in enumerate(negative_interactions[:5]):
            prompt += f"\n{i+1}. {interaction.content}\n"

        prompt += """
Based on these examples, identify patterns that distinguish positive from negative responses.
For each pattern, provide:
1. A description of the pattern
2. Examples of how to improve responses based on this pattern

Format your response as follows:
PATTERN 1:
Description: [Description of the pattern]
Improvement: [How to improve responses based on this pattern]
Example Before: [Example of a response before improvement]
Example After: [Example of the response after improvement]

PATTERN 2:
...
"""

        return prompt

    def _parse_pattern_analysis(
        self,
        agent_id: AgentId,
        analysis_text: str,
    ) -> List[FeedbackPattern]:
        """Parse patterns from pattern analysis text.

        Args:
            agent_id: Agent ID
            analysis_text: Pattern analysis text

        Returns:
            List of feedback patterns
        """
        patterns = []

        # Split the text into pattern sections
        pattern_sections = analysis_text.split("PATTERN ")

        for section in pattern_sections[1:]:  # Skip the first empty section
            try:
                # Extract pattern information
                lines = section.strip().split("\n")

                # Extract pattern number and description
                pattern_type = f"model_pattern_{lines[0].split(':')[0].strip()}"

                description_line = next((line for line in lines if line.startswith("Description:")), "")
                description = description_line.split(":", 1)[1].strip() if description_line else ""

                # Extract examples
                examples = []

                before_line_idx = next((i for i, line in enumerate(lines) if line.startswith("Example Before:")), -1)
                after_line_idx = next((i for i, line in enumerate(lines) if line.startswith("Example After:")), -1)

                if before_line_idx != -1 and after_line_idx != -1:
                    before = lines[before_line_idx].split(":", 1)[1].strip()
                    after = lines[after_line_idx].split(":", 1)[1].strip()

                    examples.append((before, after))

                if description and examples:
                    pattern = FeedbackPattern(
                        id=FeedbackPatternId(generate_id()),
                        agent_id=agent_id,
                        pattern_type=pattern_type,
                        description=description,
                        examples=examples,
                        creation_utc=datetime.now(timezone.utc),
                        confidence=0.7,
                    )

                    patterns.append(pattern)

            except Exception as e:
                self._logger.error(f"Error parsing pattern section: {e}")

        return patterns

    async def save_pattern(self, pattern: FeedbackPattern) -> FeedbackPattern:
        """Save a feedback pattern.

        Args:
            pattern: Feedback pattern to save

        Returns:
            Saved feedback pattern
        """
        async with self._lock.writer_lock:
            await self._pattern_collection.insert_one(
                document=self._serialize_pattern(pattern)
            )

        self._logger.info(f"Saved feedback pattern: {pattern.pattern_type} for agent {pattern.agent_id}")

        return pattern

    async def get_pattern(self, pattern_id: FeedbackPatternId) -> Optional[FeedbackPattern]:
        """Get a feedback pattern by ID.

        Args:
            pattern_id: Pattern ID

        Returns:
            Feedback pattern if found, None otherwise
        """
        async with self._lock.reader_lock:
            document = await self._pattern_collection.find_one(
                filters={"id": {"$eq": pattern_id}}
            )

            if not document:
                return None

            return self._deserialize_pattern(document)

    async def list_patterns(
        self,
        agent_id: Optional[AgentId] = None,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 100,
        offset: int = 0,
    ) -> List[FeedbackPattern]:
        """List feedback patterns with optional filtering.

        Args:
            agent_id: Filter by agent ID
            pattern_type: Filter by pattern type
            min_confidence: Minimum confidence threshold
            limit: Maximum number of patterns to return
            offset: Offset for pagination

        Returns:
            List of feedback patterns
        """
        async with self._lock.reader_lock:
            filters = {}

            if agent_id:
                filters["agent_id"] = {"$eq": agent_id}

            if pattern_type:
                filters["pattern_type"] = {"$eq": pattern_type}

            if min_confidence > 0:
                filters["confidence"] = {"$gte": min_confidence}

            documents = await self._pattern_collection.find(
                filters=filters,
                sort=[("confidence", -1)],
                limit=limit,
                skip=offset,
            )

            return [self._deserialize_pattern(document) for document in documents]

    async def delete_pattern(self, pattern_id: FeedbackPatternId) -> bool:
        """Delete a feedback pattern.

        Args:
            pattern_id: Pattern ID

        Returns:
            True if the pattern was deleted, False otherwise
        """
        async with self._lock.writer_lock:
            result = await self._pattern_collection.delete_one(
                filters={"id": {"$eq": pattern_id}}
            )

            if result.deleted_count == 0:
                return False

        self._logger.info(f"Deleted feedback pattern: {pattern_id}")

        return True

    async def apply_patterns(
        self,
        agent_id: AgentId,
        text: str,
        min_confidence: float = 0.7,
    ) -> str:
        """Apply feedback patterns to improve text.

        Args:
            agent_id: Agent ID
            text: Text to improve
            min_confidence: Minimum confidence threshold for patterns

        Returns:
            Improved text
        """
        # Get patterns for the agent
        patterns = await self.list_patterns(
            agent_id=agent_id,
            min_confidence=min_confidence,
        )

        if not patterns:
            return text

        # Apply patterns to the text
        improved_text = text

        for pattern in patterns:
            # Apply example-based improvements
            for before, after in pattern.examples:
                if before in improved_text:
                    improved_text = improved_text.replace(before, after)

        # If no direct replacements were made, use NLP to apply patterns
        if improved_text == text and patterns:
            # Generate a prompt for applying patterns
            prompt = self._create_pattern_application_prompt(text, patterns)

            # Generate improved text
            generator = await self._nlp_service.get_generator()
            generation_result = await generator.generate(prompt)

            # Extract the improved text
            improved_text = self._extract_improved_text(generation_result.text)

        return improved_text

    def _create_pattern_application_prompt(
        self,
        text: str,
        patterns: List[FeedbackPattern],
    ) -> str:
        """Create a prompt for applying patterns.

        Args:
            text: Text to improve
            patterns: Feedback patterns to apply

        Returns:
            Prompt for pattern application
        """
        prompt = """You are an AI assistant tasked with improving a text based on feedback patterns.
I will provide you with a text and a set of patterns to apply. Your task is to improve the text by applying these patterns.

Text to improve:
"""

        prompt += f"\n{text}\n\nPatterns to apply:\n"

        # Add patterns
        for i, pattern in enumerate(patterns):
            prompt += f"\n{i+1}. {pattern.description}\n"

            for before, after in pattern.examples:
                prompt += f"   Before: {before}\n"
                prompt += f"   After: {after}\n"

        prompt += """
Apply these patterns to improve the text. Maintain the same meaning and information, but make the text better according to the patterns.

Improved text:
"""

        return prompt

    def _extract_improved_text(self, response_text: str) -> str:
        """Extract improved text from response.

        Args:
            response_text: Response text

        Returns:
            Extracted improved text
        """
        # Look for the improved text after "Improved text:" or similar markers
        markers = ["Improved text:", "Here's the improved text:", "Improved version:"]

        for marker in markers:
            if marker in response_text:
                improved_text = response_text.split(marker, 1)[1].strip()
                return improved_text

        # If no marker is found, return the whole response
        return response_text.strip()