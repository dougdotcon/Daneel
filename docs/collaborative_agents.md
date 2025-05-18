# Collaborative Agents

This document describes the collaborative agents functionality in the Parlant framework.

## Overview

The collaborative agents module provides a comprehensive set of tools for enabling agents to work together to solve complex problems. It includes:

1. Agent communication protocol for structured message exchange
2. Team management for organizing agents into teams with specific goals
3. Role-based agent specialization to enable division of labor
4. Task delegation and coordination mechanisms for complex problem solving
5. Consensus mechanisms for collaborative decision making
6. Shared knowledge and context between agents

## Components

### Agent Communication Protocol

The agent communication protocol provides a structured way for agents to exchange messages:

- Different message types for different purposes (text, commands, tasks, etc.)
- Message priority levels
- Support for directed and broadcast messages
- Message bus for routing messages between agents

Example usage:

```python
from parlant.collaborative import AgentCommunicator, MessageBus, MessageType, MessagePriority

# Create a message bus
message_bus = MessageBus()

# Create communicators for agents
agent1_communicator = AgentCommunicator(agent_id="agent1", message_bus=message_bus)
agent2_communicator = AgentCommunicator(agent_id="agent2", message_bus=message_bus)

# Register a message handler for agent2
async def handle_text_message(message):
    print(f"Received message: {message.content}")
    
agent2_communicator.register_handler(MessageType.TEXT, handle_text_message)

# Send a message from agent1 to agent2
await agent1_communicator.send_text(
    receiver_id="agent2",
    text="Hello, agent2!",
    priority=MessagePriority.NORMAL,
)

# Broadcast a message from agent1 to all agents
await agent1_communicator.broadcast(
    message_type=MessageType.SYSTEM,
    content="System announcement",
    priority=MessagePriority.HIGH,
)
```

### Team Management

The team management component allows organizing agents into teams:

- Creating and managing teams
- Adding agents to teams with specific roles
- Team-based communication
- Role-based permissions and responsibilities

Example usage:

```python
from parlant.collaborative import TeamManager, TeamRole

# Create a team manager
team_manager = TeamManager(agent_store, message_bus, logger)

# Create a team
team = await team_manager.create_team(
    name="Development Team",
    description="A team for software development",
)

# Add agents to the team with specific roles
await team_manager.add_member(
    team_id=team.id,
    agent_id="agent1",
    roles=[TeamRole.LEADER],
)

await team_manager.add_member(
    team_id=team.id,
    agent_id="agent2",
    roles=[TeamRole.SPECIALIST],
)

# Get team members with a specific role
specialists = await team_manager.get_team_by_role(
    team_id=team.id,
    role=TeamRole.SPECIALIST,
)

# Broadcast a message to all team members
await team_manager.broadcast_to_team(
    sender_id="agent1",
    team_id=team.id,
    message_type=MessageType.TEXT,
    content="Team meeting at 10 AM",
)
```

### Task Delegation and Coordination

The task delegation and coordination component enables agents to assign and coordinate tasks:

- Creating and managing tasks
- Assigning tasks to agents
- Tracking task status and progress
- Handling task dependencies
- Reporting task results

Example usage:

```python
from parlant.collaborative import TaskManager, TaskStatus, TaskPriority

# Create a task manager
task_manager = TaskManager(agent_store, team_manager, message_bus, logger)

# Create a task
task = await task_manager.create_task(
    title="Implement Feature X",
    description="Implement the new feature X according to the specifications",
    creator_id="agent1",
    priority=TaskPriority.HIGH,
    team_id=team.id,
    deadline=datetime.now(timezone.utc) + timedelta(days=3),
)

# Assign the task to an agent
await task_manager.assign_task(
    task_id=task.id,
    agent_id="agent2",
)

# Update task status
await task_manager.update_task_status(
    task_id=task.id,
    agent_id="agent2",
    status=TaskStatus.IN_PROGRESS,
    progress=0.5,
)

# Complete the task
await task_manager.update_task_status(
    task_id=task.id,
    agent_id="agent2",
    status=TaskStatus.COMPLETED,
    progress=1.0,
    result="Feature X has been implemented successfully",
)
```

### Consensus Mechanisms

