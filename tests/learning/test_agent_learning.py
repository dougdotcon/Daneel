"""
Tests for the agent learning and adaptation functionality.
"""

import os
import pytest
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, AsyncMock

from parlant.core.loggers import ConsoleLogger
from parlant.core.agents import Agent, AgentId, AgentStore
from parlant.core.models import Model, ModelManager
from parlant.core.prompts import Prompt, PromptManager
from parlant.core.tools import ToolRegistry
from parlant.core.nlp.service import NLPService
from parlant.core.nlp.generation_info import GenerationInfo
from parlant.core.persistence.document_database import DocumentDatabase, DocumentCollection
from parlant.core.customers import Customer, CustomerId, CustomerStore

from parlant.learning import (
    InteractionHistoryTracker,
    Interaction,
    InteractionId,
    InteractionSessionId,
    InteractionType,
    FeedbackType,
    Feedback,
    PerformanceMetricsTracker,
    MetricType,
    MetricId,
    MetricValue,
    EvaluationId,
    Evaluation,
    FeedbackLearner,
    FeedbackPattern,
    FeedbackPatternId,
    LearningStrategy,
    BehaviorAdapter,
    BehaviorAdaptation,
    AdaptationId,
    AdaptationType,
    PersonalizationManager,
    UserPreference,
    PreferenceId,
    PreferenceType,
)


class MockAgent(Agent):
    """Mock agent for testing."""

    def __init__(self, agent_id: str, name: str):
        """Initialize the mock agent."""
        self.id = AgentId(agent_id)
        self.name = name
        self.description = f"Mock agent {name}"
        self.creation_utc = datetime.now(timezone.utc)
        self.max_engine_iterations = 1
        self.tags = []


