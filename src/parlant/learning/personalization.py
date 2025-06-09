"""
Personalization for Daneel.

This module provides functionality for personalizing agent responses based on user interactions.
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
from Daneel.core.customers import Customer, CustomerId, CustomerStore

from Daneel.learning.history import (
    InteractionHistoryTracker,
    Interaction,
    InteractionId,
    InteractionSessionId,
    InteractionType,
)


class PreferenceType(str, Enum):
    """Types of user preferences."""

    COMMUNICATION_STYLE = "communication_style"
    RESPONSE_LENGTH = "response_length"
    TECHNICAL_LEVEL = "technical_level"
    FORMALITY = "formality"
    TOPIC_INTEREST = "topic_interest"
    CUSTOM = "custom"


class PreferenceId(str):
    """Preference ID."""
    pass


@dataclass
class UserPreference:
    """User preference for personalization."""

    id: PreferenceId
    customer_id: CustomerId
    type: PreferenceType
    value: Any
    confidence: float
    creation_utc: datetime
    last_updated_utc: datetime
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class _PreferenceDocument(Dict[str, Any]):
    """Preference document for storage."""
    pass


class PersonalizationManager:
    """Manager for agent personalization."""

    VERSION = "0.1.0"

    def __init__(
        self,
        document_db: DocumentDatabase,
        agent_store: AgentStore,
        customer_store: CustomerStore,
        interaction_tracker: InteractionHistoryTracker,
        nlp_service: NLPService,
        logger: Logger,
    ):
        """Initialize the personalization manager.

        Args:
            document_db: Document database
            agent_store: Agent store
            customer_store: Customer store
            interaction_tracker: Interaction history tracker
            nlp_service: NLP service
            logger: Logger instance
        """
        self._document_db = document_db
        self._agent_store = agent_store
        self._customer_store = customer_store
        self._interaction_tracker = interaction_tracker
        self._nlp_service = nlp_service
        self._logger = logger

        self._preference_collection: Optional[DocumentCollection[_PreferenceDocument]] = None
        self._lock = ReaderWriterLock()

    async def __aenter__(self) -> PersonalizationManager:
        """Enter the context manager."""
        self._preference_collection = await self._document_db.get_or_create_collection(
            name="user_preferences",
            schema=_PreferenceDocument,
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        pass

    def _serialize_preference(self, preference: UserPreference) -> _PreferenceDocument:
        """Serialize a user preference.

        Args:
            preference: User preference to serialize

        Returns:
            Serialized preference document
        """
        return {
            "id": preference.id,
            "version": self.VERSION,
            "customer_id": preference.customer_id,
            "type": preference.type.value,
            "value": preference.value,
            "confidence": preference.confidence,
            "creation_utc": preference.creation_utc.isoformat(),
            "last_updated_utc": preference.last_updated_utc.isoformat(),
            "metadata": preference.metadata,
        }

    def _deserialize_preference(self, document: _PreferenceDocument) -> UserPreference:
        """Deserialize a preference document.

        Args:
            document: Preference document

        Returns:
            Deserialized user preference
        """
        return UserPreference(
            id=PreferenceId(document["id"]),
            customer_id=CustomerId(document["customer_id"]),
            type=PreferenceType(document["type"]),
            value=document["value"],
            confidence=document["confidence"],
            creation_utc=datetime.fromisoformat(document["creation_utc"]),
            last_updated_utc=datetime.fromisoformat(document["last_updated_utc"]),
            metadata=document.get("metadata", {}),
        )

    async def infer_preferences(
        self,
        customer_id: CustomerId,
        days: int = 30,
    ) -> List[UserPreference]:
        """Infer user preferences from interactions.

        Args:
            customer_id: Customer ID
            days: Number of days of interactions to analyze

        Returns:
            List of inferred user preferences
        """
        # Verify that the customer exists
        customer = await self._customer_store.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer not found: {customer_id}")

        self._logger.info(f"Inferring preferences for customer {customer_id}")

        # Get recent interactions
        start_time = datetime.now(timezone.utc) - timedelta(days=days)

        # TODO: Get interactions for the customer
        # For now, we'll create some example preferences

        preferences = []

        # Communication style preference
        communication_style = await self._infer_communication_style(customer_id)
        if communication_style:
            preferences.append(communication_style)

        # Response length preference
        response_length = await self._infer_response_length(customer_id)
        if response_length:
            preferences.append(response_length)

        # Technical level preference
        technical_level = await self._infer_technical_level(customer_id)
        if technical_level:
            preferences.append(technical_level)

        # Save the preferences
        for preference in preferences:
            await self.save_preference(preference)

        return preferences

    async def _infer_communication_style(
        self,
        customer_id: CustomerId,
    ) -> Optional[UserPreference]:
        """Infer communication style preference.

        Args:
            customer_id: Customer ID

        Returns:
            Communication style preference if inferred, None otherwise
        """
        # TODO: Implement communication style inference
        # For now, we'll create an example preference

        return UserPreference(
            id=PreferenceId(generate_id()),
            customer_id=customer_id,
            type=PreferenceType.COMMUNICATION_STYLE,
            value="friendly",
            confidence=0.8,
            creation_utc=datetime.now(timezone.utc),
            last_updated_utc=datetime.now(timezone.utc),
        )

    async def _infer_response_length(
        self,
        customer_id: CustomerId,
    ) -> Optional[UserPreference]:
        """Infer response length preference.

        Args:
            customer_id: Customer ID

        Returns:
            Response length preference if inferred, None otherwise
        """
        # TODO: Implement response length inference
        # For now, we'll create an example preference

        return UserPreference(
            id=PreferenceId(generate_id()),
            customer_id=customer_id,
            type=PreferenceType.RESPONSE_LENGTH,
            value="concise",
            confidence=0.7,
            creation_utc=datetime.now(timezone.utc),
            last_updated_utc=datetime.now(timezone.utc),
        )

    async def _infer_technical_level(
        self,
        customer_id: CustomerId,
    ) -> Optional[UserPreference]:
        """Infer technical level preference.

        Args:
            customer_id: Customer ID

        Returns:
            Technical level preference if inferred, None otherwise
        """
        # TODO: Implement technical level inference
        # For now, we'll create an example preference

        return UserPreference(
            id=PreferenceId(generate_id()),
            customer_id=customer_id,
            type=PreferenceType.TECHNICAL_LEVEL,
            value="intermediate",
            confidence=0.6,
            creation_utc=datetime.now(timezone.utc),
            last_updated_utc=datetime.now(timezone.utc),
        )

    async def save_preference(self, preference: UserPreference) -> UserPreference:
        """Save a user preference.

        Args:
            preference: User preference to save

        Returns:
            Saved user preference
        """
        async with self._lock.writer_lock:
            # Check if the preference already exists
            existing = await self._preference_collection.find_one(
                filters={
                    "customer_id": {"$eq": preference.customer_id},
                    "type": {"$eq": preference.type.value},
                }
            )

            if existing:
                # Update the existing preference
                preference.id = PreferenceId(existing["id"])
                preference.creation_utc = datetime.fromisoformat(existing["creation_utc"])

                await self._preference_collection.update_one(
                    filters={"id": {"$eq": preference.id}},
                    params={
                        "value": preference.value,
                        "confidence": preference.confidence,
                        "last_updated_utc": preference.last_updated_utc.isoformat(),
                        "metadata": preference.metadata,
                    },
                )
            else:
                # Insert a new preference
                await self._preference_collection.insert_one(
                    document=self._serialize_preference(preference)
                )

        self._logger.info(f"Saved preference: {preference.type} = {preference.value} for customer {preference.customer_id}")

        return preference

    async def get_preference(
        self,
        customer_id: CustomerId,
        type: PreferenceType,
    ) -> Optional[UserPreference]:
        """Get a user preference.

        Args:
            customer_id: Customer ID
            type: Preference type

        Returns:
            User preference if found, None otherwise
        """
        async with self._lock.reader_lock:
            document = await self._preference_collection.find_one(
                filters={
                    "customer_id": {"$eq": customer_id},
                    "type": {"$eq": type.value},
                }
            )

            if not document:
                return None

            return self._deserialize_preference(document)

    async def list_preferences(
        self,
        customer_id: CustomerId,
        min_confidence: float = 0.0,
    ) -> List[UserPreference]:
        """List user preferences.

        Args:
            customer_id: Customer ID
            min_confidence: Minimum confidence threshold

        Returns:
            List of user preferences
        """
        async with self._lock.reader_lock:
            filters = {"customer_id": {"$eq": customer_id}}

            if min_confidence > 0:
                filters["confidence"] = {"$gte": min_confidence}

            documents = await self._preference_collection.find(
                filters=filters,
                sort=[("type", 1)],
            )

            return [self._deserialize_preference(document) for document in documents]

    async def delete_preference(
        self,
        customer_id: CustomerId,
        type: PreferenceType,
    ) -> bool:
        """Delete a user preference.

        Args:
            customer_id: Customer ID
            type: Preference type

        Returns:
            True if the preference was deleted, False otherwise
        """
        async with self._lock.writer_lock:
            result = await self._preference_collection.delete_one(
                filters={
                    "customer_id": {"$eq": customer_id},
                    "type": {"$eq": type.value},
                }
            )

            if result.deleted_count == 0:
                return False

        self._logger.info(f"Deleted preference: {type} for customer {customer_id}")

        return True

    async def personalize_response(
        self,
        customer_id: CustomerId,
        text: str,
        min_confidence: float = 0.5,
    ) -> str:
        """Personalize a response based on user preferences.

        Args:
            customer_id: Customer ID
            text: Text to personalize
            min_confidence: Minimum confidence threshold for preferences

        Returns:
            Personalized text
        """
        # Get preferences for the customer
        preferences = await self.list_preferences(
            customer_id=customer_id,
            min_confidence=min_confidence,
        )

        if not preferences:
            return text

        # Create a prompt for personalization
        prompt = self._create_personalization_prompt(text, preferences)

        # Generate personalized text
        generator = await self._nlp_service.get_generator()
        generation_result = await generator.generate(prompt)

        # Extract the personalized text
        personalized_text = self._extract_personalized_text(generation_result.text)

        return personalized_text

    def _create_personalization_prompt(
        self,
        text: str,
        preferences: List[UserPreference],
    ) -> str:
        """Create a prompt for personalization.

        Args:
            text: Text to personalize
            preferences: User preferences

        Returns:
            Prompt for personalization
        """
        prompt = """You are an AI assistant tasked with personalizing a response based on user preferences.
