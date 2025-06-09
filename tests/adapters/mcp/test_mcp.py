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

"""Tests for the MCP adapter."""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from Daneel.adapters.mcp.client import MCPClient
from Daneel.adapters.mcp.server import MCPServer
from Daneel.adapters.mcp.common import MCPMessage, MCPMessageRole, MCPTool, MCPToolCall, MCPToolResult
from Daneel.adapters.mcp.sequential_thinking import SequentialThinkingMCP, SequentialThought, SequentialThinkingSession


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    return logger


@pytest.fixture
def mock_nlp_service():
    """Create a mock NLP service."""
    nlp_service = MagicMock()
    nlp_service.generate_text = AsyncMock()
    return nlp_service


@pytest.mark.asyncio
async def test_mcp_client_connect(mock_logger):
    """Test connecting to an MCP server."""
    # Mock the aiohttp ClientSession
    mock_session = MagicMock()
    mock_session.ws_connect = AsyncMock()
    
    # Mock the WebSocket connection
    mock_ws = MagicMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.receive_json = AsyncMock(return_value={
        "type": "tools",
        "tools": [
            {
                "name": "test_tool",
                "description": "A test tool",
                "parameters": {},
                "required": []
            }
        ]
    })
    mock_session.ws_connect.return_value = mock_ws
    
    # Create the client
    client = MCPClient(
        server_url="ws://localhost:8080",
        logger=mock_logger,
        session=mock_session
    )
    
    # Connect to the server
    result = await client.connect()
    
    # Check the result
    assert result is True
    assert client._connected is True
    assert len(client.available_tools) == 1
    assert client.available_tools[0].name == "test_tool"
    
    # Check that the correct methods were called
    mock_session.ws_connect.assert_called_once_with(
        "ws://localhost:8080",
        timeout=30
    )
    mock_ws.send_json.assert_called_once_with({
        "type": "get_tools"
    })
    mock_ws.receive_json.assert_called_once()


@pytest.mark.asyncio
async def test_mcp_client_send_message(mock_logger):
    """Test sending a message to an MCP server."""
    # Mock the aiohttp ClientSession
    mock_session = MagicMock()
    mock_session.ws_connect = AsyncMock()
    
    # Mock the WebSocket connection
    mock_ws = MagicMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.receive_json = AsyncMock(side_effect=[
        # First call (connect)
        {
            "type": "tools",
            "tools": []
        },
        # Second call (send_message)
        {
            "type": "message",
            "role": "assistant",
            "content": "Hello, world!",
            "tool_calls": []
        }
    ])
    mock_session.ws_connect.return_value = mock_ws
    
    # Create the client
    client = MCPClient(
        server_url="ws://localhost:8080",
        logger=mock_logger,
        session=mock_session
    )
    
    # Connect to the server
    await client.connect()
    
    # Send a message
    message = MCPMessage.user("Hello!")
    response = await client.send_message(message)
    
    # Check the response
    assert response is not None
    assert response.role == "assistant"
    assert response.content == "Hello, world!"
    
    # Check that the correct methods were called
    assert mock_ws.send_json.call_count == 2
    mock_ws.send_json.assert_any_call({
        "type": "message",
        "role": "user",
        "content": "Hello!"
    })


@pytest.mark.asyncio
async def test_sequential_thinking_mcp(mock_logger, mock_nlp_service):
    """Test the Sequential Thinking MCP."""
    # Create the Sequential Thinking MCP
    sequential_thinking = SequentialThinkingMCP(
        nlp_service=mock_nlp_service,
        logger=mock_logger,
        host="localhost",
        port=8081
    )
    
    # Mock the server start method
    sequential_thinking.server.start = AsyncMock()
    
    # Start the server
    await sequential_thinking.start()
    
    # Check that the server was started
    sequential_thinking.server.start.assert_called_once()
    
    # Test the sequential_thinking tool handler
    result = await sequential_thinking._handle_sequential_thinking({
        "totalThoughts": 5,
        "thought": "First thought",
        "thoughtNumber": 1
    })
    
    # Check the result
    assert "sessionId" in result
    assert result["thoughtNumber"] == 1
    assert result["totalThoughts"] == 5
    assert len(result["thoughts"]) == 1
    assert result["thoughts"][0]["content"] == "First thought"
    
    # Test adding a thought
    session_id = result["sessionId"]
    result = await sequential_thinking._handle_add_thought({
        "sessionId": session_id,
        "thought": "Second thought",
        "thoughtNumber": 2
    })
    
    # Check the result
    assert result["sessionId"] == session_id
    assert result["thoughtNumber"] == 2
    assert len(result["thoughts"]) == 2
    assert result["thoughts"][1]["content"] == "Second thought"
    
    # Test reviewing thoughts
    result = await sequential_thinking._handle_review_thoughts({
        "sessionId": session_id
    })
    
    # Check the result
    assert result["sessionId"] == session_id
    assert result["currentThought"] == 2
    assert len(result["thoughts"]) == 2
    assert result["thoughts"][0]["content"] == "First thought"
    assert result["thoughts"][1]["content"] == "Second thought"
