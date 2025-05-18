# Agent System

This document describes the agent system in the Parlant framework.

## Overview

The agent system provides a way to create, manage, and use agents in Parlant. It supports:

1. Different types of agents (CLI, terminal, web)
2. Agent configuration and context
3. Agent state management
4. Secure code execution through sandboxing
5. Message handling and formatting

## Components

### AgentSystem

The `AgentSystem` class is the base class for all agent implementations. It provides common functionality for:

- Initializing agents
- Running agents with instructions
- Managing agent state (running, paused, stopped)
- Handling interruptions
- Cleaning up resources

Example usage:

```python
from parlant.core.agents import AgentConfig, AgentType
from parlant.core.agents.cli import CLIAgent
from parlant.core.loggers import ConsoleLogger

# Create an agent configuration
config = AgentConfig(
    agent_type=AgentType.CLI,
    name="My CLI Agent",
    description="A CLI agent for coding tasks",
    model_id="gpt-4",
    tools=["code_search", "read_file", "write_file"],
    prompts=["cli_agent_prompt"],
)

# Create a CLI agent
agent = CLIAgent(
    agent_id="agent1",
    config=config,
    logger=ConsoleLogger(),
    model_manager=model_manager,
    prompt_manager=prompt_manager,
    tool_registry=tool_registry,
    agent_store=agent_store,
)

# Initialize the agent
await agent.initialize()

# Run the agent with an instruction
result = await agent.run("Find all functions in the codebase that handle user authentication")

# Stop the agent
await agent.stop()

# Clean up resources
await agent.cleanup()
```

### AgentSystemFactory

The `AgentSystemFactory` class provides a way to create agents of different types. It supports:

- Registering agent system types
- Creating agents with configurations
- Managing agent dependencies

Example usage:

```python
from parlant.core.agents import AgentConfig, AgentSystemFactory, AgentType
from parlant.core.agents.cli import CLIAgent
from parlant.core.agents.terminal import TerminalAgent
from parlant.core.loggers import ConsoleLogger

# Create a factory
factory = AgentSystemFactory(
    logger=ConsoleLogger(),
    model_manager=model_manager,
    prompt_manager=prompt_manager,
    tool_registry=tool_registry,
    agent_store=agent_store,
)

# Register agent system types
factory.register_agent_system_type(AgentType.CLI, CLIAgent)
factory.register_agent_system_type(AgentType.TERMINAL, TerminalAgent)

# Create a CLI agent
cli_config = AgentConfig(
    agent_type=AgentType.CLI,
    name="My CLI Agent",
    description="A CLI agent for coding tasks",
    model_id="gpt-4",
)
cli_agent = await factory.create_agent_system("agent1", cli_config)

# Create a terminal agent
terminal_config = AgentConfig(
    agent_type=AgentType.TERMINAL,
    name="My Terminal Agent",
    description="A terminal agent for shell tasks",
    model_id="gpt-4",
)
terminal_agent = await factory.create_agent_system("agent2", terminal_config)
```

### CLIAgent

The `CLIAgent` class implements a command-line interface agent. It supports:

- Processing user instructions
- Calling tools to perform actions
- Generating responses
- Managing conversation history

Example usage:

```python
from parlant.core.agents import AgentConfig, AgentType
from parlant.core.agents.cli import CLIAgent
from parlant.core.loggers import ConsoleLogger

# Create a CLI agent
agent = CLIAgent(
    agent_id="agent1",
    config=AgentConfig(
        agent_type=AgentType.CLI,
        name="My CLI Agent",
        description="A CLI agent for coding tasks",
        model_id="gpt-4",
    ),
    logger=ConsoleLogger(),
    model_manager=model_manager,
    prompt_manager=prompt_manager,
    tool_registry=tool_registry,
    agent_store=agent_store,
)

# Initialize the agent
await agent.initialize()

# Run the agent with an instruction
result = await agent.run("Find all functions in the codebase that handle user authentication")
print(result)
```

### TerminalAgent

The `TerminalAgent` class implements a terminal-based agent. It supports:

- Interacting with a terminal session
- Executing commands in the terminal
- Reading terminal output
- Managing terminal state

Example usage:

