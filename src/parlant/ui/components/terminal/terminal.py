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

"""Interactive terminal component."""

import asyncio
import os
import re
import shlex
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Set, Tuple, Union

from Daneel.core.loggers import Logger


class TerminalState(str, Enum):
    """Terminal states."""
    
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class TerminalOptions:
    """Options for the terminal component."""
    
    prompt: str = "$ "
    initial_content: str = ""
    max_height: int = 300
    title: str = "Terminal"
    read_only: bool = False
    auto_focus: bool = False
    theme: str = "dark"
    show_copy_button: bool = True
    show_clear_button: bool = True
    show_fullscreen_button: bool = True
    history_size: int = 100
    working_directory: Optional[str] = None


@dataclass
class TerminalHistoryEntry:
    """A history entry in the terminal."""
    
    command: str
    output: str
    timestamp: float = field(default_factory=time.time)


class Terminal:
    """Interactive terminal component."""
    
    def __init__(self, logger: Logger):
        """Initialize the terminal component.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.history: List[TerminalHistoryEntry] = []
        self.state = TerminalState.IDLE
        self.process: Optional[subprocess.Popen] = None
        self.working_directory = os.getcwd()
        self.command_history: List[str] = []
        self.command_handlers: Dict[str, Callable[[str], str]] = {}
        
    def register_command_handler(self, command: str, handler: Callable[[str], str]) -> None:
        """Register a handler for a specific command.
        
        Args:
            command: Command to handle
            handler: Function to handle the command
        """
        self.command_handlers[command] = handler
        
    def set_working_directory(self, directory: str) -> None:
        """Set the working directory for the terminal.
        
        Args:
            directory: Working directory
        """
        if os.path.isdir(directory):
            self.working_directory = directory
        else:
            self.logger.warning(f"Directory not found: {directory}")
            
    def add_to_history(self, command: str, output: str) -> None:
        """Add a command and its output to the history.
        
        Args:
            command: Command that was executed
            output: Output of the command
        """
        self.history.append(TerminalHistoryEntry(command=command, output=output))
        
        # Add to command history if not empty and not a duplicate
        if command and (not self.command_history or self.command_history[-1] != command):
            self.command_history.append(command)
            
            # Trim command history if it gets too long
            if len(self.command_history) > 100:
                self.command_history = self.command_history[-100:]
                
    def clear_history(self) -> None:
        """Clear the terminal history."""
        self.history = []
        
    def get_history_text(self) -> str:
        """Get the terminal history as text.
        
        Returns:
            Terminal history as text
        """
        lines = []
        for entry in self.history:
            if entry.command:
                lines.append(f"$ {entry.command}")
            if entry.output:
                lines.append(entry.output)
        return "\n".join(lines)
        
    async def execute_command(self, command: str) -> str:
        """Execute a command in the terminal.
        
        Args:
            command: Command to execute
            
        Returns:
            Output of the command
        """
        if not command.strip():
            return ""
            
        # Check for built-in commands
        if command.strip() == "clear":
            self.clear_history()
            return ""
        elif command.strip() == "exit":
            return "Terminal session ended"
        elif command.strip().startswith("cd "):
            # Handle cd command
            directory = command.strip()[3:].strip()
            
            # Handle home directory
            if directory == "~":
                directory = os.path.expanduser("~")
            elif directory.startswith("~/"):
                directory = os.path.expanduser("~") + directory[1:]
                
            # Handle relative paths
            if not os.path.isabs(directory):
                directory = os.path.join(self.working_directory, directory)
                
            # Check if directory exists
            if os.path.isdir(directory):
                self.working_directory = directory
                return f"Changed directory to {directory}"
            else:
                return f"Directory not found: {directory}"
                
        # Check for registered command handlers
        cmd = command.split()[0] if command.split() else ""
        if cmd in self.command_handlers:
            try:
                return self.command_handlers[cmd](command)
            except Exception as e:
                self.logger.error(f"Error handling command {cmd}: {e}")
                return f"Error: {str(e)}"
                
        # Execute the command in a subprocess
        try:
            self.state = TerminalState.RUNNING
            
            # Create the process
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_directory,
                shell=True,
            )
            
            self.process = process
            
            # Wait for the process to complete
            stdout, stderr = await process.communicate()
            
            # Decode the output
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")
            
            # Combine stdout and stderr
            output = stdout_str
            if stderr_str:
                if output:
                    output += "\n"
                output += stderr_str
                
            self.state = TerminalState.IDLE
            self.process = None
            
            return output
        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            self.state = TerminalState.ERROR
            self.process = None
            return f"Error: {str(e)}"
            
    def interrupt_command(self) -> None:
        """Interrupt the currently running command."""
        if self.state == TerminalState.RUNNING and self.process:
            try:
                # Send SIGINT to the process
                self.process.send_signal(signal.SIGINT)
            except Exception as e:
                self.logger.error(f"Error interrupting command: {e}")
                
    def render_html(self, options: Optional[TerminalOptions] = None) -> str:
        """Render the terminal as HTML.
        
        Args:
            options: Options for rendering
            
        Returns:
            HTML representation of the terminal
        """
        if options is None:
            options = TerminalOptions()
            
        # Set working directory if specified
        if options.working_directory:
            self.set_working_directory(options.working_directory)
            
        # Add initial content if specified and history is empty
        if options.initial_content and not self.history:
            self.add_to_history("", options.initial_content)
            
        # Build the HTML
        html = []
        
        # Terminal container
        theme_class = "Daneel-terminal-dark" if options.theme == "dark" else "Daneel-terminal-light"
        html.append(f'<div class="Daneel-terminal-container {theme_class}">')
        
        # Terminal header
        html.append('<div class="Daneel-terminal-header">')
        html.append(f'<div class="Daneel-terminal-title">{options.title}</div>')
        
        # Terminal buttons
        html.append('<div class="Daneel-terminal-buttons">')
        
        if options.show_copy_button:
            html.append('<button class="Daneel-terminal-button Daneel-terminal-copy-button" title="Copy terminal content">Copy</button>')
            
        if options.show_clear_button:
            html.append('<button class="Daneel-terminal-button Daneel-terminal-clear-button" title="Clear terminal">Clear</button>')
            
        if options.show_fullscreen_button:
            html.append('<button class="Daneel-terminal-button Daneel-terminal-fullscreen-button" title="Toggle fullscreen">Fullscreen</button>')
            
        html.append('</div>')  # End buttons
        html.append('</div>')  # End header
        
        # Terminal content
        max_height_style = f'style="max-height: {options.max_height}px;"' if options.max_height > 0 else ''
        html.append(f'<div class="Daneel-terminal-content" {max_height_style}>')
        
        # Terminal history
        html.append('<div class="Daneel-terminal-history">')
        
        for entry in self.history:
            if entry.command:
                html.append(f'<div class="Daneel-terminal-command"><span class="Daneel-terminal-prompt">{options.prompt}</span>{entry.command}</div>')
                
            if entry.output:
                # Apply simple syntax highlighting to the output
                highlighted_output = self._highlight_terminal_output(entry.output)
                html.append(f'<div class="Daneel-terminal-output">{highlighted_output}</div>')
                
        html.append('</div>')  # End history
        
        # Terminal input
        if not options.read_only:
            auto_focus = 'autofocus' if options.auto_focus else ''
            html.append('<div class="Daneel-terminal-input-line">')
            html.append(f'<span class="Daneel-terminal-prompt">{options.prompt}</span>')
            html.append(f'<input type="text" class="Daneel-terminal-input" {auto_focus}>')
            html.append('</div>')  # End input line
            
        html.append('</div>')  # End content
        html.append('</div>')  # End container
        
        return "\n".join(html)
        
    def _highlight_terminal_output(self, output: str) -> str:
        """Apply simple syntax highlighting to terminal output.
        
        Args:
            output: Terminal output to highlight
            
        Returns:
            Highlighted terminal output
        """
        # Split the output into lines
        lines = output.splitlines()
        highlighted_lines = []
        
        for line in lines:
            # Highlight error messages
            if re.search(r'error|exception|traceback|fail', line, re.IGNORECASE):
                highlighted_lines.append(f'<span class="Daneel-terminal-error">{line}</span>')
            # Highlight warning messages
            elif re.search(r'warning|warn', line, re.IGNORECASE):
                highlighted_lines.append(f'<span class="Daneel-terminal-warning">{line}</span>')
            # Highlight success messages
            elif re.search(r'success|succeeded|completed|done', line, re.IGNORECASE):
                highlighted_lines.append(f'<span class="Daneel-terminal-success">{line}</span>')
            # Highlight file paths
            elif re.search(r'[/\\][a-zA-Z0-9_.-]+[/\\][a-zA-Z0-9_.-]+', line):
                # This is a simple regex for file paths, might need improvement
                highlighted_lines.append(f'<span class="Daneel-terminal-path">{line}</span>')
            else:
                highlighted_lines.append(line)
                
        return "<br>".join(highlighted_lines)
        
    def get_css(self) -> str:
        """Get the CSS for the terminal component.
        
        Returns:
            CSS for the terminal component
        """
        css = """
        .Daneel-terminal-container {
            border: 1px solid #e2e8f0;
            border-radius: 0.375rem;
            margin: 1rem 0;
            overflow: hidden;
            font-family: monospace;
            font-size: 0.875rem;
        }
        
        .Daneel-terminal-dark {
            background-color: #1e293b;
            color: #e2e8f0;
        }
        
        .Daneel-terminal-light {
            background-color: #f8fafc;
            color: #1e293b;
        }
        
        .Daneel-terminal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 1rem;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .Daneel-terminal-dark .Daneel-terminal-header {
            background-color: #0f172a;
            border-bottom-color: #334155;
        }
        
        .Daneel-terminal-light .Daneel-terminal-header {
            background-color: #e2e8f0;
            border-bottom-color: #cbd5e1;
        }
        
        .Daneel-terminal-title {
            font-weight: 500;
        }
        
        .Daneel-terminal-buttons {
            display: flex;
            gap: 0.5rem;
        }
        
        .Daneel-terminal-button {
            background-color: transparent;
            border: 1px solid #64748b;
            border-radius: 0.25rem;
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
            cursor: pointer;
            color: inherit;
        }
        
        .Daneel-terminal-dark .Daneel-terminal-button {
            border-color: #475569;
        }
        
        .Daneel-terminal-light .Daneel-terminal-button {
            border-color: #94a3b8;
        }
        
        .Daneel-terminal-button:hover {
            background-color: rgba(100, 116, 139, 0.1);
        }
        
        .Daneel-terminal-content {
            padding: 0.5rem;
            overflow: auto;
            min-height: 200px;
        }
        
        .Daneel-terminal-history {
            white-space: pre-wrap;
            word-break: break-word;
        }
        
        .Daneel-terminal-command {
            margin-bottom: 0.25rem;
        }
        
        .Daneel-terminal-output {
            margin-bottom: 0.5rem;
        }
        
        .Daneel-terminal-prompt {
            color: #3b82f6;
            margin-right: 0.25rem;
        }
        
        .Daneel-terminal-dark .Daneel-terminal-prompt {
            color: #60a5fa;
        }
        
        .Daneel-terminal-light .Daneel-terminal-prompt {
            color: #2563eb;
        }
        
        .Daneel-terminal-input-line {
            display: flex;
            align-items: center;
            margin-top: 0.5rem;
        }
        
        .Daneel-terminal-input {
            flex: 1;
            background-color: transparent;
            border: none;
            outline: none;
            color: inherit;
            font-family: inherit;
            font-size: inherit;
        }
        
        .Daneel-terminal-error {
            color: #ef4444;
        }
        
        .Daneel-terminal-warning {
            color: #f59e0b;
        }
        
        .Daneel-terminal-success {
            color: #10b981;
        }
        
        .Daneel-terminal-path {
            color: #8b5cf6;
        }
        
        .Daneel-terminal-dark .Daneel-terminal-error {
            color: #f87171;
        }
        
        .Daneel-terminal-dark .Daneel-terminal-warning {
            color: #fbbf24;
        }
        
        .Daneel-terminal-dark .Daneel-terminal-success {
            color: #34d399;
        }
        
        .Daneel-terminal-dark .Daneel-terminal-path {
            color: #a78bfa;
        }
        
        /* Fullscreen mode */
        .Daneel-terminal-fullscreen {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 9999;
            border-radius: 0;
            margin: 0;
        }
        
        .Daneel-terminal-fullscreen .Daneel-terminal-content {
            height: calc(100vh - 40px);
            max-height: none !important;
        }
        """
        
        return css
