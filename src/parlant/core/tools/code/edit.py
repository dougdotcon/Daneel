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

"""Code editing tools for Daneel."""

import os
import re
from typing import Dict, List, Optional, Union

from Daneel.core.tools import ToolResult
from Daneel.core.tools.tool_registry import ToolCategory, tool


@tool(
    id="read_file",
    name="Read File",
    description="Read the contents of a file",
    parameters={
        "file_path": {
            "type": "string",
            "description": "Path to the file to read",
            "examples": ["src/main.py", "README.md"],
        },
        "start_line": {
            "type": "integer",
            "description": "Line number to start reading from (1-based)",
            "examples": [1, 10, 100],
        },
        "end_line": {
            "type": "integer",
            "description": "Line number to end reading at (1-based, inclusive)",
            "examples": [10, 20, 200],
        },
    },
    required=["file_path"],
    category=ToolCategory.CODE,
    tags=["file", "read", "code"],
)
def read_file(
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
) -> ToolResult:
    """Read the contents of a file.
    
    Args:
        file_path: Path to the file to read
        start_line: Line number to start reading from (1-based)
        end_line: Line number to end reading at (1-based, inclusive)
        
    Returns:
        File contents
    """
    try:
        # Normalize file path
        file_path = os.path.normpath(file_path)
        
        # Check if file exists
        if not os.path.isfile(file_path):
            return ToolResult(
                data={
                    "error": f"File not found: {file_path}",
                    "file_path": file_path,
                }
            )
        
        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Apply line range if specified
        if start_line is not None or end_line is not None:
            # Convert to 0-based indexing
            start_idx = (start_line - 1) if start_line is not None else 0
            end_idx = end_line if end_line is not None else len(lines)
            
            # Validate indices
            start_idx = max(0, start_idx)
            end_idx = min(len(lines), end_idx)
            
            # Get the specified lines
            content = "".join(lines[start_idx:end_idx])
            line_range = {"start": start_line or 1, "end": min(end_line or len(lines), len(lines))}
        else:
            content = "".join(lines)
            line_range = {"start": 1, "end": len(lines)}
        
        return ToolResult(
            data={
                "content": content,
                "file_path": file_path,
                "line_range": line_range,
                "total_lines": len(lines),
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to read file: {str(e)}",
                "file_path": file_path,
            }
        )


