"""
Consensus mechanisms for Daneel.

This module provides mechanisms for collaborative decision making between agents.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid
import json

from Daneel.core.common import JSONSerializable, generate_id
from Daneel.core.agents import Agent, AgentId, AgentStore
from Daneel.core.loggers import Logger
from Daneel.core.async_utils import ReaderWriterLock

from Daneel.collaborative.protocol import (
    AgentCommunicator,
    AgentMessage,
    MessageBus,
    MessageType,
    MessagePriority,
)
from Daneel.collaborative.team import Team, TeamId, TeamManager, TeamRole


class VoteOption(str, Enum):
    """Options for voting."""

    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"


class ConsensusStatus(str, Enum):
    """Status of a consensus process."""

    OPEN = "open"
    CLOSED = "closed"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ConsensusType(str, Enum):
    """Types of consensus processes."""

    MAJORITY = "majority"  # Simple majority (>50%)
    SUPER_MAJORITY = "super_majority"  # Super majority (>2/3)
    UNANIMOUS = "unanimous"  # All votes must be YES
    WEIGHTED = "weighted"  # Votes are weighted by agent role


class ConsensusId(str):
    """Consensus ID."""
    pass


@dataclass
class Vote:
    """Vote in a consensus process."""

    agent_id: AgentId
    option: VoteOption
    timestamp: datetime
    reason: Optional[str] = None
    weight: float = 1.0


@dataclass
class Consensus:
    """Consensus process for collaborative decision making."""

    id: ConsensusId
    title: str
    description: str
    creation_utc: datetime
    status: ConsensusStatus
    type: ConsensusType
    creator_id: AgentId
    team_id: Optional[TeamId] = None
    votes: Dict[AgentId, Vote] = field(default_factory=dict)
    deadline: Optional[datetime] = None
    required_participants: Optional[List[AgentId]] = None
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class ConsensusManager:
    """Manager for consensus processes."""

    def __init__(
        self,
        agent_store: AgentStore,
        team_manager: TeamManager,
        message_bus: MessageBus,
        logger: Logger,
    ):
        """Initialize the consensus manager.

        Args:
            agent_store: Agent store
            team_manager: Team manager
            message_bus: Message bus for agent communication
            logger: Logger instance
        """
        self._agent_store = agent_store
        self._team_manager = team_manager
        self._message_bus = message_bus
        self._logger = logger
        self._consensus_processes: Dict[ConsensusId, Consensus] = {}
        self._agent_consensus: Dict[AgentId, Set[ConsensusId]] = {}
        self._lock = ReaderWriterLock()

    async def create_consensus(
        self,
        title: str,
        description: str,
        creator_id: AgentId,
        type: ConsensusType = ConsensusType.MAJORITY,
        team_id: Optional[TeamId] = None,
        required_participants: Optional[List[AgentId]] = None,
        deadline: Optional[datetime] = None,
        metadata: Optional[Dict[str, JSONSerializable]] = None,
    ) -> Consensus:
        """Create a new consensus process.

        Args:
            title: Consensus title
            description: Consensus description
            creator_id: Creator agent ID
            type: Consensus type
            team_id: Team ID (if the consensus is for a team)
            required_participants: List of agent IDs that must participate
            deadline: Consensus deadline
            metadata: Additional metadata

        Returns:
            Created consensus process
        """
        async with self._lock.writer_lock:
            consensus_id = ConsensusId(generate_id())

            consensus = Consensus(
                id=consensus_id,
                title=title,
                description=description,
                creation_utc=datetime.now(timezone.utc),
                status=ConsensusStatus.OPEN,
                type=type,
                creator_id=creator_id,
                team_id=team_id,
                required_participants=required_participants,
                deadline=deadline,
                metadata=metadata or {},
            )

            self._consensus_processes[consensus_id] = consensus

        self._logger.info(f"Created consensus process: {title} ({consensus_id})")

        # Notify participants
        await self._notify_consensus_creation(consensus)

        return consensus

    async def get_consensus(self, consensus_id: ConsensusId) -> Optional[Consensus]:
        """Get a consensus process by ID.

        Args:
            consensus_id: Consensus ID

        Returns:
            Consensus process if found, None otherwise
        """
        async with self._lock.reader_lock:
            return self._consensus_processes.get(consensus_id)

    async def list_consensus(
        self,
        status: Optional[ConsensusStatus] = None,
        team_id: Optional[TeamId] = None,
        agent_id: Optional[AgentId] = None,
    ) -> List[Consensus]:
        """List consensus processes with optional filtering.

        Args:
            status: Filter by status
            team_id: Filter by team ID
            agent_id: Filter by participant agent ID

        Returns:
            List of consensus processes
        """
        async with self._lock.reader_lock:
            processes = list(self._consensus_processes.values())

            # Apply filters
            if status:
                processes = [p for p in processes if p.status == status]

            if team_id:
                processes = [p for p in processes if p.team_id == team_id]

            if agent_id:
                # Include processes where the agent is a participant or creator
                processes = [
                    p for p in processes
                    if agent_id in p.votes or agent_id == p.creator_id or
                    (p.required_participants and agent_id in p.required_participants)
                ]

            return processes

    async def vote(
        self,
        consensus_id: ConsensusId,
        agent_id: AgentId,
        option: VoteOption,
        reason: Optional[str] = None,
    ) -> bool:
        """Cast a vote in a consensus process.

        Args:
            consensus_id: Consensus ID
            agent_id: Agent ID
            option: Vote option
            reason: Reason for the vote

        Returns:
            True if successful, False otherwise
        """
        # Verify that the agent exists
        agent = await self._agent_store.get_agent(agent_id)
        if not agent:
            self._logger.error(f"Agent not found: {agent_id}")
            return False

        async with self._lock.writer_lock:
            # Verify that the consensus process exists
            consensus = self._consensus_processes.get(consensus_id)
            if not consensus:
                self._logger.error(f"Consensus process not found: {consensus_id}")
                return False

            # Verify that the consensus process is open
            if consensus.status != ConsensusStatus.OPEN:
                self._logger.error(f"Cannot vote in consensus {consensus_id}: process is {consensus.status}")
                return False

            # Verify that the agent is allowed to vote
            if consensus.team_id:
                team = await self._team_manager.get_team(consensus.team_id)
                if not team or agent_id not in team.members:
                    self._logger.error(f"Agent {agent_id} is not a member of team {consensus.team_id}")
                    return False

            # Determine vote weight
            weight = 1.0
            if consensus.type == ConsensusType.WEIGHTED and consensus.team_id:
                team = await self._team_manager.get_team(consensus.team_id)
                if team and agent_id in team.members:
                    # Weight based on role
                    member = team.members[agent_id]
                    if TeamRole.LEADER in member.roles:
                        weight = 3.0
                    elif TeamRole.COORDINATOR in member.roles:
                        weight = 2.0

            # Cast the vote
            consensus.votes[agent_id] = Vote(
                agent_id=agent_id,
                option=option,
                timestamp=datetime.now(timezone.utc),
                reason=reason,
                weight=weight,
            )

            # Update agent consensus
            if agent_id not in self._agent_consensus:
                self._agent_consensus[agent_id] = set()

            self._agent_consensus[agent_id].add(consensus_id)

            # Check if all required participants have voted
            if consensus.required_participants:
                missing_votes = [
                    pid for pid in consensus.required_participants
                    if pid not in consensus.votes
                ]
                if not missing_votes:
                    # All required participants have voted, check for consensus
                    await self._check_consensus(consensus)

            # If all team members have voted, check for consensus
            if consensus.team_id:
                team = await self._team_manager.get_team(consensus.team_id)
                if team and all(member_id in consensus.votes for member_id in team.members):
                    await self._check_consensus(consensus)

        self._logger.info(f"Agent {agent_id} voted {option} in consensus {consensus_id}")

        # Notify the consensus creator
        await self._notify_vote(consensus, agent_id, option, reason)

        return True

    async def close_consensus(
        self,
        consensus_id: ConsensusId,
        closer_id: AgentId,
    ) -> bool:
        """Close a consensus process.

        Args:
            consensus_id: Consensus ID
            closer_id: Agent ID of the closer

        Returns:
            True if successful, False otherwise
        """
        async with self._lock.writer_lock:
            # Verify that the consensus process exists
            consensus = self._consensus_processes.get(consensus_id)
            if not consensus:
                self._logger.error(f"Consensus process not found: {consensus_id}")
                return False

            # Verify that the consensus process is open
            if consensus.status != ConsensusStatus.OPEN:
                self._logger.error(f"Cannot close consensus {consensus_id}: process is {consensus.status}")
                return False

            # Verify that the closer is the creator or has permission
            if closer_id != consensus.creator_id:
                # Check if the closer is a team leader
                if consensus.team_id:
                    team = await self._team_manager.get_team(consensus.team_id)
                    if not team or closer_id not in team.members:
                        self._logger.error(f"Agent {closer_id} is not authorized to close consensus {consensus_id}")
                        return False

                    member = team.members[closer_id]
                    if TeamRole.LEADER not in member.roles:
                        self._logger.error(f"Agent {closer_id} is not authorized to close consensus {consensus_id}")
                        return False
                else:
                    self._logger.error(f"Agent {closer_id} is not authorized to close consensus {consensus_id}")
                    return False

            # Close the consensus process and check for consensus
            consensus.status = ConsensusStatus.CLOSED
            await self._check_consensus(consensus)

        self._logger.info(f"Closed consensus {consensus_id} by agent {closer_id}")

        # Notify participants
        await self._notify_consensus_closure(consensus, closer_id)

        return True

    async def cancel_consensus(
        self,
        consensus_id: ConsensusId,
        canceller_id: AgentId,
    ) -> bool:
        """Cancel a consensus process.

        Args:
            consensus_id: Consensus ID
            canceller_id: Agent ID of the canceller

        Returns:
            True if successful, False otherwise
        """
        async with self._lock.writer_lock:
            # Verify that the consensus process exists
            consensus = self._consensus_processes.get(consensus_id)
            if not consensus:
                self._logger.error(f"Consensus process not found: {consensus_id}")
                return False

            # Verify that the consensus process is open
            if consensus.status != ConsensusStatus.OPEN:
                self._logger.error(f"Cannot cancel consensus {consensus_id}: process is {consensus.status}")
                return False

            # Verify that the canceller is the creator or has permission
            if canceller_id != consensus.creator_id:
                # Check if the canceller is a team leader
                if consensus.team_id:
                    team = await self._team_manager.get_team(consensus.team_id)
                    if not team or canceller_id not in team.members:
                        self._logger.error(f"Agent {canceller_id} is not authorized to cancel consensus {consensus_id}")
                        return False

                    member = team.members[canceller_id]
                    if TeamRole.LEADER not in member.roles:
                        self._logger.error(f"Agent {canceller_id} is not authorized to cancel consensus {consensus_id}")
                        return False
                else:
                    self._logger.error(f"Agent {canceller_id} is not authorized to cancel consensus {consensus_id}")
                    return False

            # Cancel the consensus process
            consensus.status = ConsensusStatus.CANCELLED

        self._logger.info(f"Cancelled consensus {consensus_id} by agent {canceller_id}")

        # Notify participants
        await self._notify_consensus_cancellation(consensus, canceller_id)

        return True

    async def _check_consensus(self, consensus: Consensus) -> None:
        """Check if consensus has been reached.

        Args:
            consensus: Consensus process
        """
        if not consensus.votes:
            return

        # Count votes
        yes_votes = sum(vote.weight for vote in consensus.votes.values() if vote.option == VoteOption.YES)
        no_votes = sum(vote.weight for vote in consensus.votes.values() if vote.option == VoteOption.NO)
        abstain_votes = sum(vote.weight for vote in consensus.votes.values() if vote.option == VoteOption.ABSTAIN)
        total_votes = yes_votes + no_votes + abstain_votes

        # Check for consensus based on type
        if consensus.type == ConsensusType.MAJORITY:
            # Simple majority (>50% of non-abstaining votes)
            non_abstain_votes = yes_votes + no_votes
            if non_abstain_votes > 0 and yes_votes > non_abstain_votes / 2:
                consensus.status = ConsensusStatus.APPROVED
            elif non_abstain_votes > 0 and no_votes >= non_abstain_votes / 2:
                consensus.status = ConsensusStatus.REJECTED

        elif consensus.type == ConsensusType.SUPER_MAJORITY:
            # Super majority (>2/3 of non-abstaining votes)
            non_abstain_votes = yes_votes + no_votes
            if non_abstain_votes > 0 and yes_votes > non_abstain_votes * 2 / 3:
                consensus.status = ConsensusStatus.APPROVED
            elif non_abstain_votes > 0 and no_votes >= non_abstain_votes / 3:
                consensus.status = ConsensusStatus.REJECTED

        elif consensus.type == ConsensusType.UNANIMOUS:
            # All votes must be YES (abstentions allowed)
            if no_votes == 0 and yes_votes > 0:
                consensus.status = ConsensusStatus.APPROVED
            elif no_votes > 0:
                consensus.status = ConsensusStatus.REJECTED

        elif consensus.type == ConsensusType.WEIGHTED:
            # Weighted majority (>50% of total weight)
            if yes_votes > total_votes / 2:
                consensus.status = ConsensusStatus.APPROVED
            elif no_votes >= total_votes / 2:
                consensus.status = ConsensusStatus.REJECTED

    async def _notify_consensus_creation(self, consensus: Consensus) -> None:
        """Notify participants of a new consensus process.

        Args:
            consensus: Consensus process
        """
        # Create a communicator for the creator
        communicator = AgentCommunicator(
            agent_id=consensus.creator_id,
            message_bus=self._message_bus,
        )

        # Create consensus creation message
        content = json.dumps({
            "consensus_id": consensus.id,
            "title": consensus.title,
            "description": consensus.description,
            "type": consensus.type.value,
            "deadline": consensus.deadline.isoformat() if consensus.deadline else None,
        })

        # Determine recipients
        recipients = set()

        # Add required participants
        if consensus.required_participants:
            recipients.update(consensus.required_participants)

        # Add team members
        if consensus.team_id:
            team = await self._team_manager.get_team(consensus.team_id)
            if team:
                recipients.update(team.members.keys())

        # Remove creator from recipients
        recipients.discard(consensus.creator_id)

        # Send the message to all recipients
        for recipient_id in recipients:
            await communicator.send_message(
                receiver_id=recipient_id,
                message_type=MessageType.CONSENSUS,
                content=content,
                priority=MessagePriority.HIGH,
                metadata={"consensus_id": consensus.id, "action": "created"},
            )

    async def _notify_vote(
        self,
        consensus: Consensus,
        agent_id: AgentId,
        option: VoteOption,
        reason: Optional[str],
    ) -> None:
        """Notify the consensus creator of a vote.

        Args:
            consensus: Consensus process
            agent_id: Agent ID
            option: Vote option
            reason: Reason for the vote
        """
        # Create a communicator for the agent
        communicator = AgentCommunicator(
            agent_id=agent_id,
            message_bus=self._message_bus,
        )

        # Create vote message
        content = json.dumps({
            "consensus_id": consensus.id,
            "option": option.value,
            "reason": reason,
        })

        # Send the message to the creator
        await communicator.send_message(
            receiver_id=consensus.creator_id,
            message_type=MessageType.VOTE,
            content=content,
            priority=MessagePriority.NORMAL,
            metadata={"consensus_id": consensus.id, "option": option.value},
        )

    async def _notify_consensus_closure(
        self,
        consensus: Consensus,
        closer_id: AgentId,
    ) -> None:
        """Notify participants of a consensus process closure.

        Args:
            consensus: Consensus process
            closer_id: Agent ID of the closer
        """
        # Create a communicator for the closer
        communicator = AgentCommunicator(
            agent_id=closer_id,
            message_bus=self._message_bus,
        )

        # Create consensus closure message
        content = json.dumps({
            "consensus_id": consensus.id,
            "status": consensus.status.value,
            "result": "approved" if consensus.status == ConsensusStatus.APPROVED else "rejected",
        })

        # Determine recipients
        recipients = set(consensus.votes.keys())

        # Add required participants who haven't voted
        if consensus.required_participants:
            recipients.update(consensus.required_participants)

        # Add team members who haven't voted
        if consensus.team_id:
            team = await self._team_manager.get_team(consensus.team_id)
            if team:
                recipients.update(team.members.keys())

        # Remove closer from recipients
        recipients.discard(closer_id)

        # Send the message to all recipients
        for recipient_id in recipients:
            await communicator.send_message(
                receiver_id=recipient_id,
                message_type=MessageType.CONSENSUS,
                content=content,
                priority=MessagePriority.HIGH,
                metadata={"consensus_id": consensus.id, "action": "closed", "status": consensus.status.value},
            )

    async def _notify_consensus_cancellation(
        self,
        consensus: Consensus,
        canceller_id: AgentId,
    ) -> None:
        """Notify participants of a consensus process cancellation.

        Args:
            consensus: Consensus process
            canceller_id: Agent ID of the canceller
        """
        # Create a communicator for the canceller
        communicator = AgentCommunicator(
            agent_id=canceller_id,
            message_bus=self._message_bus,
        )

        # Create consensus cancellation message
        content = json.dumps({
            "consensus_id": consensus.id,
            "status": consensus.status.value,
            "reason": "Consensus process cancelled",
        })

        # Determine recipients
        recipients = set(consensus.votes.keys())

        # Add required participants who haven't voted
        if consensus.required_participants:
            recipients.update(consensus.required_participants)

        # Add team members who haven't voted
        if consensus.team_id:
            team = await self._team_manager.get_team(consensus.team_id)
            if team:
                recipients.update(team.members.keys())

        # Remove canceller from recipients
        recipients.discard(canceller_id)

        # Send the message to all recipients
        for recipient_id in recipients:
            await communicator.send_message(
                receiver_id=recipient_id,
                message_type=MessageType.CONSENSUS,
                content=content,
                priority=MessagePriority.HIGH,
                metadata={"consensus_id": consensus.id, "action": "cancelled"},
            )
