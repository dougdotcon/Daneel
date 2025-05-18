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

"""Sequential Thinking MCP implementation for Parlant."""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from parlant.adapters.mcp.common import MCPTool, MCPToolCall, MCPToolResult
from parlant.adapters.mcp.server import MCPServer
from parlant.core.loggers import Logger
from parlant.core.nlp.common import NLPService


@dataclass
class SequentialThought:
    """Represents a single thought in the sequential thinking process."""
    id: str
    number: int
    content: str
    timestamp: str
    path: Optional[str] = None


@dataclass
class SequentialThinkingSession:
    """Represents a sequential thinking session."""
    id: str
    thoughts: List[SequentialThought] = field(default_factory=list)
    total_thoughts: int = 0
    current_thought: int = 0


class SequentialThinkingMCP:
    """Sequential Thinking MCP implementation.
    
    This implements the Sequential Thinking MCP server that allows
    models to generate a sequence of thoughts, review them, and
    branch hypotheses before taking action.
    """
    
    def __init__(
        self,
        nlp_service: NLPService,
        logger: Logger,
        host: str = "localhost",
        port: int = 8081,
    ):
        """Initialize the Sequential Thinking MCP.
        
        Args:
            nlp_service: NLP service for generating thoughts
            logger: Logger instance
            host: Host to bind the server to
            port: Port to bind the server to
        """
        self.nlp_service = nlp_service
        self.logger = logger
        self.server = MCPServer(host=host, port=port, logger=logger)
        self._sessions: Dict[str, SequentialThinkingSession] = {}
        
        # Register tools
        self._register_tools()
        
    def _register_tools(self) -> None:
        """Register the sequential thinking tools."""
        # Tool for starting a new sequential thinking session
        self.server.register_tool(
            MCPTool(
                name="sequential_thinking",
                description="Start a sequential thinking session to plan and reason step by step",
                parameters={
                    "type": "object",
                    "properties": {
                        "totalThoughts": {
                            "type": "integer",
                            "description": "Total number of thoughts to generate"
                        },
                        "thought": {
                            "type": "string",
                            "description": "The first thought in the sequence"
                        },
                        "thoughtNumber": {
                            "type": "integer",
                            "description": "The number of this thought (usually 1 for the first thought)"
                        },
                        "path": {
                            "type": "string",
                            "description": "Optional path or context for this thought"
                        }
                    },
                    "required": ["totalThoughts", "thought", "thoughtNumber"]
                },
                required_parameters=["totalThoughts", "thought", "thoughtNumber"]
            ),
            self._handle_sequential_thinking
        )
        
        # Tool for adding a thought to an existing session
        self.server.register_tool(
            MCPTool(
                name="add_thought",
                description="Add a thought to an existing sequential thinking session",
                parameters={
                    "type": "object",
                    "properties": {
                        "sessionId": {
                            "type": "string",
                            "description": "ID of the sequential thinking session"
                        },
                        "thought": {
                            "type": "string",
                            "description": "The thought to add to the sequence"
                        },
                        "thoughtNumber": {
                            "type": "integer",
                            "description": "The number of this thought"
                        },
                        "path": {
                            "type": "string",
                            "description": "Optional path or context for this thought"
                        }
                    },
                    "required": ["sessionId", "thought", "thoughtNumber"]
                },
                required_parameters=["sessionId", "thought", "thoughtNumber"]
            ),
            self._handle_add_thought
        )
        
        # Tool for reviewing thoughts in a session
        self.server.register_tool(
            MCPTool(
                name="review_thoughts",
                description="Review thoughts in a sequential thinking session",
                parameters={
                    "type": "object",
                    "properties": {
                        "sessionId": {
                            "type": "string",
                            "description": "ID of the sequential thinking session"
                        }
                    },
                    "required": ["sessionId"]
                },
                required_parameters=["sessionId"]
            ),
            self._handle_review_thoughts
        )
        
    async def _handle_sequential_thinking(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a sequential thinking tool call.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        total_thoughts = arguments.get("totalThoughts", 5)
        thought = arguments.get("thought", "")
        thought_number = arguments.get("thoughtNumber", 1)
        path = arguments.get("path")
        
        # Create a new session
        session_id = str(uuid.uuid4())
        session = SequentialThinkingSession(
            id=session_id,
            total_thoughts=total_thoughts,
            current_thought=thought_number
        )
        
        # Add the first thought
        session.thoughts.append(
            SequentialThought(
                id=str(uuid.uuid4()),
                number=thought_number,
                content=thought,
                timestamp=self._get_timestamp(),
                path=path
            )
        )
        
        # Store the session
        self._sessions[session_id] = session
        
        return {
            "sessionId": session_id,
            "thoughtNumber": thought_number,
            "totalThoughts": total_thoughts,
            "thoughts": [
                {
                    "id": t.id,
                    "number": t.number,
                    "content": t.content,
                    "timestamp": t.timestamp,
                    "path": t.path
                }
                for t in session.thoughts
            ]
        }
        
    async def _handle_add_thought(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle adding a thought to an existing session.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        session_id = arguments.get("sessionId", "")
        thought = arguments.get("thought", "")
        thought_number = arguments.get("thoughtNumber", 1)
        path = arguments.get("path")
        
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
            
        session = self._sessions[session_id]
        
        # Add the thought
        session.thoughts.append(
            SequentialThought(
                id=str(uuid.uuid4()),
                number=thought_number,
                content=thought,
                timestamp=self._get_timestamp(),
                path=path
            )
        )
        
        # Update current thought
        session.current_thought = thought_number
        
        return {
            "sessionId": session_id,
            "thoughtNumber": thought_number,
            "totalThoughts": session.total_thoughts,
            "thoughts": [
                {
                    "id": t.id,
                    "number": t.number,
                    "content": t.content,
                    "timestamp": t.timestamp,
                    "path": t.path
                }
                for t in session.thoughts
            ]
        }
        
    async def _handle_review_thoughts(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reviewing thoughts in a session.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        session_id = arguments.get("sessionId", "")
        
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
            
        session = self._sessions[session_id]
        
        return {
            "sessionId": session_id,
            "currentThought": session.current_thought,
            "totalThoughts": session.total_thoughts,
            "thoughts": [
                {
                    "id": t.id,
                    "number": t.number,
                    "content": t.content,
                    "timestamp": t.timestamp,
                    "path": t.path
                }
                for t in session.thoughts
            ]
        }
        
    def _get_timestamp(self) -> str:
        """Get the current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
        
    async def start(self) -> None:
        """Start the Sequential Thinking MCP server."""
        await self.server.start()
        self.logger.info("Sequential Thinking MCP server started")