@tool(
    id="write_file",
    name="Write File",
    description="Write content to a file",
    parameters={
        "file_path": {
            "type": "string",
            "description": "Path to the file to write",
            "examples": ["src/main.py", "README.md"],
        },
        "content": {
            "type": "string",
            "description": "Content to write to the file",
            "examples": ["print('Hello, world!')", "# My Project\n\nThis is a sample project."],
        },
        "mode": {
            "type": "string",
            "description": "Write mode: 'w' to overwrite, 'a' to append",
            "examples": ["w", "a"],
            "enum": ["w", "a"],
        },
    },
    required=["file_path", "content"],
    category=ToolCategory.CODE,
    tags=["file", "write", "code"],
)
def write_file(
    file_path: str,
    content: str,
    mode: str = "w",
) -> ToolResult:
    """Write content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        mode: Write mode: 'w' to overwrite, 'a' to append
        
    Returns:
        Result of the operation
    """
    try:
        # Normalize file path
        file_path = os.path.normpath(file_path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Write to the file
        with open(file_path, mode, encoding="utf-8") as f:
            f.write(content)
        
        return ToolResult(
            data={
                "success": True,
                "file_path": file_path,
                "mode": mode,
                "bytes_written": len(content.encode("utf-8")),
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to write file: {str(e)}",
                "file_path": file_path,
                "mode": mode,
            }
        )


@tool(
    id="edit_file",
    name="Edit File",
    description="Edit a specific part of a file",
    parameters={
        "file_path": {
            "type": "string",
            "description": "Path to the file to edit",
            "examples": ["src/main.py", "README.md"],
        },
        "start_line": {
            "type": "integer",
            "description": "Line number to start editing from (1-based)",
            "examples": [1, 10, 100],
        },
        "end_line": {
            "type": "integer",
            "description": "Line number to end editing at (1-based, inclusive)",
            "examples": [10, 20, 200],
        },
        "new_content": {
            "type": "string",
            "description": "New content to replace the specified lines",
            "examples": ["print('Hello, world!')", "# My Project\n\nThis is a sample project."],
        },
    },
    required=["file_path", "start_line", "end_line", "new_content"],
    category=ToolCategory.CODE,
    tags=["file", "edit", "code"],
)
def edit_file(
    file_path: str,
    start_line: int,
    end_line: int,
    new_content: str,
) -> ToolResult:
    """Edit a specific part of a file.
    
    Args:
        file_path: Path to the file to edit
        start_line: Line number to start editing from (1-based)
        end_line: Line number to end editing at (1-based, inclusive)
        new_content: New content to replace the specified lines
        
    Returns:
        Result of the operation
    """
    try:
        # Normalize file path
        file_path = os.path.normpath(file_path)
        
        # Check if file exists
        if not os.path.isfile(file_path):
            return ToolResult(
                data={
                    "error": f"File not found: {file_path}",
                    "file_path": file_path,
                }
            )
        
        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Convert to 0-based indexing
        start_idx = start_line - 1
        end_idx = end_line
        
        # Validate indices
        if start_idx < 0 or start_idx >= len(lines) or end_idx <= 0 or end_idx > len(lines) or start_idx >= end_idx:
            return ToolResult(
                data={
                    "error": f"Invalid line range: {start_line}-{end_line} (file has {len(lines)} lines)",
                    "file_path": file_path,
                }
            )
        
        # Split new content into lines
        new_lines = new_content.splitlines(True)
        
        # Replace the specified lines
        lines[start_idx:end_idx] = new_lines
        
        # Write the modified content back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        
        return ToolResult(
            data={
                "success": True,
                "file_path": file_path,
                "line_range": {"start": start_line, "end": end_line},
                "lines_replaced": end_line - start_line + 1,
                "new_lines": len(new_lines),
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to edit file: {str(e)}",
                "file_path": file_path,
            }
        )


@tool(
    id="create_file",
    name="Create File",
    description="Create a new file with the specified content",
    parameters={
        "file_path": {
            "type": "string",
            "description": "Path to the file to create",
            "examples": ["src/main.py", "README.md"],
        },
        "content": {
            "type": "string",
            "description": "Content to write to the file",
            "examples": ["print('Hello, world!')", "# My Project\n\nThis is a sample project."],
        },
        "overwrite": {
            "type": "boolean",
            "description": "Whether to overwrite the file if it already exists",
            "examples": [True, False],
        },
    },
    required=["file_path", "content"],
    category=ToolCategory.CODE,
    tags=["file", "create", "code"],
)
def create_file(
    file_path: str,
    content: str,
    overwrite: bool = False,
) -> ToolResult:
    """Create a new file with the specified content.
    
    Args:
        file_path: Path to the file to create
        content: Content to write to the file
        overwrite: Whether to overwrite the file if it already exists
        
    Returns:
        Result of the operation
    """
    try:
        # Normalize file path
        file_path = os.path.normpath(file_path)
        
        # Check if file exists
        if os.path.exists(file_path) and not overwrite:
            return ToolResult(
                data={
                    "error": f"File already exists: {file_path}",
                    "file_path": file_path,
                }
            )
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Write to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return ToolResult(
            data={
                "success": True,
                "file_path": file_path,
                "bytes_written": len(content.encode("utf-8")),
                "overwritten": os.path.exists(file_path) and overwrite,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to create file: {str(e)}",
                "file_path": file_path,
            }
        )


@tool(
    id="delete_file",
    name="Delete File",
    description="Delete a file",
    parameters={
        "file_path": {
            "type": "string",
            "description": "Path to the file to delete",
            "examples": ["src/main.py", "README.md"],
        },
    },
    required=["file_path"],
    category=ToolCategory.CODE,
    tags=["file", "delete", "code"],
    consequential=True,
)
def delete_file(
    file_path: str,
) -> ToolResult:
    """Delete a file.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        Result of the operation
    """
    try:
        # Normalize file path
        file_path = os.path.normpath(file_path)
        
        # Check if file exists
        if not os.path.isfile(file_path):
            return ToolResult(
                data={
                    "error": f"File not found: {file_path}",
                    "file_path": file_path,
                }
            )
        
        # Delete the file
        os.remove(file_path)
        
        return ToolResult(
            data={
                "success": True,
                "file_path": file_path,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to delete file: {str(e)}",
                "file_path": file_path,
            }
        )
