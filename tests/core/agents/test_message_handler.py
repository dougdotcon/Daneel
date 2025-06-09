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

"""Tests for the message handler."""

import json
import pytest
from unittest.mock import MagicMock

from Daneel.core.agents.utils import Message, MessageHandler


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    return logger


@pytest.fixture
def message_handler(mock_logger):
    """Create a message handler."""
    return MessageHandler(logger=mock_logger)


class TestMessageHandler:
    """Tests for the message handler."""
    
    def test_parse_message(self, message_handler):
        """Test parsing a message."""
        # Parse a user message
        message = message_handler.parse_message("Hello, world!")
        assert message.role == "user"
        assert message.content == "Hello, world!"
        
        # Parse a message with a role prefix
        message = message_handler.parse_message("system: This is a system message")
        assert message.role == "system"
        assert message.content == "This is a system message"
        
        # Parse a message with a different role prefix
        message = message_handler.parse_message("assistant: This is an assistant message")
        assert message.role == "assistant"
        assert message.content == "This is an assistant message"
        
        # Parse a message with a tool role prefix
        message = message_handler.parse_message("tool: This is a tool message")
        assert message.role == "tool"
        assert message.content == "This is a tool message"
        
    def test_format_message(self, message_handler):
        """Test formatting a message."""
        # Format a user message
        message = Message(role="user", content="Hello, world!")
        formatted = message_handler.format_message(message)
        assert formatted == "user: Hello, world!"
        
        # Format a system message
        message = Message(role="system", content="This is a system message")
        formatted = message_handler.format_message(message)
        assert formatted == "system: This is a system message"
        
        # Format a tool message
        message = Message(role="tool", content="This is a tool message", tool_call_id="call_1")
        formatted = message_handler.format_message(message)
        assert formatted == "tool (call_1): This is a tool message"
        
        # Format a message with tool calls
        message = Message(
            role="assistant",
            content="I'll help you with that",
            tool_calls=[
                {
                    "id": "call_1",
                    "function": {
                        "name": "search",
                        "arguments": json.dumps({"query": "test"}),
                    },
                },
            ],
        )
        formatted = message_handler.format_message(message)
        assert "assistant: I'll help you with that" in formatted
        assert "Tool calls: search({\"query\": \"test\"})" in formatted
        
        # Format a message with only tool calls
        message = Message(
            role="assistant",
            tool_calls=[
                {
                    "id": "call_1",
                    "function": {
                        "name": "search",
                        "arguments": json.dumps({"query": "test"}),
                    },
                },
            ],
        )
        formatted = message_handler.format_message(message)
        assert "assistant: Tool calls: search({\"query\": \"test\"})" in formatted
        
    def test_extract_code_blocks(self, message_handler):
        """Test extracting code blocks."""
        # Extract code blocks with language
        content = """
Here's some Python code:
```python
print("Hello, world!")
```

And here's some JavaScript:
```javascript
console.log("Hello, world!");
```
"""
        code_blocks = message_handler.extract_code_blocks(content)
        assert len(code_blocks) == 2
        assert code_blocks[0] == ("python", 'print("Hello, world!")')
        assert code_blocks[1] == ("javascript", 'console.log("Hello, world!");')
        
        # Extract code blocks without language
        content = """
Here's some code:
```
print("Hello, world!")
```
"""
        code_blocks = message_handler.extract_code_blocks(content)
        assert len(code_blocks) == 1
        assert code_blocks[0] == ("text", 'print("Hello, world!")')
        
    def test_extract_tool_calls(self, message_handler):
        """Test extracting tool calls."""
        # Extract function calls
        content = """
Let me search for that:
search({"query": "test"})

And let me also get the weather:
get_weather(location="New York")
"""
        tool_calls = message_handler.extract_tool_calls(content)
        assert len(tool_calls) == 2
        assert tool_calls[0]["function"]["name"] == "search"
        assert json.loads(tool_calls[0]["function"]["arguments"]) == {"query": "test"}
        assert tool_calls[1]["function"]["name"] == "get_weather"
        assert json.loads(tool_calls[1]["function"]["arguments"]) == {"location": "New York"}
        
    def test_extract_commands(self, message_handler):
        """Test extracting commands."""
        # Extract commands from bash code blocks
        content = """
Let me run some commands:
```bash
ls -la
echo "Hello, world!"
```

And here's another command:
```shell
cat file.txt
```
"""
        commands = message_handler.extract_commands(content)
        assert len(commands) == 3
        assert commands[0] == "ls -la"
        assert commands[1] == 'echo "Hello, world!"'
        assert commands[2] == "cat file.txt"
        
        # Extract commands from code blocks without language
        content = """
Let me run a command:
```
ls -la
```
"""
        commands = message_handler.extract_commands(content)
        assert len(commands) == 1
        assert commands[0] == "ls -la"
