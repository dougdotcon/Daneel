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

"""MCP client implementation for connecting to MCP servers."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import aiohttp
from aiohttp import ClientSession, ClientWebSocketResponse

from parlant.adapters.mcp.common import MCPMessage, MCPTool, MCPToolCall, MCPToolResult
from parlant.core.loggers import Logger


class MCPClient:
    """Client for connecting to MCP servers."""
    
    def __init__(
        self, 
        server_url: str,
        logger: Logger,
        session: Optional[ClientSession] = None,
        timeout: int = 30,
    ):
        """Initialize the MCP client.
        
        Args:
            server_url: URL of the MCP server
            logger: Logger instance
            session: Optional aiohttp session
            timeout: Connection timeout in seconds
        """
        self.server_url = server_url
        self.logger = logger
        self._session = session
        self.timeout = timeout
        self._ws: Optional[ClientWebSocketResponse] = None
        self._connected = False
        self._available_tools: List[MCPTool] = []
        
    async def connect(self) -> bool:
        """Connect to the MCP server.
        
        Returns:
            True if connection was successful, False otherwise
        """
        if self._connected:
            return True
            
        try:
            if not self._session:
                self._session = aiohttp.ClientSession()
                
            self._ws = await self._session.ws_connect(
                self.server_url,
                timeout=self.timeout
            )
            
            # Request available tools from the server
            await self._ws.send_json({
                "type": "get_tools"
            })
            
            # Wait for the tools response
            response = await self._ws.receive_json(timeout=self.timeout)
            if response.get("type") == "tools":
                self._available_tools = [
                    MCPTool(
                        name=tool["name"],
                        description=tool["description"],
                        parameters=tool["parameters"],
                        required_parameters=tool.get("required", [])
                    )
                    for tool in response.get("tools", [])
                ]
                
            self._connected = True
            self.logger.info(f"Connected to MCP server at {self.server_url}")
            self.logger.info(f"Available tools: {[tool.name for tool in self._available_tools]}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server: {e}")
            return False
            
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._ws:
            await self._ws.close()
            self._ws = None
            
        if self._session:
            await self._session.close()
            self._session = None
            
        self._connected = False
        
    async def send_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Send a message to the MCP server.
        
        Args:
            message: The message to send
            
        Returns:
            The response message, or None if there was an error
        """
        if not self._connected or not self._ws:
            if not await self.connect():
                return None
                
        try:
            # Convert message to JSON format expected by MCP
            message_data = {
                "type": "message",
                "role": message.role,
                "content": message.content,
            }
            
            if message.tool_calls:
                message_data["tool_calls"] = [
                    {
                        "id": tc.id,
                        "name": tc.name,
                        "arguments": tc.arguments
                    }
                    for tc in message.tool_calls
                ]
                
            if message.tool_results:
                message_data["tool_results"] = [
                    {
                        "call_id": tr.call_id,
                        "name": tr.name,
                        "result": tr.result,
                        "error": tr.error
                    }
                    for tr in message.tool_results
                ]
                
            # Send the message
            await self._ws.send_json(message_data)
            
            # Wait for response
            response = await self._ws.receive_json(timeout=self.timeout)
            
            if response.get("type") == "message":
                return MCPMessage(
                    role=response["role"],
                    content=response["content"],
                    tool_calls=[
                        MCPToolCall(
                            id=tc["id"],
                            name=tc["name"],
                            arguments=tc["arguments"]
                        )
                        for tc in response.get("tool_calls", [])
                    ],
                    tool_results=[
                        MCPToolResult(
                            call_id=tr["call_id"],
                            name=tr["name"],
                            result=tr["result"],
                            error=tr.get("error")
                        )
                        for tr in response.get("tool_results", [])
                    ]
                )
            else:
                self.logger.error(f"Unexpected response type: {response.get('type')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error sending message to MCP server: {e}")
            return None
            
    @property
    def available_tools(self) -> List[MCPTool]:
        """Get the available tools from the MCP server.
        
        Returns:
            List of available tools
        """
        return self._available_tools
