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

"""MCP server implementation for exposing Parlant capabilities via MCP."""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import uuid
import aiohttp
from aiohttp import web

from parlant.adapters.mcp.common import MCPMessage, MCPTool, MCPToolCall, MCPToolResult
from parlant.core.loggers import Logger


class MCPServer:
    """Server for exposing Parlant capabilities via MCP."""
    
    def __init__(
        self, 
        host: str = "localhost",
        port: int = 8080,
        logger: Logger = None,
    ):
        """Initialize the MCP server.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
            logger: Logger instance
        """
        self.host = host
        self.port = port
        self.logger = logger
        self.app = web.Application()
        self.app.router.add_get("/", self._handle_websocket)
        self._tools: Dict[str, Tuple[MCPTool, Callable]] = {}
        self._message_handler: Optional[Callable[[MCPMessage], asyncio.Future[MCPMessage]]] = None
        
    def register_tool(self, tool: MCPTool, handler: Callable) -> None:
        """Register a tool with the server.
        
        Args:
            tool: Tool definition
            handler: Function to call when the tool is invoked
        """
        self.logger.info(f"Registering tool: {tool.name}")
        self._tools[tool.name] = (tool, handler)
        
    def set_message_handler(self, handler: Callable[[MCPMessage], asyncio.Future[MCPMessage]]) -> None:
        """Set the handler for incoming messages.
        
        Args:
            handler: Function to call when a message is received
        """
        self._message_handler = handler
        
    async def start(self) -> None:
        """Start the MCP server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        self.logger.info(f"MCP server started at ws://{self.host}:{self.port}")
        
    async def _handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle incoming WebSocket connections.
        
        Args:
            request: The HTTP request
            
        Returns:
            WebSocket response
        """
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.logger.info(f"Client connected: {request.remote}")
        
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    message_type = data.get("type")
                    
                    if message_type == "get_tools":
                        # Send available tools
                        await ws.send_json({
                            "type": "tools",
                            "tools": [
                                {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "parameters": tool.parameters,
                                    "required": tool.required_parameters
                                }
                                for tool, _ in self._tools.values()
                            ]
                        })
                    elif message_type == "message":
                        # Handle incoming message
                        if not self._message_handler:
                            await ws.send_json({
                                "type": "error",
                                "message": "No message handler registered"
                            })
                            continue
                            
                        # Convert to MCPMessage
                        message = MCPMessage(
                            role=data["role"],
                            content=data["content"],
                            tool_calls=[
                                MCPToolCall(
                                    id=tc["id"],
                                    name=tc["name"],
                                    arguments=tc["arguments"]
                                )
                                for tc in data.get("tool_calls", [])
                            ],
                            tool_results=[
                                MCPToolResult(
                                    call_id=tr["call_id"],
                                    name=tr["name"],
                                    result=tr["result"],
                                    error=tr.get("error")
                                )
                                for tr in data.get("tool_results", [])
                            ]
                        )
                        
                        # Process tool calls if present
                        if message.tool_calls:
                            for tool_call in message.tool_calls:
                                if tool_call.name in self._tools:
                                    tool, handler = self._tools[tool_call.name]
                                    try:
                                        result = await handler(tool_call.arguments)
                                        message.tool_results.append(
                                            MCPToolResult(
                                                call_id=tool_call.id,
                                                name=tool_call.name,
                                                result=result
                                            )
                                        )
                                    except Exception as e:
                                        self.logger.error(f"Error executing tool {tool_call.name}: {e}")
                                        message.tool_results.append(
                                            MCPToolResult(
                                                call_id=tool_call.id,
                                                name=tool_call.name,
                                                result={},
                                                error=str(e)
                                            )
                                        )
                                else:
                                    self.logger.warning(f"Unknown tool: {tool_call.name}")
                                    message.tool_results.append(
                                        MCPToolResult(
                                            call_id=tool_call.id,
                                            name=tool_call.name,
                                            result={},
                                            error=f"Unknown tool: {tool_call.name}"
                                        )
                                    )
                        
                        # Process message
                        response = await self._message_handler(message)
                        
                        # Send response
                        await ws.send_json({
                            "type": "message",
                            "role": response.role,
                            "content": response.content,
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "name": tc.name,
                                    "arguments": tc.arguments
                                }
                                for tc in response.tool_calls
                            ],
                            "tool_results": [
                                {
                                    "call_id": tr.call_id,
                                    "name": tr.name,
                                    "result": tr.result,
                                    "error": tr.error
                                }
                                for tr in response.tool_results
                            ]
                        })
                    else:
                        self.logger.warning(f"Unknown message type: {message_type}")
                        await ws.send_json({
                            "type": "error",
                            "message": f"Unknown message type: {message_type}"
                        })
                        
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
                    await ws.send_json({
                        "type": "error",
                        "message": f"Error processing message: {str(e)}"
                    })
            elif msg.type == aiohttp.WSMsgType.ERROR:
                self.logger.error(f"WebSocket connection closed with exception: {ws.exception()}")
                
        self.logger.info(f"Client disconnected: {request.remote}")
        return ws
