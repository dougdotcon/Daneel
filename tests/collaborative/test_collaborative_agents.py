"""
Tests for the collaborative agents functionality.
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

from parlant.knowledge import KnowledgeManager

from parlant.collaborative.protocol import (
    AgentCommunicator,
    AgentMessage,
    MessageBus,
    MessageType,
    MessagePriority,
)
from parlant.collaborative.team import (
    Team,
    TeamId,
    TeamMember,
    TeamRole,
    TeamManager,
)
from parlant.collaborative.tasks import (
    Task,
    TaskId,
    TaskStatus,
    TaskPriority,
    TaskAssignment,
    TaskManager,
)
from parlant.collaborative.consensus import (
    Consensus,
    ConsensusId,
    ConsensusStatus,
    ConsensusType,
    Vote,
    VoteOption,
    ConsensusManager,
)
from parlant.collaborative.knowledge import (
    SharedKnowledgeAccess,
    SharedKnowledgePermission,
    SharedKnowledgeManager,
)
from parlant.collaborative.agent import CollaborativeAgent, CollaborativeAgentConfig


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


class MockModelManager(ModelManager):
    """Mock model manager for testing."""
    
    async def get_model(self, model_id: str) -> Optional[Model]:
        """Get a model by ID."""
        return MagicMock(spec=Model)


class MockPromptManager(PromptManager):
    """Mock prompt manager for testing."""
    
    async def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Get a prompt by ID."""
        return MagicMock(spec=Prompt)


class MockToolRegistry(ToolRegistry):
    """Mock tool registry for testing."""
    
    def get_tool(self, tool_id: str) -> Optional[Any]:
        """Get a tool by ID."""
        return MagicMock()


class MockKnowledgeManager(KnowledgeManager):
    """Mock knowledge manager for testing."""
    
    def __init__(self):
        """Initialize the mock knowledge manager."""
        self.base = MagicMock()
        self.graph = MagicMock()
        self.reasoner = MagicMock()


@pytest.fixture
def logger():
    return ConsoleLogger()


@pytest.fixture
def agent_store():
    store = MockAgentStore()
    return store


@pytest.fixture
def model_manager():
    return MockModelManager()


@pytest.fixture
def prompt_manager():
    return MockPromptManager()


@pytest.fixture
def tool_registry():
    return MockToolRegistry()


@pytest.fixture
def message_bus():
    return MessageBus()


@pytest.fixture
def knowledge_manager():
    return MockKnowledgeManager()


@pytest.fixture
async def team_manager(agent_store, message_bus, logger):
    manager = TeamManager(
        agent_store=agent_store,
        message_bus=message_bus,
        logger=logger,
    )
    return manager


@pytest.fixture
async def task_manager(agent_store, team_manager, message_bus, logger):
    manager = TaskManager(
        agent_store=agent_store,
        team_manager=team_manager,
        message_bus=message_bus,
        logger=logger,
    )
    return manager


@pytest.fixture
async def consensus_manager(agent_store, team_manager, message_bus, logger):
    manager = ConsensusManager(
        agent_store=agent_store,
        team_manager=team_manager,
        message_bus=message_bus,
        logger=logger,
    )
    return manager


@pytest.fixture
async def shared_knowledge_manager(agent_store, team_manager, knowledge_manager, message_bus, logger):
    manager = SharedKnowledgeManager(
        agent_store=agent_store,
        team_manager=team_manager,
        knowledge_manager=knowledge_manager,
        message_bus=message_bus,
        logger=logger,
    )
    return manager


