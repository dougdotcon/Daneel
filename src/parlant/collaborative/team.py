"""
Agent team management for Parlant.

This module provides functionality for organizing agents into teams.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid

from parlant.core.common import JSONSerializable, generate_id
from parlant.core.agents import Agent, AgentId, AgentStore
from parlant.core.loggers import Logger
from parlant.core.async_utils import ReaderWriterLock

from parlant.collaborative.protocol import (
    AgentCommunicator,
    AgentMessage,
    MessageBus,
    MessageType,
    MessagePriority,
)


class TeamRole(str, Enum):
    """Roles that agents can have in a team."""
    
    LEADER = "leader"
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"
    GENERALIST = "generalist"
    OBSERVER = "observer"


class TeamId(str):
    """Team ID."""
    pass


@dataclass
class TeamMember:
    """Member of a team."""
    
    agent_id: AgentId
    roles: List[TeamRole]
    join_time: datetime
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


@dataclass
class Team:
    """Team of agents."""
    
    id: TeamId
    name: str
    description: Optional[str]
    creation_utc: datetime
    members: Dict[AgentId, TeamMember] = field(default_factory=dict)
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class TeamManager:
    """Manager for agent teams."""
    
    def __init__(
        self,
        agent_store: AgentStore,
        message_bus: MessageBus,
        logger: Logger,
    ):
        """Initialize the team manager.
        
        Args:
            agent_store: Agent store
            message_bus: Message bus for agent communication
            logger: Logger instance
        """
        self._agent_store = agent_store
        self._message_bus = message_bus
        self._logger = logger
        self._teams: Dict[TeamId, Team] = {}
        self._agent_teams: Dict[AgentId, Set[TeamId]] = {}
        self._lock = ReaderWriterLock()
        
    async def create_team(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, JSONSerializable]] = None,
    ) -> Team:
        """Create a new team.
        
        Args:
            name: Team name
            description: Team description
            metadata: Additional metadata
            
        Returns:
            Created team
        """
        async with self._lock.writer_lock:
            team_id = TeamId(generate_id())
            
            team = Team(
                id=team_id,
                name=name,
                description=description,
                creation_utc=datetime.now(timezone.utc),
                metadata=metadata or {},
            )
            
            self._teams[team_id] = team
            
        self._logger.info(f"Created team: {name} ({team_id})")
        
        return team
        
    async def get_team(self, team_id: TeamId) -> Optional[Team]:
        """Get a team by ID.
        
        Args:
            team_id: Team ID
            
        Returns:
            Team if found, None otherwise
        """
        async with self._lock.reader_lock:
            return self._teams.get(team_id)
            
    async def list_teams(self) -> List[Team]:
        """List all teams.
        
        Returns:
            List of teams
        """
        async with self._lock.reader_lock:
            return list(self._teams.values())
            
    async def add_member(
        self,
        team_id: TeamId,
        agent_id: AgentId,
        roles: List[TeamRole],
        metadata: Optional[Dict[str, JSONSerializable]] = None,
    ) -> Optional[TeamMember]:
        """Add a member to a team.
        
        Args:
            team_id: Team ID
            agent_id: Agent ID
            roles: Roles for the agent
            metadata: Additional metadata
            
        Returns:
            Added team member if successful, None otherwise
        """
        # Verify that the agent exists
        agent = await self._agent_store.get_agent(agent_id)
        if not agent:
            self._logger.error(f"Agent not found: {agent_id}")
            return None
            
        async with self._lock.writer_lock:
            # Verify that the team exists
            team = self._teams.get(team_id)
            if not team:
                self._logger.error(f"Team not found: {team_id}")
                return None
                
            # Add the member
            member = TeamMember(
                agent_id=agent_id,
                roles=roles,
                join_time=datetime.now(timezone.utc),
                metadata=metadata or {},
            )
            
            team.members[agent_id] = member
            
            # Update agent teams
            if agent_id not in self._agent_teams:
                self._agent_teams[agent_id] = set()
                
            self._agent_teams[agent_id].add(team_id)
            
        self._logger.info(f"Added agent {agent_id} to team {team_id} with roles {roles}")
        
        return member
        
    async def remove_member(
        self,
        team_id: TeamId,
        agent_id: AgentId,
    ) -> bool:
        """Remove a member from a team.
        
        Args:
            team_id: Team ID
            agent_id: Agent ID
            
        Returns:
            True if successful, False otherwise
        """
        async with self._lock.writer_lock:
            # Verify that the team exists
            team = self._teams.get(team_id)
            if not team:
                self._logger.error(f"Team not found: {team_id}")
                return False
                
            # Remove the member
            if agent_id in team.members:
                del team.members[agent_id]
                
                # Update agent teams
                if agent_id in self._agent_teams:
                    self._agent_teams[agent_id].discard(team_id)
                    
                self._logger.info(f"Removed agent {agent_id} from team {team_id}")
                return True
            else:
                self._logger.warning(f"Agent {agent_id} is not a member of team {team_id}")
                return False
                
    async def update_member_roles(
        self,
        team_id: TeamId,
        agent_id: AgentId,
        roles: List[TeamRole],
    ) -> bool:
        """Update a member's roles in a team.
        
        Args:
            team_id: Team ID
            agent_id: Agent ID
            roles: New roles for the agent
            
        Returns:
            True if successful, False otherwise
        """
        async with self._lock.writer_lock:
            # Verify that the team exists
            team = self._teams.get(team_id)
            if not team:
                self._logger.error(f"Team not found: {team_id}")
                return False
                
            # Update the member's roles
            if agent_id in team.members:
                team.members[agent_id].roles = roles
                self._logger.info(f"Updated roles for agent {agent_id} in team {team_id}: {roles}")
                return True
            else:
                self._logger.warning(f"Agent {agent_id} is not a member of team {team_id}")
                return False
                
    async def get_team_members(
        self,
        team_id: TeamId,
    ) -> List[Tuple[Agent, TeamMember]]:
        """Get all members of a team.
        
        Args:
            team_id: Team ID
            
        Returns:
            List of (agent, team member) tuples
        """
        async with self._lock.reader_lock:
            # Verify that the team exists
            team = self._teams.get(team_id)
            if not team:
                self._logger.error(f"Team not found: {team_id}")
                return []
                
            # Get all members
            result = []
            for agent_id, member in team.members.items():
                agent = await self._agent_store.get_agent(agent_id)
                if agent:
                    result.append((agent, member))
                    
            return result
            
    async def get_agent_teams(
        self,
        agent_id: AgentId,
    ) -> List[Team]:
        """Get all teams that an agent is a member of.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            List of teams
        """
        async with self._lock.reader_lock:
            team_ids = self._agent_teams.get(agent_id, set())
            return [self._teams[team_id] for team_id in team_ids if team_id in self._teams]
            
    async def get_team_by_role(
        self,
        team_id: TeamId,
        role: TeamRole,
    ) -> List[Tuple[Agent, TeamMember]]:
        """Get all members of a team with a specific role.
        
        Args:
            team_id: Team ID
            role: Role to filter by
            
        Returns:
            List of (agent, team member) tuples
        """
        async with self._lock.reader_lock:
            # Verify that the team exists
            team = self._teams.get(team_id)
            if not team:
                self._logger.error(f"Team not found: {team_id}")
                return []
                
            # Get members with the specified role
            result = []
            for agent_id, member in team.members.items():
                if role in member.roles:
                    agent = await self._agent_store.get_agent(agent_id)
                    if agent:
                        result.append((agent, member))
                        
            return result
            
    async def broadcast_to_team(
        self,
        sender_id: AgentId,
        team_id: TeamId,
        message_type: MessageType,
        content: str,
        priority: MessagePriority = MessagePriority.NORMAL,
        metadata: Optional[Dict[str, JSONSerializable]] = None,
    ) -> List[AgentMessage]:
        """Broadcast a message to all members of a team.
        
        Args:
            sender_id: Sender agent ID
            team_id: Team ID
            message_type: Message type
            content: Message content
            priority: Message priority
            metadata: Additional metadata
            
        Returns:
            List of sent messages
        """
        async with self._lock.reader_lock:
            # Verify that the team exists
            team = self._teams.get(team_id)
            if not team:
                self._logger.error(f"Team not found: {team_id}")
                return []
                
            # Create a communicator for the sender
            communicator = AgentCommunicator(
                agent_id=sender_id,
                message_bus=self._message_bus,
            )
            
            # Send the message to all team members
            messages = []
            for agent_id in team.members.keys():
                if agent_id != sender_id:  # Don't send to self
                    message = await communicator.send_message(
                        receiver_id=agent_id,
                        message_type=message_type,
                        content=content,
                        priority=priority,
                        metadata=metadata,
                    )
                    messages.append(message)
                    
            return messages
