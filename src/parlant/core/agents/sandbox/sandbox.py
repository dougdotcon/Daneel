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

"""Sandbox for secure code execution."""

import asyncio
import os
import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

from parlant.core.loggers import Logger


@dataclass
class SandboxConfig:
    """Configuration for a sandbox."""
    workspace_dir: str
    allowed_commands: List[str] = None
    blocked_commands: List[str] = None
    timeout_seconds: int = 30
    max_output_size: int = 10000
    environment: Dict[str, str] = None


class Sandbox(ABC):
    """Base class for sandboxes."""
    
    def __init__(self, config: SandboxConfig, logger: Logger):
        """Initialize the sandbox.
        
        Args:
            config: Configuration for the sandbox
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the sandbox."""
        pass
        
    @abstractmethod
    async def execute_command(self, command: str) -> Tuple[int, str, str]:
        """Execute a command in the sandbox.
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        pass
        
    @abstractmethod
    async def execute_file(self, file_path: str, args: List[str] = None) -> Tuple[int, str, str]:
        """Execute a file in the sandbox.
        
        Args:
            file_path: Path to the file to execute
            args: Arguments to pass to the file
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        pass
        
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up the sandbox."""
        pass


class LocalSandbox(Sandbox):
    """Sandbox for local execution."""
    
    async def initialize(self) -> None:
        """Initialize the local sandbox."""
        # Create the workspace directory if it doesn't exist
        os.makedirs(self.config.workspace_dir, exist_ok=True)
        
        self.logger.info(f"Local sandbox initialized with workspace: {self.config.workspace_dir}")
        
    async def execute_command(self, command: str) -> Tuple[int, str, str]:
        """Execute a command in the local sandbox.
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        # Check if the command is allowed
        if not self._is_command_allowed(command):
            return (1, "", f"Command not allowed: {command}")
            
        # Create a process to execute the command
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.config.workspace_dir,
            env=self.config.environment,
        )
        
        try:
            # Wait for the process to complete with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout_seconds,
            )
            
            # Decode and limit the output size
            stdout_str = stdout.decode("utf-8", errors="replace")[:self.config.max_output_size]
            stderr_str = stderr.decode("utf-8", errors="replace")[:self.config.max_output_size]
            
            return (process.returncode, stdout_str, stderr_str)
        except asyncio.TimeoutError:
            # Kill the process if it times out
            process.kill()
            return (1, "", f"Command timed out after {self.config.timeout_seconds} seconds")
            
    async def execute_file(self, file_path: str, args: List[str] = None) -> Tuple[int, str, str]:
        """Execute a file in the local sandbox.
        
        Args:
            file_path: Path to the file to execute
            args: Arguments to pass to the file
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        # Check if the file exists
        full_path = os.path.join(self.config.workspace_dir, file_path)
        if not os.path.isfile(full_path):
            return (1, "", f"File not found: {file_path}")
            
        # Determine the command to execute the file
        if file_path.endswith(".py"):
            command = ["python", file_path]
        elif file_path.endswith(".js"):
            command = ["node", file_path]
        elif file_path.endswith(".sh"):
            command = ["bash", file_path]
        elif os.access(full_path, os.X_OK):
            command = [f"./{file_path}"]
        else:
            return (1, "", f"Unsupported file type: {file_path}")
            
        # Add arguments
        if args:
            command.extend(args)
            
        # Join the command
        command_str = " ".join(command)
        
        # Execute the command
        return await self.execute_command(command_str)
        
    async def cleanup(self) -> None:
        """Clean up the local sandbox."""
        # Nothing to clean up for the local sandbox
        pass
        
    def _is_command_allowed(self, command: str) -> bool:
        """Check if a command is allowed.
        
        Args:
            command: Command to check
            
        Returns:
            True if the command is allowed, False otherwise
        """
        # If no allowed or blocked commands are specified, allow all commands
        if not self.config.allowed_commands and not self.config.blocked_commands:
            return True
            
        # Check if the command is in the blocked list
        if self.config.blocked_commands:
            for blocked in self.config.blocked_commands:
                if blocked in command:
                    return False
                    
        # Check if the command is in the allowed list
        if self.config.allowed_commands:
            for allowed in self.config.allowed_commands:
                if command.startswith(allowed):
                    return True
            return False
            
        return True


class DockerSandbox(Sandbox):
    """Sandbox for Docker execution."""
    
    async def initialize(self) -> None:
        """Initialize the Docker sandbox."""
        # Check if Docker is installed
        try:
            process = await asyncio.create_subprocess_shell(
                "docker --version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error("Docker is not installed or not running")
                raise RuntimeError("Docker is not installed or not running")
                
            # Create a Docker container
            self.container_id = await self._create_container()
            
            self.logger.info(f"Docker sandbox initialized with container: {self.container_id}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Docker sandbox: {e}")
            raise
            
    async def _create_container(self) -> str:
        """Create a Docker container.
        
        Returns:
            Container ID
        """
        # Create a Docker container with the workspace directory mounted
        process = await asyncio.create_subprocess_shell(
            f"docker run -d -v {self.config.workspace_dir}:/workspace python:3.9-slim tail -f /dev/null",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Failed to create Docker container: {stderr.decode()}")
            
        # Return the container ID
        return stdout.decode().strip()
        
    async def execute_command(self, command: str) -> Tuple[int, str, str]:
        """Execute a command in the Docker sandbox.
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        # Check if the command is allowed
        if not self._is_command_allowed(command):
            return (1, "", f"Command not allowed: {command}")
            
        # Create a process to execute the command in the Docker container
        process = await asyncio.create_subprocess_shell(
            f"docker exec {self.container_id} bash -c 'cd /workspace && {command}'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        try:
            # Wait for the process to complete with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout_seconds,
            )
            
            # Decode and limit the output size
            stdout_str = stdout.decode("utf-8", errors="replace")[:self.config.max_output_size]
            stderr_str = stderr.decode("utf-8", errors="replace")[:self.config.max_output_size]
            
            return (process.returncode, stdout_str, stderr_str)
        except asyncio.TimeoutError:
            # Kill the process if it times out
            process.kill()
            return (1, "", f"Command timed out after {self.config.timeout_seconds} seconds")
            
    async def execute_file(self, file_path: str, args: List[str] = None) -> Tuple[int, str, str]:
        """Execute a file in the Docker sandbox.
        
        Args:
            file_path: Path to the file to execute
            args: Arguments to pass to the file
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        # Check if the file exists
        full_path = os.path.join(self.config.workspace_dir, file_path)
        if not os.path.isfile(full_path):
            return (1, "", f"File not found: {file_path}")
            
        # Determine the command to execute the file
        if file_path.endswith(".py"):
            command = ["python", file_path]
        elif file_path.endswith(".js"):
            command = ["node", file_path]
        elif file_path.endswith(".sh"):
            command = ["bash", file_path]
        else:
            return (1, "", f"Unsupported file type: {file_path}")
            
        # Add arguments
        if args:
            command.extend(args)
            
        # Join the command
        command_str = " ".join(command)
        
        # Execute the command
        return await self.execute_command(command_str)
        
    async def cleanup(self) -> None:
        """Clean up the Docker sandbox."""
        # Stop and remove the Docker container
        if hasattr(self, "container_id"):
            process = await asyncio.create_subprocess_shell(
                f"docker rm -f {self.container_id}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            
    def _is_command_allowed(self, command: str) -> bool:
        """Check if a command is allowed.
        
        Args:
            command: Command to check
            
        Returns:
            True if the command is allowed, False otherwise
        """
        # If no allowed or blocked commands are specified, allow all commands
        if not self.config.allowed_commands and not self.config.blocked_commands:
            return True
            
        # Check if the command is in the blocked list
        if self.config.blocked_commands:
            for blocked in self.config.blocked_commands:
                if blocked in command:
                    return False
                    
        # Check if the command is in the allowed list
        if self.config.allowed_commands:
            for allowed in self.config.allowed_commands:
                if command.startswith(allowed):
                    return True
            return False
            
        return True


class SandboxFactory:
    """Factory for creating sandboxes."""
    
    def __init__(self, logger: Logger):
        """Initialize the sandbox factory.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        
    async def create_sandbox(self, config: SandboxConfig, sandbox_type: str = "local") -> Sandbox:
        """Create a sandbox.
        
        Args:
            config: Configuration for the sandbox
            sandbox_type: Type of sandbox to create
            
        Returns:
            Created sandbox
            
        Raises:
            ValueError: If the sandbox type is not supported
        """
        if sandbox_type == "local":
            sandbox = LocalSandbox(config, self.logger)
        elif sandbox_type == "docker":
            sandbox = DockerSandbox(config, self.logger)
        else:
            raise ValueError(f"Unsupported sandbox type: {sandbox_type}")
            
        await sandbox.initialize()
        
        return sandbox
