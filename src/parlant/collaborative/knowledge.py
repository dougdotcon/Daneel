"""
Shared knowledge for Daneel.

This module provides functionality for sharing knowledge between agents.
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

from Daneel.knowledge import (
    KnowledgeBase,
    KnowledgeItem,
    KnowledgeItemId,
    KnowledgeItemType,
    KnowledgeItemSource,
    KnowledgeGraph,
    KnowledgeManager,
)

from Daneel.collaborative.protocol import (
    AgentCommunicator,
    AgentMessage,
    MessageBus,
    MessageType,
    MessagePriority,
)
from Daneel.collaborative.team import Team, TeamId, TeamManager, TeamRole


class SharedKnowledgeAccess(str, Enum):
    """Access levels for shared knowledge."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


@dataclass
class SharedKnowledgePermission:
    """Permission for shared knowledge."""

    agent_id: AgentId
    access: SharedKnowledgeAccess
    grant_time: datetime
    granted_by: AgentId


class SharedKnowledgeManager:
    """Manager for shared knowledge between agents."""

    def __init__(
        self,
        agent_store: AgentStore,
        team_manager: TeamManager,
        knowledge_manager: KnowledgeManager,
        message_bus: MessageBus,
        logger: Logger,
    ):
        """Initialize the shared knowledge manager.

        Args:
            agent_store: Agent store
            team_manager: Team manager
            knowledge_manager: Knowledge manager
            message_bus: Message bus for agent communication
            logger: Logger instance
        """
        self._agent_store = agent_store
        self._team_manager = team_manager
        self._knowledge_manager = knowledge_manager
        self._message_bus = message_bus
        self._logger = logger
        self._permissions: Dict[KnowledgeItemId, Dict[AgentId, SharedKnowledgePermission]] = {}
        self._team_permissions: Dict[TeamId, Dict[KnowledgeItemId, SharedKnowledgeAccess]] = {}
        self._lock = ReaderWriterLock()

    async def share_knowledge(
        self,
        knowledge_id: KnowledgeItemId,
        owner_id: AgentId,
        recipient_id: AgentId,
        access: SharedKnowledgeAccess = SharedKnowledgeAccess.READ,
    ) -> bool:
        """Share knowledge with another agent.

        Args:
            knowledge_id: Knowledge item ID
            owner_id: Owner agent ID
            recipient_id: Recipient agent ID
            access: Access level

        Returns:
            True if successful, False otherwise
        """
        # Verify that the knowledge item exists
        try:
            knowledge_item = await self._knowledge_manager.base.read_item(knowledge_id)
        except Exception as e:
            self._logger.error(f"Knowledge item not found: {knowledge_id}")
            return False

        # Verify that the agents exist
        owner = await self._agent_store.get_agent(owner_id)
        recipient = await self._agent_store.get_agent(recipient_id)

        if not owner or not recipient:
            self._logger.error(f"Agent not found: {owner_id if not owner else recipient_id}")
            return False

        async with self._lock.writer_lock:
            # Initialize permissions for this knowledge item if needed
            if knowledge_id not in self._permissions:
                self._permissions[knowledge_id] = {}

            # Add permission for the recipient
            self._permissions[knowledge_id][recipient_id] = SharedKnowledgePermission(
                agent_id=recipient_id,
                access=access,
                grant_time=datetime.now(timezone.utc),
                granted_by=owner_id,
            )

        self._logger.info(f"Shared knowledge {knowledge_id} with agent {recipient_id} (access: {access})")

        # Notify the recipient
        await self._notify_knowledge_sharing(knowledge_item, owner_id, recipient_id, access)

        return True

    async def share_with_team(
        self,
        knowledge_id: KnowledgeItemId,
        owner_id: AgentId,
        team_id: TeamId,
        access: SharedKnowledgeAccess = SharedKnowledgeAccess.READ,
    ) -> bool:
        """Share knowledge with a team.

        Args:
            knowledge_id: Knowledge item ID
            owner_id: Owner agent ID
            team_id: Team ID
            access: Access level

        Returns:
            True if successful, False otherwise
        """
        # Verify that the knowledge item exists
        try:
            knowledge_item = await self._knowledge_manager.base.read_item(knowledge_id)
        except Exception as e:
            self._logger.error(f"Knowledge item not found: {knowledge_id}")
            return False

        # Verify that the owner exists
        owner = await self._agent_store.get_agent(owner_id)
        if not owner:
            self._logger.error(f"Agent not found: {owner_id}")
            return False

        # Verify that the team exists
        team = await self._team_manager.get_team(team_id)
        if not team:
            self._logger.error(f"Team not found: {team_id}")
            return False

        async with self._lock.writer_lock:
            # Initialize team permissions if needed
            if team_id not in self._team_permissions:
                self._team_permissions[team_id] = {}

            # Add permission for the team
            self._team_permissions[team_id][knowledge_id] = access

            # Add individual permissions for team members
            if knowledge_id not in self._permissions:
                self._permissions[knowledge_id] = {}

            for member_id in team.members.keys():
                self._permissions[knowledge_id][member_id] = SharedKnowledgePermission(
                    agent_id=member_id,
                    access=access,
                    grant_time=datetime.now(timezone.utc),
                    granted_by=owner_id,
                )

        self._logger.info(f"Shared knowledge {knowledge_id} with team {team_id} (access: {access})")

        # Notify team members
        for member_id in team.members.keys():
            if member_id != owner_id:  # Don't notify the owner
                await self._notify_knowledge_sharing(knowledge_item, owner_id, member_id, access)

        return True

    async def revoke_access(
        self,
        knowledge_id: KnowledgeItemId,
        owner_id: AgentId,
        agent_id: AgentId,
    ) -> bool:
        """Revoke access to knowledge.

        Args:
            knowledge_id: Knowledge item ID
            owner_id: Owner agent ID
            agent_id: Agent ID to revoke access from

        Returns:
            True if successful, False otherwise
        """
        # Verify that the knowledge item exists
        try:
            knowledge_item = await self._knowledge_manager.base.read_item(knowledge_id)
        except Exception as e:
            self._logger.error(f"Knowledge item not found: {knowledge_id}")
            return False

        # Verify that the agents exist
        owner = await self._agent_store.get_agent(owner_id)
        agent = await self._agent_store.get_agent(agent_id)

        if not owner or not agent:
            self._logger.error(f"Agent not found: {owner_id if not owner else agent_id}")
            return False

        async with self._lock.writer_lock:
            # Check if the knowledge item has permissions
            if knowledge_id not in self._permissions:
                self._logger.warning(f"No permissions found for knowledge {knowledge_id}")
                return False

            # Check if the agent has permission
            if agent_id not in self._permissions[knowledge_id]:
                self._logger.warning(f"Agent {agent_id} does not have permission for knowledge {knowledge_id}")
                return False

            # Remove the permission
            del self._permissions[knowledge_id][agent_id]

            # Clean up if no more permissions
            if not self._permissions[knowledge_id]:
                del self._permissions[knowledge_id]

            # Remove from team permissions if needed
            for team_id, perms in self._team_permissions.items():
                if knowledge_id in perms:
                    team = await self._team_manager.get_team(team_id)
                    if team and agent_id in team.members:
                        # Only remove from team permissions if this is the last team member with access
                        other_members_with_access = False
                        for member_id in team.members.keys():
                            if member_id != agent_id and knowledge_id in self._permissions.get(knowledge_id, {}):
                                other_members_with_access = True
                                break

                        if not other_members_with_access:
                            del self._team_permissions[team_id][knowledge_id]

                        if not self._team_permissions[team_id]:
                            del self._team_permissions[team_id]

        self._logger.info(f"Revoked access to knowledge {knowledge_id} from agent {agent_id}")

        # Notify the agent
        await self._notify_access_revocation(knowledge_item, owner_id, agent_id)

        return True

    async def check_access(
        self,
        knowledge_id: KnowledgeItemId,
        agent_id: AgentId,
        required_access: SharedKnowledgeAccess = SharedKnowledgeAccess.READ,
    ) -> bool:
        """Check if an agent has access to knowledge.

        Args:
            knowledge_id: Knowledge item ID
            agent_id: Agent ID
            required_access: Required access level

        Returns:
            True if the agent has the required access, False otherwise
        """
        async with self._lock.reader_lock:
            # Check direct permissions
            if knowledge_id in self._permissions and agent_id in self._permissions[knowledge_id]:
                permission = self._permissions[knowledge_id][agent_id]

                # Check access level
                if required_access == SharedKnowledgeAccess.READ:
                    # Any access level allows reading
                    return True
                elif required_access == SharedKnowledgeAccess.WRITE:
                    # WRITE or ADMIN access allows writing
                    return permission.access in [SharedKnowledgeAccess.WRITE, SharedKnowledgeAccess.ADMIN]
                elif required_access == SharedKnowledgeAccess.ADMIN:
                    # Only ADMIN access allows admin operations
                    return permission.access == SharedKnowledgeAccess.ADMIN

            # Check team permissions
            for team_id, perms in self._team_permissions.items():
                if knowledge_id in perms:
                    team = await self._team_manager.get_team(team_id)
                    if team and agent_id in team.members:
                        team_access = perms[knowledge_id]

                        # Check access level
                        if required_access == SharedKnowledgeAccess.READ:
                            # Any access level allows reading
                            return True
                        elif required_access == SharedKnowledgeAccess.WRITE:
                            # WRITE or ADMIN access allows writing
                            return team_access in [SharedKnowledgeAccess.WRITE, SharedKnowledgeAccess.ADMIN]
                        elif required_access == SharedKnowledgeAccess.ADMIN:
                            # Only ADMIN access allows admin operations
                            return team_access == SharedKnowledgeAccess.ADMIN

        return False

    async def list_shared_knowledge(
        self,
        agent_id: AgentId,
    ) -> List[Tuple[KnowledgeItem, SharedKnowledgeAccess]]:
        """List all knowledge shared with an agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of (knowledge item, access level) tuples
        """
        result = []

        async with self._lock.reader_lock:
            # Check direct permissions
            for knowledge_id, perms in self._permissions.items():
                if agent_id in perms:
                    try:
                        knowledge_item = await self._knowledge_manager.base.read_item(knowledge_id)
                        result.append((knowledge_item, perms[agent_id].access))
                    except Exception as e:
                        self._logger.warning(f"Failed to read knowledge item {knowledge_id}: {e}")

            # Check team permissions
            for team_id, perms in self._team_permissions.items():
                team = await self._team_manager.get_team(team_id)
                if team and agent_id in team.members:
                    for knowledge_id, access in perms.items():
                        # Skip if already added from direct permissions
                        if any(item[0].id == knowledge_id for item in result):
                            continue

                        try:
                            knowledge_item = await self._knowledge_manager.base.read_item(knowledge_id)
                            result.append((knowledge_item, access))
                        except Exception as e:
                            self._logger.warning(f"Failed to read knowledge item {knowledge_id}: {e}")

        return result

    async def _notify_knowledge_sharing(
        self,
        knowledge_item: KnowledgeItem,
        owner_id: AgentId,
        recipient_id: AgentId,
        access: SharedKnowledgeAccess,
    ) -> None:
        """Notify an agent that knowledge has been shared with them.

        Args:
            knowledge_item: Knowledge item
            owner_id: Owner agent ID
            recipient_id: Recipient agent ID
            access: Access level
        """
        # Create a communicator for the owner
        communicator = AgentCommunicator(
            agent_id=owner_id,
            message_bus=self._message_bus,
        )

        # Create knowledge sharing message
        content = json.dumps({
            "knowledge_id": knowledge_item.id,
            "title": knowledge_item.title,
            "type": knowledge_item.type,
            "access": access.value,
        })

        # Send the message
        await communicator.send_message(
            receiver_id=recipient_id,
            message_type=MessageType.KNOWLEDGE_SHARE,
            content=content,
            priority=MessagePriority.NORMAL,
            metadata={"knowledge_id": knowledge_item.id, "access": access.value},
        )

    async def _notify_access_revocation(
        self,
        knowledge_item: KnowledgeItem,
        owner_id: AgentId,
        agent_id: AgentId,
    ) -> None:
        """Notify an agent that their access to knowledge has been revoked.

        Args:
            knowledge_item: Knowledge item
            owner_id: Owner agent ID
            agent_id: Agent ID
        """
        # Create a communicator for the owner
        communicator = AgentCommunicator(
            agent_id=owner_id,
            message_bus=self._message_bus,
        )

        # Create access revocation message
        content = json.dumps({
            "knowledge_id": knowledge_item.id,
            "title": knowledge_item.title,
            "type": knowledge_item.type,
        })

        # Send the message
        await communicator.send_message(
            receiver_id=agent_id,
            message_type=MessageType.KNOWLEDGE_SHARE,
            content=content,
            priority=MessagePriority.NORMAL,
            metadata={"knowledge_id": knowledge_item.id, "action": "revoked"},
        )
