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

"""Terminal agent implementation for Daneel."""

import asyncio
import json
import os
import pty
import re
import shlex
import signal
import subprocess
import sys
import termios
import tty
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from Daneel.core.agents import AgentId
from Daneel.core.agents.agent_system import AgentConfig, AgentState, AgentSystem, AgentType
from Daneel.core.agents.utils.message_handler import MessageHandler
from Daneel.core.loggers import Logger
from Daneel.core.models import Model, ModelManager
from Daneel.core.prompts import Prompt, PromptManager
from Daneel.core.tools import ToolContext, ToolRegistry


class TerminalAgent(AgentSystem):
    """Terminal agent implementation."""
    
    def __init__(
        self,
        agent_id: AgentId,
        config: AgentConfig,
        logger: Logger,
        model_manager: ModelManager,
        prompt_manager: PromptManager,
        tool_registry: ToolRegistry,
        agent_store: Any,
        workspace_dir: Optional[str] = None,
    ):
        """Initialize the terminal agent.
        
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
        super().__init__(
            agent_id=agent_id,
            config=config,
            logger=logger,
            model_manager=model_manager,
            prompt_manager=prompt_manager,
            tool_registry=tool_registry,
            agent_store=agent_store,
            workspace_dir=workspace_dir,
        )
        
        self.message_handler = MessageHandler(logger=logger)
        self.terminal_fd = -1
        self.terminal_pid = -1
        self.terminal_buffer = ""
        self.terminal_reader_task = None
        
    async def initialize(self) -> None:
        """Initialize the terminal agent."""
        # Load the model
        self.model = await self.model_manager.get_model(self.config.model_id)
        
        # Load the prompts
        self.prompts = []
        for prompt_id in self.config.prompts:
            prompt = self.prompt_manager.get_prompt(prompt_id)
            if prompt:
                self.prompts.append(prompt)
            else:
                self.logger.warning(f"Prompt not found: {prompt_id}")
                
        # Initialize the terminal
        await self._initialize_terminal()
        
        self.state = AgentState.IDLE
        self.logger.info(f"Terminal agent {self.agent_id} initialized")
        
    async def _initialize_terminal(self) -> None:
        """Initialize the terminal."""
        # Create a pseudo-terminal
        self.terminal_pid, self.terminal_fd = pty.fork()
        
        if self.terminal_pid == 0:
            # Child process
            shell = os.environ.get("SHELL", "/bin/bash")
            os.execv(shell, [shell])
        else:
            # Parent process
            # Set terminal to raw mode
            old_settings = termios.tcgetattr(self.terminal_fd)
            tty.setraw(self.terminal_fd)
            
            # Start a task to read from the terminal
            self.terminal_reader_task = asyncio.create_task(self._read_terminal())
            
            # Change to the workspace directory
            os.write(self.terminal_fd, f"cd {self.workspace_dir}\n".encode())
            
            # Wait for the terminal to be ready
            await asyncio.sleep(0.5)
            
    async def _read_terminal(self) -> None:
        """Read from the terminal."""
        while True:
            try:
                data = os.read(self.terminal_fd, 1024)
                if not data:
                    break
                    
                # Add to the buffer
                self.terminal_buffer += data.decode("utf-8", errors="replace")
                
                # Limit the buffer size
                if len(self.terminal_buffer) > 10000:
                    self.terminal_buffer = self.terminal_buffer[-10000:]
            except Exception as e:
                self.logger.error(f"Error reading from terminal: {e}")
                break
                
    async def _write_to_terminal(self, data: str) -> None:
        """Write to the terminal.
        
        Args:
            data: Data to write
        """
        os.write(self.terminal_fd, data.encode())
        
    async def run(self, instruction: str) -> str:
        """Run the terminal agent with an instruction.
        
        Args:
            instruction: Instruction for the agent
            
        Returns:
            Result of the agent run
        """
        if self.state == AgentState.RUNNING:
            return "Agent is already running"
            
        self.state = AgentState.RUNNING
        self.interrupt_requested = False
        
        # Create a task for the agent run
        self.current_task = asyncio.create_task(self._run_agent_loop(instruction))
        
        try:
            result = await self.current_task
            return result
        except asyncio.CancelledError:
            return "Agent run was cancelled"
        finally:
            self.state = AgentState.IDLE
            
    async def _run_agent_loop(self, instruction: str) -> str:
        """Run the agent loop.
        
        Args:
            instruction: Instruction for the agent
            
        Returns:
            Result of the agent run
        """
        iteration = 0
        max_iterations = self.config.max_iterations
        result = ""
        
        # Clear the terminal buffer
        self.terminal_buffer = ""
        
        # Build the system prompt
        system_prompt = self._build_system_prompt()
        
        # Build the user prompt with the terminal state
        user_prompt = f"""
Instruction: {instruction}

Current terminal state:
```
{self.terminal_buffer}
```

