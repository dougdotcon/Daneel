# MCP (Model Context Protocol) Integration

This document describes the integration of the Model Context Protocol (MCP) into the Parlant framework.

## Overview

The Model Context Protocol (MCP) is a standardized protocol for communication between IDEs and AI agents. It allows for context sharing and tool usage, enabling AI agents to perform complex tasks by leveraging external tools and services.

Parlant now includes a complete MCP implementation, allowing it to:

1. Connect to external MCP servers to use their tools and capabilities
2. Expose its own capabilities as an MCP server for other applications to use
3. Implement specialized MCP servers like Sequential Thinking for improved reasoning

## Components

### MCPClient

The `MCPClient` class allows Parlant to connect to external MCP servers and use their tools. It handles:

- WebSocket connection management
- Tool discovery and registration
- Message sending and receiving
- Tool call execution

Example usage:

```python
from parlant.adapters.mcp import MCPClient
from parlant.core.loggers import ConsoleLogger

# Create a client
client = MCPClient(
    server_url="ws://localhost:8080",
    logger=ConsoleLogger()
)

# Connect to the server
await client.connect()

# Send a message
message = MCPMessage.user("Hello!")
response = await client.send_message(message)

# Disconnect
await client.disconnect()
```

### MCPServer

The `MCPServer` class allows Parlant to expose its capabilities as an MCP server. It handles:

- WebSocket server management
- Tool registration and discovery
- Message handling
- Tool call execution

Example usage:

```python
from parlant.adapters.mcp import MCPServer, MCPTool
from parlant.core.loggers import ConsoleLogger

# Create a server
server = MCPServer(
    host="localhost",
    port=8080,
    logger=ConsoleLogger()
)

# Register a tool
server.register_tool(
    MCPTool(
        name="echo",
        description="Echo the input",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to echo"
                }
            },
            "required": ["text"]
        },
        required_parameters=["text"]
    ),
    lambda args: {"echo": args["text"]}
)

# Set a message handler
server.set_message_handler(async_message_handler)

# Start the server
await server.start()
```

### SequentialThinkingMCP

The `SequentialThinkingMCP` class implements a specialized MCP server for sequential thinking. It allows models to:

- Generate a sequence of thoughts
- Review and refine those thoughts
- Branch hypotheses
- Make decisions based on structured reasoning

Example usage:

```python
from parlant.adapters.mcp import SequentialThinkingMCP
from parlant.core.loggers import ConsoleLogger
from parlant.adapters.nlp import OpenAIService

# Create a sequential thinking MCP
sequential_thinking = SequentialThinkingMCP(
    nlp_service=OpenAIService(...),
    logger=ConsoleLogger(),
    host="localhost",
    port=8081
)

# Start the server
await sequential_thinking.start()
```

## Integration with Parlant

The MCP integration is designed to work seamlessly with the existing Parlant architecture:

1. **Adapters Layer**: The MCP implementation lives in the adapters layer, allowing it to be used by the core components.
2. **Tools Integration**: MCP tools can be registered and used by Parlant's tool system.
3. **NLP Services**: MCP can be used with any of Parlant's NLP services.
4. **Session Management**: MCP sessions can be integrated with Parlant's session management.

## Future Enhancements

Future enhancements to the MCP integration may include:

1. **Tool Chaining**: Allow tools to be chained together for complex workflows.
2. **Tool Versioning**: Support for versioned tools and backward compatibility.
3. **Authentication**: Add authentication and authorization for MCP connections.
4. **Streaming**: Support for streaming responses from tools.
5. **Multi-modal Support**: Add support for multi-modal inputs and outputs.

## References

- [Model Context Protocol Specification](https://github.com/modelcontextprotocol/servers)
- [Sequential Thinking MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking)
- [VSCode Agent Mode with MCP](https://code.visualstudio.com/blogs/2025/04/07/agentMode)
