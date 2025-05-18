# Tool Integration System

This document describes the tool integration system in the Parlant framework.

## Overview

The tool integration system provides a way to create, manage, and use tools in Parlant. It supports:

1. Registering and discovering tools
2. Categorizing tools by functionality
3. Calling tools with arguments
4. Handling tool results
5. Managing tool metadata

## Components

### ToolRegistry

The `ToolRegistry` class is the central component of the tool integration system. It manages the registration, discovery, and access of tools. It provides methods for:

- Registering tools
- Getting tools by ID
- Listing tools by category or tags
- Calling tools with arguments
- Managing tool metadata

Example usage:

```python
from parlant.core.loggers import ConsoleLogger
from parlant.core.tools import LocalToolService, ToolRegistry
from parlant.core.tools.tool_registry import ToolCategory

# Create a tool registry
tool_service = LocalToolService()
registry = ToolRegistry(
    logger=ConsoleLogger(),
    tool_service=tool_service,
)

# Register a tool
tool = await registry.register_tool(
    tool_id="my_tool",
    module_path="my_module",
    name="My Tool",
    description="A custom tool",
    parameters={
        "param1": {
            "type": "string",
            "description": "Parameter 1",
        },
    },
    required=["param1"],
    category=ToolCategory.CUSTOM,
    tags=["custom", "example"],
)

# Get a tool
tool = await registry.get_tool("my_tool")

# List tools by category
tools = await registry.list_tools(category=ToolCategory.CUSTOM)

# Call a tool
result = await registry.call_tool(
    tool_id="my_tool",
    context=tool_context,
    arguments={"param1": "value1"},
)
```

### Tool Decorator

The `tool` decorator provides a convenient way to define tools as Python functions. It automatically handles the conversion of function parameters to tool parameters and the registration of the tool with the registry.

Example usage:

```python
from parlant.core.tools import ToolResult
from parlant.core.tools.tool_registry import ToolCategory, tool

@tool(
    id="my_tool",
    name="My Tool",
    description="A custom tool",
    parameters={
        "param1": {
            "type": "string",
            "description": "Parameter 1",
        },
        "param2": {
            "type": "integer",
            "description": "Parameter 2",
        },
    },
    required=["param1"],
    category=ToolCategory.CUSTOM,
    tags=["custom", "example"],
)
def my_tool(param1, param2=None):
    # Tool implementation
    return ToolResult(
        data={
            "result": "success",
            "param1": param1,
            "param2": param2,
        }
    )
```

### Tool Categories

Tools are organized into categories based on their functionality:

- `CODE`: Tools for working with code (search, edit, execute)
- `WEB`: Tools for working with the web (search, fetch)
- `FILESYSTEM`: Tools for working with the filesystem (list, create, delete)
- `UTILS`: Utility tools (time, random, UUID)
- `CUSTOM`: Custom tools defined by the user

### Tool Metadata

Each tool has associated metadata that describes its purpose, parameters, and other attributes:

- `id`: Unique identifier for the tool
- `name`: Display name for the tool
- `description`: Description of what the tool does
- `category`: Category of the tool
- `version`: Version of the tool
- `author`: Author of the tool
- `tags`: Tags for categorizing the tool
- `documentation_url`: URL to the tool's documentation

## Available Tools

### Code Tools

#### Search Tools

- `code_search`: Search for code in the workspace using a query string
- `code_semantic_search`: Search for code semantically using natural language
- `find_definition`: Find the definition of a symbol in the codebase

#### Edit Tools

- `read_file`: Read the contents of a file
- `write_file`: Write content to a file
- `edit_file`: Edit a specific part of a file
- `create_file`: Create a new file with the specified content
- `delete_file`: Delete a file

#### Execute Tools

- `execute_python`: Execute Python code and return the result
- `execute_shell`: Execute a shell command and return the result
- `run_tests`: Run tests for a project
- `execute_code_snippet`: Execute a code snippet in a specific language

### Web Tools

- `web_search`: Search the web for information
- `fetch_webpage`: Fetch the content of a webpage
- `search_wikipedia`: Search Wikipedia for information

### Filesystem Tools

- `list_directory`: List files and directories in a directory
- `create_directory`: Create a new directory
- `delete_directory`: Delete a directory
- `copy_file`: Copy a file from source to destination
- `move_file`: Move a file from source to destination

### Utility Tools

- `get_current_time`: Get the current date and time
- `generate_random_string`: Generate a random string
- `generate_uuid`: Generate a UUID
- `get_system_info`: Get information about the system
- `parse_json`: Parse a JSON string
- `format_json`: Format a JSON string

## Integration with Parlant

The tool integration system is integrated with the Parlant framework:

1. **Core Engine**: The core engine uses tools to perform actions
2. **Agents**: Agents use tools to interact with the environment
3. **Prompt System**: The prompt system includes tool descriptions and examples
4. **MCP**: The MCP uses tools to execute actions

## Future Enhancements

Future enhancements to the tool integration system may include:

1. **Tool Versioning**: Track changes to tools over time
2. **Tool Testing**: Test tools with different arguments
3. **Tool Optimization**: Optimize tools for different environments
4. **Tool Sharing**: Share tools between Parlant instances
5. **Tool Marketplace**: Discover and use tools from a marketplace