```python
from parlant.core.agents import AgentConfig, AgentType
from parlant.core.agents.terminal import TerminalAgent
from parlant.core.loggers import ConsoleLogger

# Create a terminal agent
agent = TerminalAgent(
    agent_id="agent1",
    config=AgentConfig(
        agent_type=AgentType.TERMINAL,
        name="My Terminal Agent",
        description="A terminal agent for shell tasks",
        model_id="gpt-4",
    ),
    logger=ConsoleLogger(),
    model_manager=model_manager,
    prompt_manager=prompt_manager,
    tool_registry=tool_registry,
    agent_store=agent_store,
)

# Initialize the agent
await agent.initialize()

# Run the agent with an instruction
result = await agent.run("List all files in the current directory and find the largest one")
print(result)
```

### Sandbox

The `Sandbox` class provides a secure environment for executing code. It supports:

- Local and Docker-based sandboxes
- Command execution
- File execution
- Resource cleanup

Example usage:

```python
from parlant.core.agents.sandbox import SandboxConfig, SandboxFactory
from parlant.core.loggers import ConsoleLogger

# Create a sandbox factory
factory = SandboxFactory(logger=ConsoleLogger())

# Create a sandbox configuration
config = SandboxConfig(
    workspace_dir="/path/to/workspace",
    allowed_commands=["echo", "ls", "cat"],
    blocked_commands=["rm", "mv", "cp"],
    timeout_seconds=5,
    max_output_size=1000,
)

# Create a local sandbox
sandbox = await factory.create_sandbox(config, "local")

# Execute a command
exit_code, stdout, stderr = await sandbox.execute_command("echo 'Hello, world!'")
print(f"Exit code: {exit_code}")
print(f"Output: {stdout}")
print(f"Error: {stderr}")

# Execute a file
exit_code, stdout, stderr = await sandbox.execute_file("script.py")
print(f"Exit code: {exit_code}")
print(f"Output: {stdout}")
print(f"Error: {stderr}")

# Clean up the sandbox
await sandbox.cleanup()
```

### MessageHandler

The `MessageHandler` class provides utilities for handling messages in agent systems. It supports:

- Parsing messages
- Formatting messages
- Extracting code blocks
- Extracting tool calls
- Extracting commands

Example usage:

```python
from parlant.core.agents.utils import Message, MessageHandler
from parlant.core.loggers import ConsoleLogger

# Create a message handler
handler = MessageHandler(logger=ConsoleLogger())

# Parse a message
message = handler.parse_message("user: Hello, world!")
print(f"Role: {message.role}")
print(f"Content: {message.content}")

# Format a message
formatted = handler.format_message(Message(role="assistant", content="I'll help you with that"))
print(formatted)

# Extract code blocks
code_blocks = handler.extract_code_blocks("""
Here's some Python code:
```python
print("Hello, world!")
```
""")
for language, code in code_blocks:
    print(f"Language: {language}")
    print(f"Code: {code}")

# Extract commands
commands = handler.extract_commands("""
Let me run some commands:
```bash
ls -la
echo "Hello, world!"
```
""")
for command in commands:
    print(f"Command: {command}")
```

## Agent Types

Agents are organized into types based on their functionality:

- `CLI`: Command-line interface agents
- `TERMINAL`: Terminal-based agents
- `WEB`: Web-based agents
- `CUSTOM`: Custom agent types

## Agent States

Agents can be in different states:

- `IDLE`: The agent is idle and ready to run
- `RUNNING`: The agent is currently running
- `PAUSED`: The agent is paused
- `STOPPED`: The agent is stopped
- `ERROR`: The agent encountered an error

## Integration with Parlant

The agent system is integrated with the Parlant framework:

1. **Core Engine**: The core engine uses agents to perform tasks
2. **Models**: Agents use models to generate responses
3. **Prompts**: Agents use prompts for their behavior
4. **Tools**: Agents use tools to perform actions

## Future Enhancements

Future enhancements to the agent system may include:

1. **Agent Collaboration**: Enable agents to collaborate on tasks
2. **Agent Learning**: Allow agents to learn from their interactions
3. **Agent Customization**: Provide more ways to customize agent behavior
4. **Agent Monitoring**: Improve monitoring and debugging of agents
5. **Agent Marketplace**: Discover and use agents from a marketplace
