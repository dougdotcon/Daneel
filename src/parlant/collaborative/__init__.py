"""
Collaborative agents module for Parlant.

This module provides functionality for agent collaboration, including:
- Agent communication protocol
- Team management
- Task delegation and coordination
- Consensus mechanisms
- Shared knowledge
"""

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