class MockAgentStore(AgentStore):
    """Mock agent store for testing."""

    def __init__(self):
        """Initialize the mock agent store."""
        self.agents = {}

    async def get_agent(self, agent_id: AgentId) -> Optional[Agent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    async def create_agent(
        self,
        name: str,
        description: Optional[str] = None,
        creation_utc: Optional[datetime] = None,
        max_engine_iterations: Optional[int] = None,
        composition_mode: Optional[Any] = None,
        tags: Optional[List[Any]] = None,
    ) -> Agent:
        """Create an agent."""
        agent_id = AgentId(f"agent_{len(self.agents) + 1}")
        agent = MockAgent(agent_id, name)
        self.agents[agent_id] = agent
        return agent

    async def update_agent(self, agent_id: AgentId, params: Dict[str, Any]) -> Optional[Agent]:
        """Update an agent."""
        if agent_id not in self.agents:
            return None
        return self.agents[agent_id]

    async def delete_agent(self, agent_id: AgentId) -> bool:
        """Delete an agent."""
        if agent_id not in self.agents:
            return False
        del self.agents[agent_id]
        return True

    async def list_agents(self) -> List[Agent]:
        """List all agents."""
        return list(self.agents.values())


class MockCustomer(Customer):
    """Mock customer for testing."""

    def __init__(self, customer_id: str, name: str):
        """Initialize the mock customer."""
        self.id = CustomerId(customer_id)
        self.name = name
        self.creation_utc = datetime.now(timezone.utc)


class MockCustomerStore(CustomerStore):
    """Mock customer store for testing."""

    def __init__(self):
        """Initialize the mock customer store."""
        self.customers = {}

    async def get_customer(self, customer_id: CustomerId) -> Optional[Customer]:
        """Get a customer by ID."""
        return self.customers.get(customer_id)

    async def create_customer(
        self,
        name: str,
        creation_utc: Optional[datetime] = None,
    ) -> Customer:
        """Create a customer."""
        customer_id = CustomerId(f"customer_{len(self.customers) + 1}")
        customer = MockCustomer(customer_id, name)
        self.customers[customer_id] = customer
        return customer


class MockDocumentCollection(DocumentCollection):
    """Mock document collection for testing."""

    def __init__(self):
        """Initialize the mock document collection."""
        self.documents = []

    async def insert_one(self, document: Dict[str, Any]) -> Any:
        """Insert a document."""
        self.documents.append(document)
        return MagicMock()

    async def find_one(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a document."""
        for document in self.documents:
            match = True
            for key, value in filters.items():
                if key not in document:
                    match = False
                    break

                if isinstance(value, dict) and "$eq" in value:
                    if document[key] != value["$eq"]:
                        match = False
                        break
                elif document[key] != value:
                    match = False
                    break

            if match:
                return document

        return None

    async def find(
        self,
        filters: Dict[str, Any],
        sort: Optional[List[Tuple[str, int]]] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Find documents."""
        results = []

        for document in self.documents:
            match = True
            for key, value in filters.items():
                if key not in document:
                    match = False
                    break

                if isinstance(value, dict) and "$eq" in value:
                    if document[key] != value["$eq"]:
                        match = False
                        break
                elif document[key] != value:
                    match = False
                    break

            if match:
                results.append(document)

        if sort:
            for field, direction in reversed(sort):
                results.sort(key=lambda x: x.get(field, ""), reverse=direction == -1)

        if skip:
            results = results[skip:]

        if limit:
            results = results[:limit]

        return results

    async def update_one(
        self,
        filters: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Any:
        """Update a document."""
        document = await self.find_one(filters)
        if document:
            for key, value in params.items():
                document[key] = value

        return MagicMock(modified_count=1 if document else 0)

    async def delete_one(self, filters: Dict[str, Any]) -> Any:
        """Delete a document."""
        document = await self.find_one(filters)
        if document:
            self.documents.remove(document)
            return MagicMock(deleted_count=1)

        return MagicMock(deleted_count=0)


class MockDocumentDatabase(DocumentDatabase):
    """Mock document database for testing."""

    def __init__(self):
        """Initialize the mock document database."""
        self.collections = {}

    async def get_or_create_collection(
        self,
        name: str,
        schema: Any,
    ) -> DocumentCollection:
        """Get or create a collection."""
        if name not in self.collections:
            self.collections[name] = MockDocumentCollection()

        return self.collections[name]


class MockNLPService(NLPService):
    """Mock NLP service for testing."""

    async def get_generator(self) -> Any:
        """Get a generator."""
        generator = MagicMock()
        generator.generate = AsyncMock(return_value=GenerationInfo(
            text="This is a mock response",
            usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        ))
        return generator


@pytest.fixture
def logger():
    return ConsoleLogger()


@pytest.fixture
def agent_store():
    store = MockAgentStore()
    return store


@pytest.fixture
def customer_store():
    store = MockCustomerStore()
    return store


@pytest.fixture
def document_db():
    return MockDocumentDatabase()


@pytest.fixture
def nlp_service():
    return MockNLPService()


@pytest.fixture
async def interaction_tracker(document_db, agent_store, logger):
    tracker = InteractionHistoryTracker(
        document_db=document_db,
        agent_store=agent_store,
        logger=logger,
    )
    async with tracker:
        yield tracker


@pytest.fixture
async def metrics_tracker(document_db, agent_store, interaction_tracker, logger):
    tracker = PerformanceMetricsTracker(
        document_db=document_db,
        agent_store=agent_store,
        interaction_tracker=interaction_tracker,
        logger=logger,
    )
    async with tracker:
        yield tracker


@pytest.fixture
async def feedback_learner(document_db, agent_store, interaction_tracker, nlp_service, logger):
    learner = FeedbackLearner(
        document_db=document_db,
        agent_store=agent_store,
        interaction_tracker=interaction_tracker,
        nlp_service=nlp_service,
        logger=logger,
    )
    async with learner:
        yield learner


@pytest.fixture
async def behavior_adapter(
    document_db,
    agent_store,
    interaction_tracker,
    metrics_tracker,
    feedback_learner,
    nlp_service,
    logger,
):
    prompt_manager = MagicMock()
    adapter = BehaviorAdapter(
        document_db=document_db,
        agent_store=agent_store,
        interaction_tracker=interaction_tracker,
        metrics_tracker=metrics_tracker,
        feedback_learner=feedback_learner,
        prompt_manager=prompt_manager,
        nlp_service=nlp_service,
        logger=logger,
    )
    async with adapter:
        yield adapter


@pytest.fixture
async def personalization_manager(
    document_db,
    agent_store,
    customer_store,
    interaction_tracker,
    nlp_service,
    logger,
):
    manager = PersonalizationManager(
        document_db=document_db,
        agent_store=agent_store,
        customer_store=customer_store,
        interaction_tracker=interaction_tracker,
        nlp_service=nlp_service,
        logger=logger,
    )
    async with manager:
        yield manager


async def test_interaction_tracking(interaction_tracker, agent_store):
    """Test that interactions can be tracked."""
    # Create an agent
    agent = await agent_store.create_agent(name="Test Agent")

    # Track an interaction
    session_id = InteractionSessionId("test_session")
    interaction = await interaction_tracker.track_interaction(
        session_id=session_id,
        agent_id=agent.id,
        type=InteractionType.AGENT_MESSAGE,
        content="Hello, world!",
    )

    # Check that the interaction was created
    assert interaction is not None
    assert interaction.id is not None
    assert interaction.session_id == session_id
    assert interaction.agent_id == agent.id
    assert interaction.type == InteractionType.AGENT_MESSAGE
    assert interaction.content == "Hello, world!"

    # Get the interaction
    retrieved = await interaction_tracker.get_interaction(interaction.id)

    # Check that the interaction was retrieved
    assert retrieved is not None
    assert retrieved.id == interaction.id
    assert retrieved.session_id == session_id
    assert retrieved.agent_id == agent.id
    assert retrieved.type == InteractionType.AGENT_MESSAGE
    assert retrieved.content == "Hello, world!"

    # Add feedback to the interaction
    updated = await interaction_tracker.add_feedback(
        interaction_id=interaction.id,
        feedback_type=FeedbackType.THUMBS_UP,
        value=True,
        source="user",
    )

    # Check that the feedback was added
    assert updated is not None
    assert len(updated.feedback) == 1
    assert updated.feedback[0].type == FeedbackType.THUMBS_UP
    assert updated.feedback[0].value is True
    assert updated.feedback[0].source == "user"

    # List interactions for the session
    interactions = await interaction_tracker.get_session_interactions(session_id)

    # Check that the interaction is in the list
    assert len(interactions) == 1
    assert interactions[0].id == interaction.id


async def test_performance_metrics(metrics_tracker, agent_store):
    """Test that performance metrics can be tracked."""
    # Create an agent
    agent = await agent_store.create_agent(name="Test Agent")

    # Track a metric
    metric = await metrics_tracker.track_metric(
        agent_id=agent.id,
        type=MetricType.RESPONSE_TIME,
        value=1.5,
    )

    # Check that the metric was created
    assert metric is not None
    assert metric.id is not None
    assert metric.agent_id == agent.id
    assert metric.type == MetricType.RESPONSE_TIME
    assert metric.value == 1.5

    # Get the metric
    retrieved = await metrics_tracker.get_metric(metric.id)

    # Check that the metric was retrieved
    assert retrieved is not None
    assert retrieved.id == metric.id
    assert retrieved.agent_id == agent.id
    assert retrieved.type == MetricType.RESPONSE_TIME
    assert retrieved.value == 1.5

    # Track another metric
    await metrics_tracker.track_metric(
        agent_id=agent.id,
        type=MetricType.RESPONSE_TIME,
        value=2.0,
    )

    # Get metric stats
    stats = await metrics_tracker.get_metric_stats(
        agent_id=agent.id,
        type=MetricType.RESPONSE_TIME,
    )

    # Check the stats
    assert stats is not None
    assert stats["count"] == 2
    assert stats["min"] == 1.5
    assert stats["max"] == 2.0
    assert stats["mean"] == 1.75

    # Create an evaluation
    evaluation = await metrics_tracker.create_evaluation(
        agent_id=agent.id,
        metrics=[metric],
        summary="Test evaluation",
        score=0.8,
    )

    # Check that the evaluation was created
    assert evaluation is not None
    assert evaluation.id is not None
    assert evaluation.agent_id == agent.id
    assert len(evaluation.metrics) == 1
    assert evaluation.metrics[0].id == metric.id
    assert evaluation.summary == "Test evaluation"
    assert evaluation.score == 0.8

    # Get the evaluation
    retrieved = await metrics_tracker.get_evaluation(evaluation.id)

    # Check that the evaluation was retrieved
    assert retrieved is not None
    assert retrieved.id == evaluation.id
    assert retrieved.agent_id == agent.id
    assert len(retrieved.metrics) == 1
    assert retrieved.metrics[0].id == metric.id
    assert retrieved.summary == "Test evaluation"
    assert retrieved.score == 0.8


async def test_feedback_learning(feedback_learner, agent_store, interaction_tracker):
    """Test that feedback patterns can be learned."""
    # Create an agent
    agent = await agent_store.create_agent(name="Test Agent")

    # Create a feedback pattern
    pattern = FeedbackPattern(
        id=FeedbackPatternId("test_pattern"),
        agent_id=agent.id,
        pattern_type="test",
        description="Test pattern",
        examples=[("Hello", "Hello, world!")],
        creation_utc=datetime.now(timezone.utc),
        confidence=0.8,
    )

    # Save the pattern
    saved = await feedback_learner.save_pattern(pattern)

    # Check that the pattern was saved
    assert saved is not None
    assert saved.id == pattern.id
    assert saved.agent_id == agent.id
    assert saved.pattern_type == "test"
    assert saved.description == "Test pattern"
    assert len(saved.examples) == 1
    assert saved.examples[0] == ("Hello", "Hello, world!")
    assert saved.confidence == 0.8

    # Get the pattern
    retrieved = await feedback_learner.get_pattern(pattern.id)

    # Check that the pattern was retrieved
    assert retrieved is not None
    assert retrieved.id == pattern.id
    assert retrieved.agent_id == agent.id
    assert retrieved.pattern_type == "test"
    assert retrieved.description == "Test pattern"
    assert len(retrieved.examples) == 1
    assert retrieved.examples[0] == ("Hello", "Hello, world!")
    assert retrieved.confidence == 0.8

    # Apply patterns to text
    improved = await feedback_learner.apply_patterns(
        agent_id=agent.id,
        text="Hello",
    )

    # Check that the text was improved
    assert improved is not None
    assert improved != "Hello"


async def test_behavior_adaptation(behavior_adapter, agent_store, metrics_tracker):
    """Test that behavior adaptations can be generated."""
    # Create an agent
    agent = await agent_store.create_agent(name="Test Agent")

    # Track some metrics
    await metrics_tracker.track_metric(
        agent_id=agent.id,
        type=MetricType.RESPONSE_TIME,
        value=6.0,  # High response time
    )

    # Generate adaptations
    adaptations = await behavior_adapter.generate_adaptations(agent_id=agent.id)

    # Check that adaptations were generated
    assert adaptations is not None
    assert len(adaptations) > 0

    # Get an adaptation
    adaptation = adaptations[0]

    # Check the adaptation
    assert adaptation is not None
    assert adaptation.id is not None
    assert adaptation.agent_id == agent.id
    assert adaptation.type is not None
    assert adaptation.description is not None
    assert adaptation.applied is False

    # Apply the adaptation
    success = await behavior_adapter.apply_adaptation(adaptation.id)

    # Check that the adaptation was applied
    assert success is True

    # Get the adaptation again
    retrieved = await behavior_adapter.get_adaptation(adaptation.id)

    # Check that the adaptation was updated
    assert retrieved is not None
    assert retrieved.id == adaptation.id
    assert retrieved.applied is True


async def test_personalization(personalization_manager, customer_store):
    """Test that responses can be personalized."""
    # Create a customer
    customer = await customer_store.create_customer(name="Test Customer")

    # Infer preferences
    preferences = await personalization_manager.infer_preferences(customer.id)

    # Check that preferences were inferred
    assert preferences is not None
    assert len(preferences) > 0

    # Get a preference
    preference = preferences[0]

    # Check the preference
    assert preference is not None
    assert preference.id is not None
    assert preference.customer_id == customer.id
    assert preference.type is not None
    assert preference.value is not None
    assert preference.confidence > 0

    # Get the preference by type
    retrieved = await personalization_manager.get_preference(
        customer_id=customer.id,
        type=preference.type,
    )

    # Check that the preference was retrieved
    assert retrieved is not None
    assert retrieved.id == preference.id
    assert retrieved.customer_id == customer.id
    assert retrieved.type == preference.type
    assert retrieved.value == preference.value

    # Personalize a response
    personalized = await personalization_manager.personalize_response(
        customer_id=customer.id,
        text="Hello, world!",
    )

    # Check that the response was personalized
    assert personalized is not None
    assert personalized != "Hello, world!"

    # Create a personalized prompt
    personalized_prompt = await personalization_manager.create_personalized_prompt(
        customer_id=customer.id,
        prompt_template="You are an AI assistant.",
    )

    # Check that the prompt was personalized
    assert personalized_prompt is not None
    assert personalized_prompt != "You are an AI assistant."
    assert "User preferences" in personalized_prompt