I will provide you with a text and a set of user preferences. Your task is to rewrite the text to match these preferences.

Text to personalize:
"""

        prompt += f"\n{text}\n\nUser preferences:\n"

        # Add preferences
        for preference in preferences:
            prompt += f"\n- {preference.type.value}: {preference.value}\n"

        prompt += """
Rewrite the text to match these preferences. Maintain the same meaning and information, but adapt the style, length, and technical level according to the preferences.

Personalized text:
"""

        return prompt

    def _extract_personalized_text(self, response_text: str) -> str:
        """Extract personalized text from response.

        Args:
            response_text: Response text

        Returns:
            Extracted personalized text
        """
        # Look for the personalized text after "Personalized text:" or similar markers
        markers = ["Personalized text:", "Here's the personalized text:", "Personalized version:"]

        for marker in markers:
            if marker in response_text:
                personalized_text = response_text.split(marker, 1)[1].strip()
                return personalized_text

        # If no marker is found, return the whole response
        return response_text.strip()

    async def create_personalized_prompt(
        self,
        customer_id: CustomerId,
        prompt_template: str,
        min_confidence: float = 0.5,
    ) -> str:
        """Create a personalized prompt based on user preferences.

        Args:
            customer_id: Customer ID
            prompt_template: Prompt template
            min_confidence: Minimum confidence threshold for preferences

        Returns:
            Personalized prompt
        """
        # Get preferences for the customer
        preferences = await self.list_preferences(
            customer_id=customer_id,
            min_confidence=min_confidence,
        )

        if not preferences:
            return prompt_template

        # Add personalization instructions to the prompt
        personalized_prompt = prompt_template + "\n\nUser preferences:\n"

        for preference in preferences:
            personalized_prompt += f"- {preference.type.value}: {preference.value}\n"

        personalized_prompt += "\nPlease adapt your response to match these preferences."

        return personalized_prompt
