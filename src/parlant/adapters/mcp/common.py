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

"""Common data structures for MCP (Model Context Protocol)."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class MCPMessageRole(str, Enum):
    """Roles for MCP messages."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class MCPToolCall:
    """Represents a tool call in the MCP protocol."""
    id: str
    name: str
    arguments: Dict[str, Any]
    

@dataclass
class MCPToolResult:
    """Represents a tool result in the MCP protocol."""
    call_id: str
    name: str
    result: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class MCPMessage:
    """Represents a message in the MCP protocol."""
    role: MCPMessageRole
    content: str
    tool_calls: List[MCPToolCall] = field(default_factory=list)
    tool_results: List[MCPToolResult] = field(default_factory=list)
    
    @classmethod
    def system(cls, content: str) -> "MCPMessage":
        """Create a system message."""
        return cls(role=MCPMessageRole.SYSTEM, content=content)
    
    @classmethod
    def user(cls, content: str) -> "MCPMessage":
        """Create a user message."""
        return cls(role=MCPMessageRole.USER, content=content)
    
    @classmethod
    def assistant(cls, content: str, tool_calls: Optional[List[MCPToolCall]] = None) -> "MCPMessage":
        """Create an assistant message."""
        return cls(
            role=MCPMessageRole.ASSISTANT, 
            content=content, 
            tool_calls=tool_calls or []
        )
    
    @classmethod
    def tool(cls, content: str, tool_results: Optional[List[MCPToolResult]] = None) -> "MCPMessage":
        """Create a tool message."""
        return cls(
            role=MCPMessageRole.TOOL, 
            content=content, 
            tool_results=tool_results or []
        )


@dataclass
class MCPTool:
    """Represents a tool in the MCP protocol."""
    name: str
    description: str
    parameters: Dict[str, Any]
    required_parameters: List[str] = field(default_factory=list)
