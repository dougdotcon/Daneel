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

"""Message handler for agent systems."""

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

from parlant.core.loggers import Logger


@dataclass
class Message:
    """A message in a conversation."""
    role: str
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        result = {"role": self.role}
        
        if self.content is not None:
            result["content"] = self.content
            
        if self.name is not None:
            result["name"] = self.name
            
        if self.tool_calls is not None:
            result["tool_calls"] = self.tool_calls
            
        if self.tool_call_id is not None:
            result["tool_call_id"] = self.tool_call_id
            
        return result
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create a message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            Created message
        """
        return cls(
            role=data["role"],
            content=data.get("content"),
            name=data.get("name"),
            tool_calls=data.get("tool_calls"),
            tool_call_id=data.get("tool_call_id"),
        )


class MessageHandler:
    """Handler for messages in agent systems."""
    
    def __init__(self, logger: Logger):
        """Initialize the message handler.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        
    def parse_message(self, message: str) -> Message:
        """Parse a message string into a Message object.
        
        Args:
            message: Message string
            
        Returns:
            Parsed message
        """
        # Default to user message
        role = "user"
        content = message
        
        # Check for role prefix
        role_match = re.match(r"^(system|user|assistant|tool):\s*(.*)", message, re.DOTALL)
        if role_match:
            role = role_match.group(1)
            content = role_match.group(2)
            
        return Message(role=role, content=content)
        
    def format_message(self, message: Message) -> str:
        """Format a Message object into a string.
        
        Args:
            message: Message to format
            
        Returns:
            Formatted message string
        """
        if message.role == "tool" and message.tool_call_id:
            return f"tool ({message.tool_call_id}): {message.content}"
        elif message.tool_calls:
            tool_calls_str = []
            for tc in message.tool_calls:
                function = tc.get("function", {})
                name = function.get("name", "unknown")
                args = function.get("arguments", "{}")
                tool_calls_str.append(f"{name}({args})")
            
            tool_calls = ", ".join(tool_calls_str)
            content = message.content or ""
            
            if content:
                return f"{message.role}: {content}\nTool calls: {tool_calls}"
            else:
                return f"{message.role}: Tool calls: {tool_calls}"
        else:
            return f"{message.role}: {message.content}"
            
    def extract_code_blocks(self, content: str) -> List[Tuple[str, str]]:
        """Extract code blocks from content.
        
        Args:
            content: Content to extract code blocks from
            
        Returns:
            List of tuples of (language, code)
        """
        code_blocks = []
        
        # Extract code blocks with language
        pattern = r"```(\w*)\n(.*?)\n```"
        matches = re.findall(pattern, content, re.DOTALL)
        
        for language, code in matches:
            code_blocks.append((language.strip() or "text", code.strip()))
            
        return code_blocks
        
    def extract_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """Extract tool calls from content.
        
        Args:
            content: Content to extract tool calls from
            
        Returns:
            List of tool calls
        """
        tool_calls = []
        
        # Extract function calls
        function_pattern = r"(\w+)\((.*?)\)"
        matches = re.findall(function_pattern, content)
        
        for name, args_str in matches:
            # Try to parse the arguments as JSON
            try:
                args = json.loads(args_str)
            except json.JSONDecodeError:
                # If not valid JSON, try to parse as key-value pairs
                args = {}
                for pair in args_str.split(","):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        args[key.strip()] = value.strip()
                        
            tool_calls.append({
                "id": f"call_{len(tool_calls)}",
                "function": {
                    "name": name,
                    "arguments": json.dumps(args),
                },
            })
            
        return tool_calls
        
    def extract_commands(self, content: str) -> List[str]:
        """Extract commands from content.
        
        Args:
            content: Content to extract commands from
            
        Returns:
            List of commands
        """
        commands = []
        
        # Extract code blocks with bash/shell language
        code_blocks = self.extract_code_blocks(content)
        
        for language, code in code_blocks:
            if language in ["bash", "shell", "sh", ""]:
                # Split multi-line commands
                for line in code.split("\n"):
                    if line.strip():
                        commands.append(line.strip())
                        
        return commands
