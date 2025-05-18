# Copyright 2025 Emcie Co Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Agent system for Parlant."""

import asyncio
import os
import signal
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Type, Union, cast

from parlant.core.agents import Agent, AgentId, AgentStore
from parlant.core.loggers import Logger
from parlant.core.models import Model, ModelManager
from parlant.core.prompts import Prompt, PromptManager
from parlant.core.tools import ToolRegistry


class AgentState(str, Enum):
    """States of an agent."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class AgentType(str, Enum):
    """Types of agents."""
    CLI = "cli"
    TERMINAL = "terminal"
    WEB = "web"
    CUSTOM = "custom"


@dataclass
class AgentContext:
    """Context for an agent."""
    agent_id: AgentId
    workspace_dir: str
    model: Model
    tools: List[str]
    prompts: List[str]
    environment: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    agent_type: AgentType
    name: str
    description: Optional[str] = None
    model_id: str = "gpt-4"
    max_iterations: int = 10
    max_tokens_per_iteration: int = 4096
    tools: List[str] = field(default_factory=list)
    prompts: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentSystem(ABC):
    """Base class for agent systems."""
    
    def __init__(
        self,
        agent_id: AgentId,
        config: AgentConfig,
        logger: Logger,
        model_manager: ModelManager,
        prompt_manager: PromptManager,
        tool_registry: ToolRegistry,
        agent_store: AgentStore,
        workspace_dir: Optional[str] = None,
    ):
        """Initialize the agent system.
        
        Args:
            agent_id: ID of the agent
            config: Configuration for the agent
            logger: Logger instance
            model_manager: Model manager
            prompt_manager: Prompt manager
            tool_registry: Tool registry
            agent_store: Agent store
            workspace_dir: Directory for the agent's workspace
        """
        self.agent_id = agent_id
        self.config = config
        self.logger = logger
        self.model_manager = model_manager
        self.prompt_manager = prompt_manager
        self.tool_registry = tool_registry
        self.agent_store = agent_store
        self.workspace_dir = workspace_dir or os.path.join(os.getcwd(), "workspace", str(agent_id))
        
        # Create workspace directory if it doesn't exist
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        self.state = AgentState.IDLE
        self.current_task: Optional[asyncio.Task] = None
        self.interrupt_requested = False
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent system."""
        pass
        
    @abstractmethod
    async def run(self, instruction: str) -> str:
        """Run the agent with an instruction.
        
        Args:
            instruction: Instruction for the agent
            
        Returns:
            Result of the agent run
        """
        pass
        
    @abstractmethod
    async def stop(self) -> None:
        """Stop the agent."""
        pass
        
    async def pause(self) -> None:
        """Pause the agent."""
        if self.state == AgentState.RUNNING:
            self.state = AgentState.PAUSED
            self.logger.info(f"Agent {self.agent_id} paused")
            
    async def resume(self) -> None:
        """Resume the agent."""
        if self.state == AgentState.PAUSED:
            self.state = AgentState.RUNNING
            self.logger.info(f"Agent {self.agent_id} resumed")
            
    async def interrupt(self) -> None:
        """Interrupt the agent."""
        if self.state == AgentState.RUNNING:
            self.interrupt_requested = True
            self.logger.info(f"Agent {self.agent_id} interrupt requested")
            
    async def get_state(self) -> AgentState:
        """Get the current state of the agent.
        
        Returns:
            Current state of the agent
        """
        return self.state
        
    async def get_context(self) -> AgentContext:
        """Get the context of the agent.
        
        Returns:
            Context of the agent
        """
        model = await self.model_manager.get_model(self.config.model_id)
        
        return AgentContext(
            agent_id=self.agent_id,
            workspace_dir=self.workspace_dir,
            model=model,
            tools=self.config.tools,
            prompts=self.config.prompts,
            environment=self.config.environment,
            metadata=self.config.metadata,
        )
        
    async def update_config(self, config: AgentConfig) -> None:
        """Update the configuration of the agent.
        
        Args:
            config: New configuration for the agent
        """
        self.config = config
        self.logger.info(f"Agent {self.agent_id} configuration updated")
        
    async def cleanup(self) -> None:
        """Clean up resources used by the agent."""
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass
            
        self.state = AgentState.STOPPED
        self.logger.info(f"Agent {self.agent_id} cleaned up")


class AgentSystemFactory:
    """Factory for creating agent systems."""
    
    def __init__(
        self,
        logger: Logger,
        model_manager: ModelManager,
        prompt_manager: PromptManager,
        tool_registry: ToolRegistry,
        agent_store: AgentStore,
    ):
        """Initialize the agent system factory.
        
        Args:
            logger: Logger instance
            model_manager: Model manager
            prompt_manager: Prompt manager
            tool_registry: Tool registry
            agent_store: Agent store
        """
        self.logger = logger
        self.model_manager = model_manager
        self.prompt_manager = prompt_manager
        self.tool_registry = tool_registry
        self.agent_store = agent_store
        self.agent_system_types: Dict[AgentType, Type[AgentSystem]] = {}
        
    def register_agent_system_type(self, agent_type: AgentType, agent_system_class: Type[AgentSystem]) -> None:
        """Register an agent system type.
        
        Args:
            agent_type: Type of the agent
            agent_system_class: Class for the agent system
        """
        self.agent_system_types[agent_type] = agent_system_class
        self.logger.info(f"Registered agent system type: {agent_type}")
        
    async def create_agent_system(self, agent_id: AgentId, config: AgentConfig) -> AgentSystem:
        """Create an agent system.
        
        Args:
            agent_id: ID of the agent
            config: Configuration for the agent
            
        Returns:
            Created agent system
            
        Raises:
            ValueError: If the agent type is not registered
        """
        if config.agent_type not in self.agent_system_types:
            raise ValueError(f"Agent type not registered: {config.agent_type}")
            
        agent_system_class = self.agent_system_types[config.agent_type]
        
        agent_system = agent_system_class(
            agent_id=agent_id,
            config=config,
            logger=self.logger,
            model_manager=self.model_manager,
            prompt_manager=self.prompt_manager,
            tool_registry=self.tool_registry,
            agent_store=self.agent_store,
        )
        
        await agent_system.initialize()
        
        self.logger.info(f"Created agent system: {agent_id} ({config.agent_type})")
        
        return agent_system
