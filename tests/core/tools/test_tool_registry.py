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

"""Tests for the tool registry."""

import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from Daneel.core.loggers import Logger
from Daneel.core.tools import LocalToolService, Tool, ToolContext, ToolResult
from Daneel.core.tools.tool_registry import ToolCategory, ToolMetadata, ToolRegistry, tool


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = MagicMock(spec=Logger)
    return logger


@pytest.fixture
def mock_tool_service():
    """Create a mock tool service."""
    tool_service = MagicMock(spec=LocalToolService)
    
    # Mock the create_tool method
    async def create_tool(name, module_path, description, parameters, required, consequential):
        return Tool(
            name=name,
            creation_utc=MagicMock(),
            description=description,
            metadata={},
            parameters=parameters,
            required=required,
            consequential=consequential,
        )
    
    tool_service.create_tool.side_effect = create_tool
    
    # Mock the read_tool method
    async def read_tool(name):
        return Tool(
            name=name,
            creation_utc=MagicMock(),
            description="Test tool",
            metadata={},
            parameters={},
            required=[],
            consequential=False,
        )
    
    tool_service.read_tool.side_effect = read_tool
    
    # Mock the list_tools method
    async def list_tools():
        return [
            Tool(
                name="test_tool_1",
                creation_utc=MagicMock(),
                description="Test tool 1",
                metadata={},
                parameters={},
                required=[],
                consequential=False,
            ),
            Tool(
                name="test_tool_2",
                creation_utc=MagicMock(),
                description="Test tool 2",
                metadata={},
                parameters={},
                required=[],
                consequential=False,
            ),
        ]
    
    tool_service.list_tools.side_effect = list_tools
    
    # Mock the call_tool method
    async def call_tool(name, context, arguments):
        return ToolResult(
            data={"result": "success", "tool": name, "arguments": arguments},
        )
    
    tool_service.call_tool.side_effect = call_tool
    
    return tool_service


@pytest.fixture
def tool_registry(mock_logger, mock_tool_service):
    """Create a tool registry."""
    return ToolRegistry(
        logger=mock_logger,
        tool_service=mock_tool_service,
    )


@pytest.mark.asyncio
async def test_register_tool(tool_registry):
    """Test registering a tool."""
    # Register a tool
    tool = await tool_registry.register_tool(
        tool_id="test_tool",
        module_path="test.module",
        name="Test Tool",
        description="A test tool",
        parameters={},
        required=[],
        category=ToolCategory.UTILS,
        version="1.0.0",
        author="Test Author",
        tags=["test", "tool"],
        documentation_url="https://example.com/docs",
        consequential=False,
    )
    
    # Check that the tool was registered
    assert tool.name == "test_tool"
    assert tool.description == "A test tool"
    
    # Check that the tool metadata was stored
    metadata = tool_registry._tools["test_tool"]
    assert metadata.id == "test_tool"
    assert metadata.name == "Test Tool"
    assert metadata.description == "A test tool"
    assert metadata.category == ToolCategory.UTILS
    assert metadata.version == "1.0.0"
    assert metadata.author == "Test Author"
    assert metadata.tags == ["test", "tool"]
    assert metadata.documentation_url == "https://example.com/docs"
    
    # Check that the tool module path was stored
    assert tool_registry._tool_modules["test_tool"] == "test.module"


@pytest.mark.asyncio
async def test_get_tool(tool_registry):
    """Test getting a tool."""
    # Register a tool
    await tool_registry.register_tool(
        tool_id="test_tool",
        module_path="test.module",
        name="Test Tool",
        description="A test tool",
        parameters={},
        required=[],
        category=ToolCategory.UTILS,
    )
    
    # Get the tool
    tool = await tool_registry.get_tool("test_tool")
    
    # Check that the tool was returned
    assert tool.name == "test_tool"
    assert tool.description == "Test tool"  # From the mock


@pytest.mark.asyncio
async def test_list_tools(tool_registry):
    """Test listing tools."""
    # Register tools
    await tool_registry.register_tool(
        tool_id="test_tool_1",
        module_path="test.module",
        name="Test Tool 1",
        description="A test tool",
        parameters={},
        required=[],
        category=ToolCategory.UTILS,
        tags=["test", "tool"],
    )
    
    await tool_registry.register_tool(
        tool_id="test_tool_2",
        module_path="test.module",
        name="Test Tool 2",
        description="Another test tool",
        parameters={},
        required=[],
        category=ToolCategory.CODE,
        tags=["test", "code"],
    )
    
    # List all tools
    tools = await tool_registry.list_tools()
    
    # Check that all tools were returned
    assert len(tools) == 2
    assert tools[0].name == "test_tool_1"
    assert tools[1].name == "test_tool_2"
    
    # List tools by category
    tools = await tool_registry.list_tools(category=ToolCategory.UTILS)
    
    # Check that only the utils tool was returned
    assert len(tools) == 1
    assert tools[0].name == "test_tool_1"
    
    # List tools by tags
    tools = await tool_registry.list_tools(tags=["code"])
    
    # Check that only the code tool was returned
    assert len(tools) == 1
    assert tools[0].name == "test_tool_2"


