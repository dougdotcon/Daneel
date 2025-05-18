"""
Collaborative agent system for Parlant.

This module provides a collaborative agent system that extends the base agent system.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
import asyncio
import json

from parlant.core.common import JSONSerializable
from parlant.core.agents import Agent, AgentId, AgentStore
from parlant.core.loggers import Logger
from parlant.core.models import Model, ModelManager
from parlant.core.prompts import Prompt, PromptManager
from parlant.core.tools import ToolRegistry
from parlant.core.agent_system import AgentSystem, AgentConfig, AgentContext, AgentState, AgentType

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


@dataclass
class CollaborativeAgentConfig(AgentConfig):
    """Configuration for a collaborative agent."""
    
    team_ids: List[TeamId] = field(default_factory=list)
    roles: Dict[TeamId, List[TeamRole]] = field(default_factory=dict)
    specializations: List[str] = field(default_factory=list)
    collaboration_mode: str = "proactive"  # "proactive" or "reactive"


class CollaborativeAgent(AgentSystem):
    """Collaborative agent system."""
    
    def __init__(
        self,
        agent_id: AgentId,
        config: CollaborativeAgentConfig,
        logger: Logger,
        model_manager: ModelManager,
        prompt_manager: PromptManager,
        tool_registry: ToolRegistry,
        agent_store: AgentStore,
        message_bus: MessageBus,
        team_manager: TeamManager,
        task_manager: TaskManager,
        consensus_manager: ConsensusManager,
        knowledge_manager: KnowledgeManager,
        shared_knowledge_manager: SharedKnowledgeManager,
    ):
        """Initialize the collaborative agent system.
        
        Args:
            agent_id: Agent ID
            config: Agent configuration
            logger: Logger instance
            model_manager: Model manager
            prompt_manager: Prompt manager
            tool_registry: Tool registry
            agent_store: Agent store
            message_bus: Message bus for agent communication
            team_manager: Team manager
            task_manager: Task manager
            consensus_manager: Consensus manager
            knowledge_manager: Knowledge manager
            shared_knowledge_manager: Shared knowledge manager
        """
        super().__init__(
            agent_id=agent_id,
            config=config,
            logger=logger,
            model_manager=model_manager,
            prompt_manager=prompt_manager,
            tool_registry=tool_registry,
            agent_store=agent_store,
        )
        
        self._message_bus = message_bus
        self._team_manager = team_manager
        self._task_manager = task_manager
        self._consensus_manager = consensus_manager
        self._knowledge_manager = knowledge_manager
        self._shared_knowledge_manager = shared_knowledge_manager
        
        self._communicator: Optional[AgentCommunicator] = None
        self._message_handlers: Dict[MessageType, List[callable]] = {}
        self._assigned_tasks: Set[TaskId] = set()
        self._config = cast(CollaborativeAgentConfig, config)
        
    async def initialize(self) -> None:
        """Initialize the collaborative agent system."""
        # Initialize the base agent system
        await super().initialize()
        
        # Create a communicator for this agent
        self._communicator = AgentCommunicator(
            agent_id=self.agent_id,
            message_bus=self._message_bus,
        )
        
        # Register message handlers
        self._register_message_handlers()
        
        # Join teams
        for team_id in self._config.team_ids:
            roles = self._config.roles.get(team_id, [TeamRole.GENERALIST])
            await self._team_manager.add_member(
                team_id=team_id,
                agent_id=self.agent_id,
                roles=roles,
            )
            
        self.logger.info(f"Collaborative agent {self.agent_id} initialized")
        
    async def run(self, instruction: str) -> str:
        """Run the agent with an instruction.
        
        Args:
            instruction: Instruction for the agent
            
        Returns:
            Result of the agent run
        """
        self.state = AgentState.RUNNING
        
        try:
            # Process the instruction
            result = await self._process_instruction(instruction)
            
            # Check for assigned tasks
            tasks = await self._task_manager.get_agent_tasks(
                agent_id=self.agent_id,
                status=TaskStatus.ASSIGNED,
            )
            
            for task in tasks:
                self._assigned_tasks.add(task.id)
                
                # Update task status
                await self._task_manager.update_task_status(
                    task_id=task.id,
                    agent_id=self.agent_id,
                    status=TaskStatus.IN_PROGRESS,
                )
                
                # Process the task
                task_result = await self._process_task(task)
                
                # Update task status
                await self._task_manager.update_task_status(
                    task_id=task.id,
                    agent_id=self.agent_id,
                    status=TaskStatus.COMPLETED,
                    progress=1.0,
                    result=task_result,
                )
                
                self._assigned_tasks.remove(task.id)
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error running collaborative agent: {e}")
            self.state = AgentState.ERROR
            return f"Error: {e}"
            
        finally:
            if self.state != AgentState.ERROR:
                self.state = AgentState.IDLE
                
    async def stop(self) -> None:
        """Stop the agent."""
        # Stop the base agent system
        await super().stop()
        
        # Cancel any assigned tasks
        for task_id in self._assigned_tasks:
            await self._task_manager.update_task_status(
                task_id=task_id,
                agent_id=self.agent_id,
                status=TaskStatus.FAILED,
                error="Agent stopped",
            )
            
        self._assigned_tasks.clear()
        
    async def _process_instruction(self, instruction: str) -> str:
        """Process an instruction.
        
        Args:
            instruction: Instruction to process
            
        Returns:
            Processing result
        """
        # TODO: Implement instruction processing
        return f"Processed instruction: {instruction}"
        
    async def _process_task(self, task: Task) -> str:
        """Process a task.
        
        Args:
            task: Task to process
            
        Returns:
            Task result
        """
        # TODO: Implement task processing
        return f"Processed task: {task.title}"
        
    def _register_message_handlers(self) -> None:
        """Register handlers for different message types."""
        if not self._communicator:
            return
            
        # Register handlers for different message types
        self._communicator.register_handler(
            MessageType.TEXT,
            self._handle_text_message,
        )
        
        self._communicator.register_handler(
            MessageType.TASK_ASSIGNMENT,
            self._handle_task_assignment,
        )
        
        self._communicator.register_handler(
            MessageType.CONSENSUS,
            self._handle_consensus,
        )
        
        self._communicator.register_handler(
            MessageType.KNOWLEDGE_SHARE,
            self._handle_knowledge_share,
        )
        
    async def _handle_text_message(self, message: AgentMessage) -> None:
        """Handle a text message.
        
        Args:
            message: Received message
        """
        self.logger.info(f"Received text message from {message.sender_id}: {message.content}")
        
        # TODO: Implement text message handling
        
    async def _handle_task_assignment(self, message: AgentMessage) -> None:
        """Handle a task assignment.
        
        Args:
            message: Received message
        """
        self.logger.info(f"Received task assignment from {message.sender_id}")
        
        try:
            # Parse the task assignment
            task_data = json.loads(message.content)
            task_id = task_data.get("task_id")
            
            if not task_id:
                self.logger.error("Invalid task assignment: missing task_id")
                return
                
            # Get the task
            task = await self._task_manager.get_task(task_id)
            if not task:
                self.logger.error(f"Task not found: {task_id}")
                return
                
            # Add to assigned tasks
            self._assigned_tasks.add(task_id)
            
            # Update task status
            await self._task_manager.update_task_status(
                task_id=task_id,
                agent_id=self.agent_id,
                status=TaskStatus.IN_PROGRESS,
            )
            
            # Process the task if the agent is idle
            if self.state == AgentState.IDLE:
                self.state = AgentState.RUNNING
                
                try:
                    # Process the task
                    task_result = await self._process_task(task)
                    
                    # Update task status
                    await self._task_manager.update_task_status(
                        task_id=task_id,
                        agent_id=self.agent_id,
                        status=TaskStatus.COMPLETED,
                        progress=1.0,
                        result=task_result,
                    )
                    
                except Exception as e:
                    self.logger.error(f"Error processing task: {e}")
                    
                    # Update task status
                    await self._task_manager.update_task_status(
                        task_id=task_id,
                        agent_id=self.agent_id,
                        status=TaskStatus.FAILED,
                        error=str(e),
                    )
                    
                finally:
                    self._assigned_tasks.remove(task_id)
                    self.state = AgentState.IDLE
                    
        except Exception as e:
            self.logger.error(f"Error handling task assignment: {e}")
            
    async def _handle_consensus(self, message: AgentMessage) -> None:
        """Handle a consensus message.
        
        Args:
            message: Received message
        """
        self.logger.info(f"Received consensus message from {message.sender_id}")
        
        # TODO: Implement consensus handling
        
    async def _handle_knowledge_share(self, message: AgentMessage) -> None:
        """Handle a knowledge share message.
        
        Args:
            message: Received message
        """
        self.logger.info(f"Received knowledge share message from {message.sender_id}")
        
        # TODO: Implement knowledge share handling