@pytest.fixture
async def collaborative_agent(
    agent_store,
    model_manager,
    prompt_manager,
    tool_registry,
    message_bus,
    team_manager,
    task_manager,
    consensus_manager,
    knowledge_manager,
    shared_knowledge_manager,
    logger,
):
    # Create an agent
    agent = await agent_store.create_agent(name="Test Agent")
    
    # Create a collaborative agent config
    config = CollaborativeAgentConfig(
        agent_type="collaborative",
        name="Test Collaborative Agent",
        description="A test collaborative agent",
        model_id="gpt-4",
        team_ids=[],
        specializations=["coding", "planning"],
        collaboration_mode="proactive",
    )
    
    # Create a collaborative agent
    agent = CollaborativeAgent(
        agent_id=agent.id,
        config=config,
        logger=logger,
        model_manager=model_manager,
        prompt_manager=prompt_manager,
        tool_registry=tool_registry,
        agent_store=agent_store,
        message_bus=message_bus,
        team_manager=team_manager,
        task_manager=task_manager,
        consensus_manager=consensus_manager,
        knowledge_manager=knowledge_manager,
        shared_knowledge_manager=shared_knowledge_manager,
    )
    
    # Initialize the agent
    await agent.initialize()
    
    return agent


async def test_agent_initialization(collaborative_agent):
    """Test that a collaborative agent can be initialized."""
    assert collaborative_agent is not None
    assert collaborative_agent.agent_id is not None
    assert collaborative_agent.state == "idle"


async def test_agent_communication(collaborative_agent, message_bus, agent_store):
    """Test that agents can communicate with each other."""
    # Create another agent
    other_agent = await agent_store.create_agent(name="Other Agent")
    
    # Create a communicator for the other agent
    communicator = AgentCommunicator(
        agent_id=other_agent.id,
        message_bus=message_bus,
    )
    
    # Set up a message handler for the other agent
    received_messages = []
    
    async def message_handler(message):
        received_messages.append(message)
        
    message_bus.subscribe(other_agent.id, message_handler)
    
    # Send a message from the collaborative agent to the other agent
    message = await collaborative_agent._communicator.send_text(
        receiver_id=other_agent.id,
        text="Hello from the collaborative agent!",
    )
    
    # Wait for the message to be processed
    await asyncio.sleep(0.1)
    
    # Check that the message was received
    assert len(received_messages) == 1
    assert received_messages[0].sender_id == collaborative_agent.agent_id
    assert received_messages[0].receiver_id == other_agent.id
    assert received_messages[0].content == "Hello from the collaborative agent!"
    assert received_messages[0].type == MessageType.TEXT


async def test_team_creation_and_membership(collaborative_agent, team_manager):
    """Test that teams can be created and agents can join them."""
    # Create a team
    team = await team_manager.create_team(
        name="Test Team",
        description="A test team",
    )
    
    # Add the agent to the team
    member = await team_manager.add_member(
        team_id=team.id,
        agent_id=collaborative_agent.agent_id,
        roles=[TeamRole.SPECIALIST],
    )
    
    # Check that the agent is a member of the team
    assert member is not None
    assert member.agent_id == collaborative_agent.agent_id
    assert TeamRole.SPECIALIST in member.roles
    
    # Get the team members
    members = await team_manager.get_team_members(team.id)
    
    # Check that the agent is in the list of members
    assert len(members) == 1
    assert members[0][0].id == collaborative_agent.agent_id
    assert members[0][1].agent_id == collaborative_agent.agent_id


async def test_task_assignment_and_execution(collaborative_agent, task_manager):
    """Test that tasks can be assigned to agents and executed."""
    # Create a task
    task = await task_manager.create_task(
        title="Test Task",
        description="A test task",
        creator_id=collaborative_agent.agent_id,
        priority=TaskPriority.NORMAL,
    )
    
    # Assign the task to the agent
    assigned = await task_manager.assign_task(
        task_id=task.id,
        agent_id=collaborative_agent.agent_id,
    )
    
    # Check that the task was assigned
    assert assigned
    
    # Get the agent's tasks
    tasks = await task_manager.get_agent_tasks(collaborative_agent.agent_id)
    
    # Check that the task is in the list
    assert len(tasks) == 1
    assert tasks[0].id == task.id
    assert tasks[0].status == TaskStatus.ASSIGNED
