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

"""Tests for terminal UI components."""

import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from parlant.ui.components.terminal import Terminal, TerminalOptions, TerminalState


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    return logger


class TestTerminal:
    """Tests for the Terminal component."""
    
    def test_add_to_history(self, mock_logger):
        """Test adding to history."""
        terminal = Terminal(mock_logger)
        
        # Add a command and output to history
        terminal.add_to_history("echo Hello", "Hello")
        
        # Check that the history was updated
        assert len(terminal.history) == 1
        assert terminal.history[0].command == "echo Hello"
        assert terminal.history[0].output == "Hello"
        
        # Check that the command history was updated
        assert len(terminal.command_history) == 1
        assert terminal.command_history[0] == "echo Hello"
        
    def test_clear_history(self, mock_logger):
        """Test clearing history."""
        terminal = Terminal(mock_logger)
        
        # Add some history
        terminal.add_to_history("echo Hello", "Hello")
        terminal.add_to_history("ls", "file1\nfile2")
        
        # Clear the history
        terminal.clear_history()
        
        # Check that the history was cleared
        assert len(terminal.history) == 0
        
    def test_get_history_text(self, mock_logger):
        """Test getting history as text."""
        terminal = Terminal(mock_logger)
        
        # Add some history
        terminal.add_to_history("echo Hello", "Hello")
        terminal.add_to_history("ls", "file1\nfile2")
        
        # Get the history text
        history_text = terminal.get_history_text()
        
        # Check that the history text is correct
        assert "$ echo Hello" in history_text
        assert "Hello" in history_text
        assert "$ ls" in history_text
        assert "file1" in history_text
        assert "file2" in history_text
        
    @pytest.mark.asyncio
    async def test_execute_command_clear(self, mock_logger):
        """Test executing the clear command."""
        terminal = Terminal(mock_logger)
        
        # Add some history
        terminal.add_to_history("echo Hello", "Hello")
        
        # Execute the clear command
        output = await terminal.execute_command("clear")
        
        # Check that the history was cleared
        assert len(terminal.history) == 0
        assert output == ""
        
    @pytest.mark.asyncio
    async def test_execute_command_cd(self, mock_logger):
        """Test executing the cd command."""
        terminal = Terminal(mock_logger)
        
        # Get the current directory
        current_dir = os.getcwd()
        parent_dir = os.path.dirname(current_dir)
        
        # Execute the cd command
        output = await terminal.execute_command(f"cd {parent_dir}")
        
        # Check that the working directory was changed
        assert terminal.working_directory == parent_dir
        assert "Changed directory" in output
        
    @pytest.mark.asyncio
    async def test_execute_command_with_handler(self, mock_logger):
        """Test executing a command with a registered handler."""
        terminal = Terminal(mock_logger)
        
        # Register a command handler
        def handle_hello(command):
            return "Hello, world!"
            
        terminal.register_command_handler("hello", handle_hello)
        
        # Execute the command
        output = await terminal.execute_command("hello")
        
        # Check that the handler was called
        assert output == "Hello, world!"
        
    @pytest.mark.asyncio
    async def test_execute_command_subprocess(self, mock_logger):
        """Test executing a command in a subprocess."""
        terminal = Terminal(mock_logger)
        
        # Mock the subprocess
        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(return_value=(b"Hello, world!", b""))
        
        with patch("asyncio.create_subprocess_shell", AsyncMock(return_value=mock_process)):
            # Execute the command
            output = await terminal.execute_command("echo Hello, world!")
            
            # Check that the command was executed
            assert output == "Hello, world!"
            assert terminal.state == TerminalState.IDLE
            
    def test_render_html(self, mock_logger):
        """Test HTML rendering."""
        terminal = Terminal(mock_logger)
        options = TerminalOptions(
            prompt="$ ",
            initial_content="Welcome to the terminal!",
            title="Test Terminal",
            theme="dark",
        )
        
        # Add some history
        terminal.add_to_history("echo Hello", "Hello")
        
        # Render the HTML
        html = terminal.render_html(options)
        
        # Check that the HTML contains the expected elements
        assert "parlant-terminal-container" in html
        assert "parlant-terminal-dark" in html
        assert "parlant-terminal-header" in html
        assert "parlant-terminal-title" in html
        assert "parlant-terminal-buttons" in html
        assert "parlant-terminal-content" in html
        assert "parlant-terminal-history" in html
        assert "parlant-terminal-command" in html
        assert "parlant-terminal-output" in html
        assert "parlant-terminal-input-line" in html
        assert "parlant-terminal-prompt" in html
        assert "parlant-terminal-input" in html
        assert "Test Terminal" in html
        assert "$ echo Hello" in html
        assert "Hello" in html
        
    def test_highlight_terminal_output(self, mock_logger):
        """Test terminal output highlighting."""
        terminal = Terminal(mock_logger)
        
        # Test highlighting error messages
        output = "Error: Something went wrong"
        highlighted = terminal._highlight_terminal_output(output)
        assert "parlant-terminal-error" in highlighted
        
        # Test highlighting warning messages
        output = "Warning: This is a warning"
        highlighted = terminal._highlight_terminal_output(output)
        assert "parlant-terminal-warning" in highlighted
        
        # Test highlighting success messages
        output = "Success: Operation completed"
        highlighted = terminal._highlight_terminal_output(output)
        assert "parlant-terminal-success" in highlighted
        
        # Test highlighting file paths
        output = "/path/to/file.txt"
        highlighted = terminal._highlight_terminal_output(output)
        assert "parlant-terminal-path" in highlighted
        
    def test_get_css(self, mock_logger):
        """Test CSS generation."""
        terminal = Terminal(mock_logger)
        css = terminal.get_css()
        
        # Check that the CSS contains the expected selectors
        assert ".parlant-terminal-container" in css
        assert ".parlant-terminal-dark" in css
        assert ".parlant-terminal-light" in css
        assert ".parlant-terminal-header" in css
        assert ".parlant-terminal-title" in css
        assert ".parlant-terminal-buttons" in css
        assert ".parlant-terminal-button" in css
        assert ".parlant-terminal-content" in css
        assert ".parlant-terminal-history" in css
        assert ".parlant-terminal-command" in css
        assert ".parlant-terminal-output" in css
        assert ".parlant-terminal-prompt" in css
        assert ".parlant-terminal-input-line" in css
        assert ".parlant-terminal-input" in css
        assert ".parlant-terminal-error" in css
        assert ".parlant-terminal-warning" in css
        assert ".parlant-terminal-success" in css
        assert ".parlant-terminal-path" in css
        assert ".parlant-terminal-fullscreen" in css
