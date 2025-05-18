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

"""Tests for the agent system."""

import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from parlant.core.agents import (
    AgentConfig,
    AgentContext,
    AgentState,
    AgentSystem,
    AgentSystemFactory,
    AgentType,
)
from parlant.core.agents.cli import CLIAgent
from parlant.core.agents.terminal import TerminalAgent
from parlant.core.agents.sandbox import SandboxConfig, SandboxFactory, LocalSandbox


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    return logger


@pytest.fixture
def mock_model_manager():
    """Create a mock model manager."""
    model_manager = MagicMock()
    model_manager.get_model = AsyncMock()
    return model_manager


@pytest.fixture
def mock_prompt_manager():
    """Create a mock prompt manager."""
    prompt_manager = MagicMock()
    prompt_manager.get_prompt = MagicMock()
    return prompt_manager


@pytest.fixture
def mock_tool_registry():
    """Create a mock tool registry."""
    tool_registry = MagicMock()
    tool_registry.get_tool = AsyncMock()
    tool_registry.call_tool = AsyncMock()
    return tool_registry


@pytest.fixture
def mock_agent_store():
    """Create a mock agent store."""
    agent_store = MagicMock()
    return agent_store


@pytest.fixture
def agent_config():
    """Create an agent configuration."""
    return AgentConfig(
        agent_type=AgentType.CLI,
        name="Test Agent",
        description="A test agent",
        model_id="gpt-4",
        max_iterations=5,
        max_tokens_per_iteration=1000,
        tools=["tool1", "tool2"],
        prompts=["prompt1", "prompt2"],
        environment={"VAR1": "value1", "VAR2": "value2"},
        metadata={"key1": "value1", "key2": "value2"},
    )


@pytest.fixture
def temp_workspace_dir():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


class TestAgentSystem:
    """Tests for the agent system."""
    
    @pytest.mark.asyncio
    async def test_agent_system_factory(
        self,
        mock_logger,
        mock_model_manager,
        mock_prompt_manager,
        mock_tool_registry,
        mock_agent_store,
        agent_config,
    ):
        """Test the agent system factory."""
        # Create a factory
        factory = AgentSystemFactory(
            logger=mock_logger,
            model_manager=mock_model_manager,
            prompt_manager=mock_prompt_manager,
            tool_registry=mock_tool_registry,
            agent_store=mock_agent_store,
        )
        
        # Register agent system types
        factory.register_agent_system_type(AgentType.CLI, CLIAgent)
        factory.register_agent_system_type(AgentType.TERMINAL, TerminalAgent)
        
        # Create a CLI agent
        with patch.object(CLIAgent, "initialize", AsyncMock()):
            agent = await factory.create_agent_system("agent1", agent_config)
            
            # Check that the agent was created
            assert isinstance(agent, CLIAgent)
            assert agent.agent_id == "agent1"
            assert agent.config == agent_config
            
            # Check that initialize was called
            agent.initialize.assert_called_once()
            
        # Create a terminal agent
        terminal_config = AgentConfig(
            agent_type=AgentType.TERMINAL,
            name="Terminal Agent",
            description="A terminal agent",
            model_id="gpt-4",
        )
        
        with patch.object(TerminalAgent, "initialize", AsyncMock()):
            agent = await factory.create_agent_system("agent2", terminal_config)
            
            # Check that the agent was created
            assert isinstance(agent, TerminalAgent)
            assert agent.agent_id == "agent2"
            assert agent.config == terminal_config
            
            # Check that initialize was called
            agent.initialize.assert_called_once()
            
        # Try to create an agent with an unregistered type
        custom_config = AgentConfig(
            agent_type=AgentType.CUSTOM,
            name="Custom Agent",
            description="A custom agent",
            model_id="gpt-4",
        )
        
        with pytest.raises(ValueError):
            await factory.create_agent_system("agent3", custom_config)
            
    @pytest.mark.asyncio
    async def test_cli_agent(
        self,
        mock_logger,
        mock_model_manager,
        mock_prompt_manager,
        mock_tool_registry,
        mock_agent_store,
        agent_config,
        temp_workspace_dir,
    ):
        """Test the CLI agent."""
        # Create a CLI agent
        agent = CLIAgent(
            agent_id="agent1",
            config=agent_config,
            logger=mock_logger,
            model_manager=mock_model_manager,
            prompt_manager=mock_prompt_manager,
            tool_registry=mock_tool_registry,
            agent_store=mock_agent_store,
            workspace_dir=temp_workspace_dir,
        )
        
        # Mock the model
        mock_model = MagicMock()
        mock_model.generate = AsyncMock(return_value={"content": "Task completed"})
        mock_model_manager.get_model.return_value = mock_model
        
        # Mock the prompts
        mock_prompt = MagicMock()
        mock_prompt.content = "Test prompt content"
        mock_prompt_manager.get_prompt.return_value = mock_prompt
        
        # Initialize the agent
        await agent.initialize()
        
        # Check that the agent was initialized
        assert agent.state == AgentState.IDLE
        assert agent.model == mock_model
        assert len(agent.prompts) == 2
        assert len(agent.messages) == 1
        assert agent.messages[0].role == "system"
        
        # Run the agent
        result = await agent.run("Test instruction")
        
        # Check that the agent was run
        assert result == "Task completed"
        assert agent.state == AgentState.IDLE
        assert len(agent.messages) == 3
        assert agent.messages[1].role == "user"
        assert agent.messages[1].content == "Test instruction"
        assert agent.messages[2].role == "assistant"
        assert agent.messages[2].content == "Task completed"
        
        # Check that the model was called
        mock_model.generate.assert_called_once()
        
        # Stop the agent
        await agent.stop()
        
        # Check that the agent was stopped
        assert agent.state == AgentState.STOPPED
        
        # Clean up the agent
        await agent.cleanup()
        
    @pytest.mark.asyncio
    async def test_sandbox(
        self,
        mock_logger,
        temp_workspace_dir,
    ):
        """Test the sandbox."""
        # Create a sandbox factory
        factory = SandboxFactory(logger=mock_logger)
        
        # Create a sandbox configuration
        config = SandboxConfig(
            workspace_dir=temp_workspace_dir,
            allowed_commands=["echo", "ls", "cat"],
            blocked_commands=["rm", "mv", "cp"],
            timeout_seconds=5,
            max_output_size=1000,
            environment={"VAR1": "value1", "VAR2": "value2"},
        )
        
        # Create a local sandbox
        sandbox = await factory.create_sandbox(config, "local")
        
        # Check that the sandbox was created
        assert isinstance(sandbox, LocalSandbox)
        
        # Execute a command
        exit_code, stdout, stderr = await sandbox.execute_command("echo 'Hello, world!'")
        
        # Check that the command was executed
        assert exit_code == 0
        assert "Hello, world!" in stdout
        assert not stderr
        
        # Execute a blocked command
        exit_code, stdout, stderr = await sandbox.execute_command("rm -rf /")
        
        # Check that the command was blocked
        assert exit_code == 1
        assert not stdout
        assert "Command not allowed" in stderr
        
        # Create a test file
        test_file_path = os.path.join(temp_workspace_dir, "test.py")
        with open(test_file_path, "w") as f:
            f.write("print('Hello from Python!')")
            
        # Execute the file
        exit_code, stdout, stderr = await sandbox.execute_file("test.py")
        
        # Check that the file was executed
        assert exit_code == 0
        assert "Hello from Python!" in stdout
        assert not stderr
        
        # Clean up the sandbox
        await sandbox.cleanup()