The consensus mechanisms component enables collaborative decision making:

- Different consensus types (majority, super majority, unanimous, weighted)
- Voting on proposals
- Tracking consensus status
- Notifying participants of results

Example usage:

```python
from parlant.collaborative import ConsensusManager, ConsensusType, VoteOption

# Create a consensus manager
consensus_manager = ConsensusManager(agent_store, team_manager, message_bus, logger)

# Create a consensus process
consensus = await consensus_manager.create_consensus(
    title="Feature Prioritization",
    description="Vote on which feature to implement next",
    creator_id="agent1",
    type=ConsensusType.MAJORITY,
    team_id=team.id,
)

# Agents vote on the consensus
await consensus_manager.vote(
    consensus_id=consensus.id,
    agent_id="agent2",
    option=VoteOption.YES,
    reason="Feature X is more important for our users",
)

await consensus_manager.vote(
    consensus_id=consensus.id,
    agent_id="agent3",
    option=VoteOption.NO,
    reason="Feature Y should be prioritized instead",
)

# Close the consensus process
await consensus_manager.close_consensus(
    consensus_id=consensus.id,
    closer_id="agent1",
)
```

### Shared Knowledge

The shared knowledge component enables agents to share knowledge with each other:

- Different access levels (read, write, admin)
- Sharing knowledge with individual agents or teams
- Tracking permissions
- Notifying agents of shared knowledge

Example usage:

```python
from parlant.collaborative import SharedKnowledgeManager, SharedKnowledgeAccess

# Create a shared knowledge manager
shared_knowledge_manager = SharedKnowledgeManager(
    agent_store, team_manager, knowledge_manager, message_bus, logger
)

# Share knowledge with an agent
await shared_knowledge_manager.share_knowledge(
    knowledge_id="knowledge1",
    owner_id="agent1",
    recipient_id="agent2",
    access=SharedKnowledgeAccess.READ,
)

# Share knowledge with a team
await shared_knowledge_manager.share_with_team(
    knowledge_id="knowledge1",
    owner_id="agent1",
    team_id=team.id,
    access=SharedKnowledgeAccess.WRITE,
)

# Check if an agent has access to knowledge
has_access = await shared_knowledge_manager.check_access(
    knowledge_id="knowledge1",
    agent_id="agent2",
    required_access=SharedKnowledgeAccess.WRITE,
)

# List all knowledge shared with an agent
shared_knowledge = await shared_knowledge_manager.list_shared_knowledge(
    agent_id="agent2",
)
```

### Collaborative Agent

The collaborative agent component extends the base agent system with collaboration capabilities:

- Team membership and roles
- Specializations
- Message handling
- Task processing
- Consensus participation
- Knowledge sharing

Example usage:

```python
from parlant.collaborative import CollaborativeAgent, CollaborativeAgentConfig, TeamRole

# Create a collaborative agent configuration
config = CollaborativeAgentConfig(
    agent_type="collaborative",
    name="Development Agent",
    description="An agent for software development",
    model_id="gpt-4",
    team_ids=[team.id],
    roles={team.id: [TeamRole.SPECIALIST]},
    specializations=["coding", "testing"],
    collaboration_mode="proactive",
)

# Create a collaborative agent
agent = CollaborativeAgent(
    agent_id="agent1",
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

# Run the agent with an instruction
result = await agent.run("Implement a new feature")
```

## Integration with Parlant

The collaborative agents functionality is integrated with the Parlant framework:

1. **Agent System**: Collaborative agents extend the base agent system
2. **Knowledge Management**: Collaborative agents can share knowledge using the knowledge management system
3. **Models**: Collaborative agents use models for generating responses and making decisions
4. **Tools**: Collaborative agents can use tools to perform actions

## Future Enhancements

Potential future enhancements for the collaborative agents module:

1. **Agent Learning**: Allow agents to learn from their collaborative interactions
2. **Conflict Resolution**: Add mechanisms for resolving conflicts between agents
3. **Performance Optimization**: Optimize agent team performance based on past interactions
4. **Dynamic Team Formation**: Enable dynamic team formation based on task requirements
5. **Multi-Modal Collaboration**: Support collaboration across different modalities (text, code, images, etc.)
