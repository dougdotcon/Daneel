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

"""Call stack viewer component for debugging."""

import os
import traceback
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Union

from Daneel.core.loggers import Logger
from Daneel.ui.components.code.code_block import CodeBlock, CodeBlockOptions


@dataclass
class StackFrame:
    """A frame in a call stack."""
    
    function_name: str
    file_name: str
    line_number: int
    column_number: Optional[int] = None
    source: Optional[str] = None
    is_library: bool = False
    variables: Dict[str, any] = field(default_factory=dict)


@dataclass
class CallStackOptions:
    """Options for the call stack component."""
    
    title: str = "Call Stack"
    theme: str = "default"
    max_height: int = 500
    show_library_frames: bool = False
    show_variables: bool = True
    show_source: bool = True
    context_lines: int = 3


class CallStack:
    """Call stack viewer component for debugging."""
    
    def __init__(self, logger: Logger):
        """Initialize the call stack component.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.code_block = CodeBlock(logger)
        
    def get_current_stack_frames(self) -> List[StackFrame]:
        """Get the current stack frames.
        
        Returns:
            List of stack frames
        """
        frames = []
        
        # Get the current stack
        stack = traceback.extract_stack()
        
        # Skip the last frame (this function)
        for frame_info in stack[:-1]:
            file_name, line_number, function_name, text = frame_info
            
            # Check if this is a library frame
            is_library = "/site-packages/" in file_name or "\\site-packages\\" in file_name
            
            # Create a stack frame
            frame = StackFrame(
                function_name=function_name,
                file_name=file_name,
                line_number=line_number,
                source=text,
                is_library=is_library,
            )
            
            frames.append(frame)
            
        return frames
        
    def get_exception_stack_frames(self, exception: Exception) -> List[StackFrame]:
        """Get stack frames from an exception.
        
        Args:
            exception: Exception to get stack frames from
            
        Returns:
            List of stack frames
        """
        frames = []
        
        # Get the traceback
        tb = traceback.extract_tb(exception.__traceback__)
        
        for frame_info in tb:
            file_name, line_number, function_name, text = frame_info
            
            # Check if this is a library frame
            is_library = "/site-packages/" in file_name or "\\site-packages\\" in file_name
            
            # Create a stack frame
            frame = StackFrame(
                function_name=function_name,
                file_name=file_name,
                line_number=line_number,
                source=text,
                is_library=is_library,
            )
            
            frames.append(frame)
            
        return frames
        
    def get_source_code(self, file_name: str, line_number: int, context_lines: int = 3) -> Optional[str]:
        """Get source code from a file.
        
        Args:
            file_name: File to get source code from
            line_number: Line number to get source code around
            context_lines: Number of context lines to include
            
        Returns:
            Source code, or None if the file couldn't be read
        """
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            # Calculate the range of lines to include
            start_line = max(0, line_number - context_lines - 1)
            end_line = min(len(lines), line_number + context_lines)
            
            # Extract the lines
            source_lines = lines[start_line:end_line]
            
            return "".join(source_lines)
        except Exception as e:
            self.logger.warning(f"Error reading source code from {file_name}: {e}")
            return None
            
    def render_frame(self, frame: StackFrame, index: int, is_selected: bool, options: CallStackOptions) -> str:
        """Render a stack frame as HTML.
        
        Args:
            frame: Stack frame to render
            index: Index of the frame
            is_selected: Whether the frame is selected
            options: Options for rendering
            
        Returns:
            HTML representation of the stack frame
        """
        # Get the file name without the path
        file_name = os.path.basename(frame.file_name)
        
        # Create the HTML
        html = []
        
        # Frame container
        selected_class = "Daneel-call-stack-frame-selected" if is_selected else ""
        library_class = "Daneel-call-stack-frame-library" if frame.is_library else ""
        html.append(f'<div class="Daneel-call-stack-frame {selected_class} {library_class}" data-index="{index}">')
        
        # Frame header
        html.append('<div class="Daneel-call-stack-frame-header">')
        
        # Function name
        html.append(f'<div class="Daneel-call-stack-function-name">{frame.function_name or "<anonymous>"}</div>')
        
        # File and line
        location = f"{file_name}:{frame.line_number}"
        if frame.column_number is not None:
            location += f":{frame.column_number}"
            
        html.append(f'<div class="Daneel-call-stack-location">{location}</div>')
        
        html.append('</div>')  # End frame header
        
        # Frame details (only shown if selected)
        if is_selected:
            html.append('<div class="Daneel-call-stack-frame-details">')
            
            # Source code
            if options.show_source and frame.source:
                html.append('<div class="Daneel-call-stack-source">')
                html.append('<div class="Daneel-call-stack-section-title">Source</div>')
                
                # Get the source code with context
                source = frame.source
                if not source and os.path.isfile(frame.file_name):
                    source = self.get_source_code(frame.file_name, frame.line_number, options.context_lines)
                    
                if source:
                    # Render the source code with syntax highlighting
                    code_options = CodeBlockOptions(
                        language=None,  # Auto-detect
                        show_line_numbers=True,
                        show_copy_button=True,
                        show_collapse_button=False,
                        max_height=200,
                        file_name=None,
                        highlight_lines=[frame.line_number],
                        theme=options.theme,
                        line_start=max(1, frame.line_number - options.context_lines),
                    )
                    
                    html.append(self.code_block.render_html(source, code_options))
                else:
                    html.append('<div class="Daneel-call-stack-no-source">Source code not available</div>')
                    
                html.append('</div>')  # End source
                
            # Variables
            if options.show_variables and frame.variables:
                html.append('<div class="Daneel-call-stack-variables">')
                html.append('<div class="Daneel-call-stack-section-title">Local Variables</div>')
                
                html.append('<div class="Daneel-call-stack-variables-list">')
                for name, value in frame.variables.items():
                    html.append('<div class="Daneel-call-stack-variable">')
                    html.append(f'<div class="Daneel-call-stack-variable-name">{name}</div>')
                    
                    # Format the value based on its type
                    if isinstance(value, str):
                        formatted_value = f'"{value}"'
                        value_class = "Daneel-call-stack-string"
                    elif isinstance(value, (int, float)):
                        formatted_value = str(value)
                        value_class = "Daneel-call-stack-number"
                    elif isinstance(value, bool):
                        formatted_value = str(value).lower()
                        value_class = "Daneel-call-stack-boolean"
                    elif value is None:
                        formatted_value = "null"
                        value_class = "Daneel-call-stack-null"
                    elif isinstance(value, list):
                        formatted_value = f"Array({len(value)})"
                        value_class = ""
                    elif isinstance(value, dict):
                        formatted_value = f"Object {{{', '.join(value.keys())}}}"
                        value_class = ""
                    else:
                        formatted_value = str(value)
                        value_class = ""
                        
                    html.append(f'<div class="Daneel-call-stack-variable-value {value_class}">{formatted_value}</div>')
                    html.append('</div>')  # End variable
                    
                html.append('</div>')  # End variables list
                html.append('</div>')  # End variables
                
            html.append('</div>')  # End frame details
            
        html.append('</div>')  # End frame
        
        return "\n".join(html)
        
    def render_html(self, frames: List[StackFrame], options: Optional[CallStackOptions] = None) -> str:
        """Render the call stack as HTML.
        
        Args:
            frames: Stack frames to render
            options: Options for rendering
            
        Returns:
            HTML representation of the call stack
        """
        if options is None:
            options = CallStackOptions()
            
        # Filter out library frames if not showing them
        if not options.show_library_frames:
            frames = [frame for frame in frames if not frame.is_library]
            
        # Add container
        html = []
        
        theme_class = "Daneel-call-stack-dark" if options.theme == "dark" else "Daneel-call-stack-light"
        html.append(f'<div class="Daneel-call-stack-container {theme_class}">')
        
        # Add title
        html.append(f'<div class="Daneel-call-stack-title">{options.title}</div>')
        
        # Add content
        max_height_style = f'style="max-height: {options.max_height}px;"' if options.max_height > 0 else ''
        html.append(f'<div class="Daneel-call-stack-content" {max_height_style}>')
        
        if frames:
            # Render each frame
            for i, frame in enumerate(frames):
                # First frame is selected by default
                is_selected = i == 0
                html.append(self.render_frame(frame, i, is_selected, options))
        else:
            html.append('<div class="Daneel-call-stack-empty">No stack frames available</div>')
            
        html.append('</div>')  # End content
        
        html.append('</div>')  # End container
        
        return "\n".join(html)
        
    def get_css(self) -> str:
        """Get the CSS for the call stack component.
        
        Returns:
            CSS for the call stack component
        """
        css = """
        .Daneel-call-stack-container {
            border: 1px solid #e2e8f0;
            border-radius: 0.375rem;
            margin: 1rem 0;
            overflow: hidden;
            font-family: system-ui, -apple-system, sans-serif;
            font-size: 0.875rem;
        }
        
        .Daneel-call-stack-light {
            background-color: #ffffff;
            color: #1e293b;
        }
        
        .Daneel-call-stack-dark {
            background-color: #1e293b;
            color: #e2e8f0;
        }
        
        .Daneel-call-stack-title {
            padding: 0.5rem 1rem;
            font-weight: 500;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .Daneel-call-stack-light .Daneel-call-stack-title {
            background-color: #f8fafc;
            border-bottom-color: #e2e8f0;
        }
        
        .Daneel-call-stack-dark .Daneel-call-stack-title {
            background-color: #0f172a;
            border-bottom-color: #334155;
        }
        
        .Daneel-call-stack-content {
            overflow: auto;
        }
        
        .Daneel-call-stack-frame {
            border-bottom: 1px solid #e2e8f0;
            cursor: pointer;
        }
        
        .Daneel-call-stack-dark .Daneel-call-stack-frame {
            border-bottom-color: #334155;
        }
        
        .Daneel-call-stack-frame:last-child {
            border-bottom: none;
        }
        
        .Daneel-call-stack-frame-header {
            padding: 0.5rem 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .Daneel-call-stack-frame:hover .Daneel-call-stack-frame-header {
            background-color: rgba(100, 116, 139, 0.1);
        }
        
        .Daneel-call-stack-frame-selected .Daneel-call-stack-frame-header {
            background-color: rgba(59, 130, 246, 0.1);
        }
        
        .Daneel-call-stack-function-name {
            font-weight: 500;
        }
        
        .Daneel-call-stack-location {
            font-family: monospace;
            font-size: 0.75rem;
            color: #64748b;
        }
        
        .Daneel-call-stack-dark .Daneel-call-stack-location {
            color: #94a3b8;
        }
        
        .Daneel-call-stack-frame-library {
            opacity: 0.7;
        }
        
        .Daneel-call-stack-frame-details {
            padding: 0 1rem 1rem 1rem;
            border-top: 1px solid #e2e8f0;
        }
        
        .Daneel-call-stack-dark .Daneel-call-stack-frame-details {
            border-top-color: #334155;
        }
        
        .Daneel-call-stack-section-title {
            font-weight: 500;
            margin: 0.5rem 0;
            font-size: 0.75rem;
            color: #64748b;
        }
        
        .Daneel-call-stack-dark .Daneel-call-stack-section-title {
            color: #94a3b8;
        }
        
        .Daneel-call-stack-source {
            margin-bottom: 1rem;
        }
        
        .Daneel-call-stack-no-source {
            font-style: italic;
            color: #64748b;
            padding: 0.5rem;
        }
        
        .Daneel-call-stack-dark .Daneel-call-stack-no-source {
            color: #94a3b8;
        }
        
        .Daneel-call-stack-variables-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 0.5rem;
        }
        
        .Daneel-call-stack-variable {
            padding: 0.25rem;
            border-radius: 0.25rem;
            background-color: rgba(100, 116, 139, 0.1);
        }
        
        .Daneel-call-stack-variable-name {
            font-weight: 500;
            font-size: 0.75rem;
        }
        
        .Daneel-call-stack-variable-value {
            font-family: monospace;
            font-size: 0.75rem;
            word-break: break-word;
        }
        
        .Daneel-call-stack-string {
            color: #10b981;
        }
        
        .Daneel-call-stack-number {
            color: #3b82f6;
        }
        
        .Daneel-call-stack-boolean {
            color: #8b5cf6;
        }
        
        .Daneel-call-stack-null {
            color: #64748b;
        }
        
        .Daneel-call-stack-dark .Daneel-call-stack-string {
            color: #34d399;
        }
        
        .Daneel-call-stack-dark .Daneel-call-stack-number {
            color: #60a5fa;
        }
        
        .Daneel-call-stack-dark .Daneel-call-stack-boolean {
            color: #a78bfa;
        }
        
        .Daneel-call-stack-dark .Daneel-call-stack-null {
            color: #94a3b8;
        }
        
        .Daneel-call-stack-empty {
            padding: 1rem;
            text-align: center;
            color: #64748b;
            font-style: italic;
        }
        
        .Daneel-call-stack-dark .Daneel-call-stack-empty {
            color: #94a3b8;
        }
        """
        
        return css