@pytest.mark.asyncio
async def test_call_tool(tool_registry):
    """Test calling a tool."""
    # Register a tool
    await tool_registry.register_tool(
        tool_id="test_tool",
        module_path="test.module",
        name="Test Tool",
        description="A test tool",
        parameters={},
        required=[],
        category=ToolCategory.UTILS,
    )
    
    # Create a tool context
    context = ToolContext(
        agent_id="test_agent",
        session_id="test_session",
        customer_id="test_customer",
    )
    
    # Call the tool
    result = await tool_registry.call_tool(
        tool_id="test_tool",
        context=context,
        arguments={"arg1": "value1"},
    )
    
    # Check that the tool was called
    assert result.data["result"] == "success"
    assert result.data["tool"] == "test_tool"
    assert result.data["arguments"] == {"arg1": "value1"}


@pytest.mark.asyncio
async def test_get_tool_metadata(tool_registry):
    """Test getting tool metadata."""
    # Register a tool
    await tool_registry.register_tool(
        tool_id="test_tool",
        module_path="test.module",
        name="Test Tool",
        description="A test tool",
        parameters={},
        required=[],
        category=ToolCategory.UTILS,
        version="1.0.0",
        author="Test Author",
        tags=["test", "tool"],
        documentation_url="https://example.com/docs",
    )
    
    # Get the tool metadata
    metadata = await tool_registry.get_tool_metadata("test_tool")
    
    # Check that the metadata was returned
    assert metadata.id == "test_tool"
    assert metadata.name == "Test Tool"
    assert metadata.description == "A test tool"
    assert metadata.category == ToolCategory.UTILS
    assert metadata.version == "1.0.0"
    assert metadata.author == "Test Author"
    assert metadata.tags == ["test", "tool"]
    assert metadata.documentation_url == "https://example.com/docs"


@pytest.mark.asyncio
async def test_list_tool_metadata(tool_registry):
    """Test listing tool metadata."""
    # Register tools
    await tool_registry.register_tool(
        tool_id="test_tool_1",
        module_path="test.module",
        name="Test Tool 1",
        description="A test tool",
        parameters={},
        required=[],
        category=ToolCategory.UTILS,
        tags=["test", "tool"],
    )
    
    await tool_registry.register_tool(
        tool_id="test_tool_2",
        module_path="test.module",
        name="Test Tool 2",
        description="Another test tool",
        parameters={},
        required=[],
        category=ToolCategory.CODE,
        tags=["test", "code"],
    )
    
    # List all tool metadata
    metadata_list = await tool_registry.list_tool_metadata()
    
    # Check that all metadata was returned
    assert len(metadata_list) == 2
    assert metadata_list[0].id == "test_tool_1"
    assert metadata_list[1].id == "test_tool_2"
    
    # List metadata by category
    metadata_list = await tool_registry.list_tool_metadata(category=ToolCategory.UTILS)
    
    # Check that only the utils metadata was returned
    assert len(metadata_list) == 1
    assert metadata_list[0].id == "test_tool_1"
    
    # List metadata by tags
    metadata_list = await tool_registry.list_tool_metadata(tags=["code"])
    
    # Check that only the code metadata was returned
    assert len(metadata_list) == 1
    assert metadata_list[0].id == "test_tool_2"


def test_tool_decorator():
    """Test the tool decorator."""
    # Define a function with the tool decorator
    @tool(
        id="test_tool",
        name="Test Tool",
        description="A test tool",
        parameters={
            "arg1": {
                "type": "string",
                "description": "Argument 1",
            },
            "arg2": {
                "type": "integer",
                "description": "Argument 2",
            },
        },
        required=["arg1"],
        category=ToolCategory.UTILS,
        version="1.0.0",
        author="Test Author",
        tags=["test", "tool"],
        documentation_url="https://example.com/docs",
    )
    def test_function(arg1, arg2=None):
        return ToolResult(data={"arg1": arg1, "arg2": arg2})
    
    # Check that the function has the tool metadata
    assert hasattr(test_function, "__tool_metadata__")
    
    # Check the tool metadata
    metadata = test_function.__tool_metadata__
    assert metadata["id"] == "test_tool"
    assert metadata["name"] == "Test Tool"
    assert metadata["description"] == "A test tool"
    assert "arg1" in metadata["parameters"]
    assert "arg2" in metadata["parameters"]
    assert metadata["required"] == ["arg1"]
    assert metadata["category"] == ToolCategory.UTILS
    assert metadata["version"] == "1.0.0"
    assert metadata["author"] == "Test Author"
    assert metadata["tags"] == ["test", "tool"]
    assert metadata["documentation_url"] == "https://example.com/docs"
