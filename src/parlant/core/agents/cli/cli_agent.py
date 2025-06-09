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

"""CLI agent implementation for Daneel."""

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

from Daneel.core.agents import AgentId
from Daneel.core.agents.agent_system import AgentConfig, AgentState, AgentSystem, AgentType
from Daneel.core.agents.utils.message_handler import MessageHandler
from Daneel.core.loggers import Logger
from Daneel.core.models import Model, ModelManager
from Daneel.core.prompts import Prompt, PromptManager
from Daneel.core.tools import ToolContext, ToolRegistry


@dataclass
class ToolCall:
    """A tool call from the model."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class Message:
    """A message in the conversation."""
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None


class CLIAgent(AgentSystem):
    """CLI agent implementation."""
    
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
        """Initialize the CLI agent.
        
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
        
        self.messages: List[Message] = []
        self.message_handler = MessageHandler(logger=logger)
        
    async def initialize(self) -> None:
        """Initialize the CLI agent."""
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
        
        # Initialize the messages with a system message
        system_content = self._build_system_prompt()
        self.messages = [Message(role="system", content=system_content)]
        
        self.state = AgentState.IDLE
        self.logger.info(f"CLI agent {self.agent_id} initialized")
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt from the loaded prompts.
        
        Returns:
            System prompt
        """
        prompt_contents = []
        
        # Add the base CLI agent prompt
        prompt_contents.append("""
You are a CLI agent that can help users with tasks in a terminal environment.
You have access to a set of tools that allow you to interact with the file system, run commands, and more.
Your goal is to help the user accomplish their tasks efficiently and effectively.

Working directory: {workspace_dir}
""".format(workspace_dir=self.workspace_dir))
        
        # Add the contents of the loaded prompts
        for prompt in self.prompts:
            prompt_contents.append(prompt.content)
            
        return "\n\n".join(prompt_contents)
        
    async def run(self, instruction: str) -> str:
        """Run the CLI agent with an instruction.
        
        Args:
            instruction: Instruction for the agent
            
        Returns:
            Result of the agent run
        """
        if self.state == AgentState.RUNNING:
            return "Agent is already running"
            
        self.state = AgentState.RUNNING
        self.interrupt_requested = False
        
        # Add the user message
        self.messages.append(Message(role="user", content=instruction))
        
        # Create a task for the agent run
        self.current_task = asyncio.create_task(self._run_agent_loop())
        
        try:
            result = await self.current_task
            return result
        except asyncio.CancelledError:
            return "Agent run was cancelled"
        finally:
            self.state = AgentState.IDLE
            
    async def _run_agent_loop(self) -> str:
        """Run the agent loop.
        
        Returns:
            Result of the agent run
        """
        iteration = 0
        max_iterations = self.config.max_iterations
        result = ""
        
        while iteration < max_iterations and self.state == AgentState.RUNNING:
            if self.interrupt_requested:
                self.logger.info(f"Agent {self.agent_id} interrupted")
                result = "Agent run was interrupted"
                break
                
            iteration += 1
            self.logger.info(f"Agent {self.agent_id} iteration {iteration}/{max_iterations}")
            
            # Get the model response
            try:
                model_response = await self._get_model_response()
                
                # Process the model response
                if model_response.tool_calls:
                    # Handle tool calls
                    for tool_call in model_response.tool_calls:
                        tool_result = await self._handle_tool_call(tool_call)
                        
                        # Add the tool result as a message
                        self.messages.append(Message(
                            role="tool",
                            content=tool_result,
                            tool_call_id=tool_call.id,
                        ))
                else:
                    # No tool calls, just a regular message
                    result = model_response.content or ""
                    
                    # Check if the agent is done
                    if self._is_agent_done(result):
                        break
            except Exception as e:
                self.logger.error(f"Error in agent loop: {e}")
                result = f"Error: {str(e)}"
                self.state = AgentState.ERROR
                break
                
        if iteration >= max_iterations:
            self.logger.warning(f"Agent {self.agent_id} reached maximum iterations")
            result = "Agent reached maximum iterations"
            
        return result
        
    async def _get_model_response(self) -> Message:
        """Get a response from the model.
        
        Returns:
            Model response
        """
        # Convert messages to the format expected by the model
        model_messages = []
        for message in self.messages:
            model_message = {"role": message.role}
            
            if message.content is not None:
                model_message["content"] = message.content
                
            if message.tool_calls:
                model_message["tool_calls"] = [
                    {
                        "id": tc.id,
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in message.tool_calls
                ]
                
            if message.tool_call_id:
                model_message["tool_call_id"] = message.tool_call_id
                
            model_messages.append(model_message)
            
        # Get the available tools
        tools = []
        for tool_id in self.config.tools:
            tool = await self.tool_registry.get_tool(tool_id)
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            })
            
        # Generate a response from the model
        response = await self.model.generate(
            messages=model_messages,
            max_tokens=self.config.max_tokens_per_iteration,
            tools=tools,
        )
        
        # Parse the response
        if "tool_calls" in response:
            tool_calls = []
            for tc in response["tool_calls"]:
                tool_calls.append(ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=json.loads(tc["function"]["arguments"]),
                ))
                
            model_response = Message(
                role="assistant",
                content=response.get("content"),
                tool_calls=tool_calls,
            )
        else:
            model_response = Message(
                role="assistant",
                content=response.get("content"),
            )
            
        # Add the model response to the messages
        self.messages.append(model_response)
        
        return model_response
        
    async def _handle_tool_call(self, tool_call: ToolCall) -> str:
        """Handle a tool call.
        
        Args:
            tool_call: Tool call to handle
            
        Returns:
            Result of the tool call
        """
        self.logger.info(f"Handling tool call: {tool_call.name}")
        
        try:
            # Get the tool
            tool = await self.tool_registry.get_tool(tool_call.name)
            
            # Create a tool context
            context = ToolContext(
                agent_id=str(self.agent_id),
                session_id="cli_session",
                customer_id="cli_user",
            )
            
            # Call the tool
            result = await self.tool_registry.call_tool(
                tool_id=tool_call.name,
                context=context,
                arguments=tool_call.arguments,
            )
            
            # Return the result
            return json.dumps(result.data)
        except Exception as e:
            self.logger.error(f"Error handling tool call: {e}")
            return json.dumps({"error": str(e)})
            
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
        """Stop the CLI agent."""
        if self.state == AgentState.RUNNING:
            if self.current_task and not self.current_task.done():
                self.current_task.cancel()
                try:
                    await self.current_task
                except asyncio.CancelledError:
                    pass
                    
            self.state = AgentState.STOPPED
            self.logger.info(f"CLI agent {self.agent_id} stopped")
            
    async def cleanup(self) -> None:
        """Clean up resources used by the CLI agent."""
        await super().cleanup()
        
        # Clear the messages
        self.messages = []