Please help me accomplish this task in the terminal. You can execute commands by responding with:
```bash
<command>
```

You can also provide explanations and guidance.
"""
        
        # Initialize the messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        while iteration < max_iterations and self.state == AgentState.RUNNING:
            if self.interrupt_requested:
                self.logger.info(f"Agent {self.agent_id} interrupted")
                result = "Agent run was interrupted"
                break
                
            iteration += 1
            self.logger.info(f"Agent {self.agent_id} iteration {iteration}/{max_iterations}")
            
            # Get the model response
            try:
                response = await self.model.generate(
                    messages=messages,
                    max_tokens=self.config.max_tokens_per_iteration,
                )
                
                # Extract the response content
                content = response.get("content", "")
                
                # Add the assistant message
                messages.append({"role": "assistant", "content": content})
                
                # Extract commands from the response
                commands = self._extract_commands(content)
                
                if commands:
                    # Execute the commands
                    for command in commands:
                        # Write the command to the terminal
                        await self._write_to_terminal(command + "\n")
                        
                        # Wait for the command to complete
                        await asyncio.sleep(1)
                        
                    # Add the terminal output as a user message
                    user_message = f"""
Terminal output:
```
{self.terminal_buffer}
```

What should I do next?
"""
                    messages.append({"role": "user", "content": user_message})
                else:
                    # No commands, check if the agent is done
                    result = content
                    if self._is_agent_done(content):
                        break
                        
                    # Add a user message asking for the next step
                    messages.append({"role": "user", "content": "What should I do next?"})
            except Exception as e:
                self.logger.error(f"Error in agent loop: {e}")
                result = f"Error: {str(e)}"
                self.state = AgentState.ERROR
                break
                
        if iteration >= max_iterations:
            self.logger.warning(f"Agent {self.agent_id} reached maximum iterations")
            result = "Agent reached maximum iterations"
            
        return result
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt from the loaded prompts.
        
        Returns:
            System prompt
        """
        prompt_contents = []
        
        # Add the base terminal agent prompt
        prompt_contents.append("""
You are a terminal agent that can help users with tasks in a terminal environment.
You have access to a terminal session in the user's workspace.
Your goal is to help the user accomplish their tasks efficiently and effectively.

Working directory: {workspace_dir}

Guidelines:
1. Execute commands in the terminal to accomplish the user's task.
2. Provide clear explanations of what you're doing and why.
3. Be careful with destructive commands (rm, mv, etc.) and always confirm before executing them.
4. If a command fails, explain why and suggest alternatives.
5. When you're done with the task, clearly indicate that you've completed it.

When you want to execute a command in the terminal, format it as:
```bash
<command>
```
""".format(workspace_dir=self.workspace_dir))
        
        # Add the contents of the loaded prompts
        for prompt in self.prompts:
            prompt_contents.append(prompt.content)
            
        return "\n\n".join(prompt_contents)
        
    def _extract_commands(self, content: str) -> List[str]:
        """Extract commands from the content.
        
        Args:
            content: Content to extract commands from
            
        Returns:
            List of commands
        """
        commands = []
        
        # Extract commands enclosed in ```bash ... ``` or ```shell ... ``` or ``` ... ```
        bash_pattern = r"```(?:bash|shell)?\s*\n(.*?)\n```"
        matches = re.findall(bash_pattern, content, re.DOTALL)
        
        for match in matches:
            # Split multi-line commands
            for line in match.strip().split("\n"):
                if line.strip():
                    commands.append(line.strip())
                    
        return commands
        
    def _is_agent_done(self, content: str) -> bool:
        """Check if the agent is done.
        
        Args:
            content: Content to check
            
        Returns:
            True if the agent is done, False otherwise
        """
        # Check for completion indicators in the content
        completion_indicators = [
            "task complete",
            "task completed",
            "task is complete",
            "task is completed",
            "completed the task",
            "finished the task",
            "done with the task",
        ]
        
        content_lower = content.lower()
        for indicator in completion_indicators:
            if indicator in content_lower:
                return True
                
        return False
        
    async def stop(self) -> None:
        """Stop the terminal agent."""
        if self.state == AgentState.RUNNING:
            if self.current_task and not self.current_task.done():
                self.current_task.cancel()
                try:
                    await self.current_task
                except asyncio.CancelledError:
                    pass
                    
            self.state = AgentState.STOPPED
            self.logger.info(f"Terminal agent {self.agent_id} stopped")
            
    async def cleanup(self) -> None:
        """Clean up resources used by the terminal agent."""
        await super().cleanup()
        
        # Stop the terminal reader task
        if self.terminal_reader_task:
            self.terminal_reader_task.cancel()
            try:
                await self.terminal_reader_task
            except asyncio.CancelledError:
                pass
                
        # Close the terminal
        if self.terminal_fd >= 0:
            os.close(self.terminal_fd)
            
        # Kill the terminal process
        if self.terminal_pid > 0:
            try:
                os.kill(self.terminal_pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
