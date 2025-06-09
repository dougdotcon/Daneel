"""
Collaborative agents module for Daneel.

This module provides functionality for agent collaboration, including:
- Agent communication protocol
- Team management
- Task delegation and coordination
- Consensus mechanisms
- Shared knowledge
"""

from Daneel.collaborative.protocol import (
    AgentCommunicator,
    AgentMessage,
    MessageBus,
    MessageType,
    MessagePriority,
)

from Daneel.collaborative.team import (
    Team,
    TeamId,
    TeamMember,
    TeamRole,
    TeamManager,
)

from Daneel.collaborative.tasks import (
    Task,
    TaskId,
    TaskStatus,
    TaskPriority,
    TaskAssignment,
    TaskManager,
)

from Daneel.collaborative.consensus import (
    Consensus,
    ConsensusId,
    ConsensusStatus,
    ConsensusType,
    Vote,
    VoteOption,
    ConsensusManager,
)

from Daneel.collaborative.knowledge import (
    SharedKnowledgeAccess,
    SharedKnowledgePermission,
    SharedKnowledgeManager,
)

__all__ = [
    # Protocol
    "AgentCommunicator",
    "AgentMessage",
    "MessageBus",
    "MessageType",
    "MessagePriority",
    
    # Team
    "Team",
    "TeamId",
    "TeamMember",
    "TeamRole",
    "TeamManager",
    
    # Tasks
    "Task",
    "TaskId",
    "TaskStatus",
    "TaskPriority",
    "TaskAssignment",
    "TaskManager",
    
    # Consensus
    "Consensus",
    "ConsensusId",
    "ConsensusStatus",
    "ConsensusType",
    "Vote",
    "VoteOption",
    "ConsensusManager",
    
    # Shared Knowledge
    "SharedKnowledgeAccess",
    "SharedKnowledgePermission",
    "SharedKnowledgeManager",
]
