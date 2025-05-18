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

"""Filesystem operation tools for Parlant."""

import os
import shutil
import glob
from typing import Dict, List, Optional, Union

from parlant.core.tools import ToolResult
from parlant.core.tools.tool_registry import ToolCategory, tool


@tool(
    id="list_directory",
    name="List Directory",
    description="List files and directories in a directory",
    parameters={
        "directory": {
            "type": "string",
            "description": "Directory to list",
            "examples": [".", "src", "/tmp"],
        },
        "pattern": {
            "type": "string",
            "description": "Optional glob pattern to filter results",
            "examples": ["*.py", "*.js", "*.txt"],
        },
        "recursive": {
            "type": "boolean",
            "description": "Whether to list files recursively",
            "examples": [True, False],
        },
    },
    required=["directory"],
    category=ToolCategory.FILESYSTEM,
    tags=["filesystem", "list", "directory"],
)
def list_directory(
    directory: str,
    pattern: Optional[str] = None,
    recursive: bool = False,
) -> ToolResult:
    """List files and directories in a directory.
    
    Args:
        directory: Directory to list
        pattern: Optional glob pattern to filter results
        recursive: Whether to list files recursively
        
    Returns:
        List of files and directories
    """
    try:
        # Normalize directory path
        directory = os.path.normpath(directory)
        
        # Check if directory exists
        if not os.path.isdir(directory):
            return ToolResult(
                data={
                    "error": f"Directory not found: {directory}",
                    "directory": directory,
                }
            )
        
        # List files and directories
        if recursive:
            if pattern:
                # Use glob for recursive pattern matching
                matches = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
                items = [os.path.relpath(match, directory) for match in matches]
            else:
                # Walk the directory tree
                items = []
                for root, dirs, files in os.walk(directory):
                    rel_root = os.path.relpath(root, directory)
                    if rel_root == ".":
                        items.extend(dirs + files)
                    else:
                        items.extend([os.path.join(rel_root, d) for d in dirs] + [os.path.join(rel_root, f) for f in files])
        else:
            # List only the specified directory
            all_items = os.listdir(directory)
            if pattern:
                # Filter by pattern
                items = [item for item in all_items if glob.fnmatch.fnmatch(item, pattern)]
            else:
                items = all_items
        
        # Get item details
        item_details = []
        for item in items:
            item_path = os.path.join(directory, item)
            is_dir = os.path.isdir(item_path)
            try:
                stat = os.stat(item_path)
                item_details.append({
                    "name": item,
                    "is_directory": is_dir,
                    "size": stat.st_size if not is_dir else None,
                    "modified": stat.st_mtime,
                })
            except (FileNotFoundError, PermissionError):
                # Skip items that can't be accessed
                continue
        
        return ToolResult(
            data={
                "items": item_details,
                "total_items": len(item_details),
                "directory": directory,
                "pattern": pattern,
                "recursive": recursive,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to list directory: {str(e)}",
                "directory": directory,
            }
        )


@tool(
    id="create_directory",
    name="Create Directory",
    description="Create a new directory",
    parameters={
        "directory": {
            "type": "string",
            "description": "Directory to create",
            "examples": ["new_dir", "src/new_module", "path/to/new/dir"],
        },
        "parents": {
            "type": "boolean",
            "description": "Whether to create parent directories if they don't exist",
            "examples": [True, False],
        },
    },
    required=["directory"],
    category=ToolCategory.FILESYSTEM,
    tags=["filesystem", "create", "directory"],
)
def create_directory(
    directory: str,
    parents: bool = True,
) -> ToolResult:
    """Create a new directory.
    
    Args:
        directory: Directory to create
        parents: Whether to create parent directories if they don't exist
        
    Returns:
        Result of the operation
    """
    try:
        # Normalize directory path
        directory = os.path.normpath(directory)
        
        # Check if directory already exists
        if os.path.exists(directory):
            return ToolResult(
                data={
                    "error": f"Path already exists: {directory}",
                    "directory": directory,
                }
            )
        
        # Create the directory
        if parents:
            os.makedirs(directory)
        else:
            os.mkdir(directory)
        
        return ToolResult(
            data={
                "success": True,
                "directory": directory,
                "parents": parents,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to create directory: {str(e)}",
                "directory": directory,
            }
        )


@tool(
    id="delete_directory",
    name="Delete Directory",
    description="Delete a directory",
    parameters={
        "directory": {
            "type": "string",
            "description": "Directory to delete",
            "examples": ["old_dir", "src/old_module", "path/to/old/dir"],
        },
        "recursive": {
            "type": "boolean",
            "description": "Whether to delete the directory recursively",
            "examples": [True, False],
        },
    },
    required=["directory"],
    category=ToolCategory.FILESYSTEM,
    tags=["filesystem", "delete", "directory"],
    consequential=True,
)
def delete_directory(
    directory: str,
    recursive: bool = False,
) -> ToolResult:
    """Delete a directory.
    
    Args:
        directory: Directory to delete
        recursive: Whether to delete the directory recursively
        
    Returns:
        Result of the operation
    """
    try:
        # Normalize directory path
        directory = os.path.normpath(directory)
        
        # Check if directory exists
        if not os.path.isdir(directory):
            return ToolResult(
                data={
                    "error": f"Directory not found: {directory}",
                    "directory": directory,
                }
            )
        
        # Delete the directory
        if recursive:
            shutil.rmtree(directory)
        else:
            os.rmdir(directory)
        
        return ToolResult(
            data={
                "success": True,
                "directory": directory,
                "recursive": recursive,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to delete directory: {str(e)}",
                "directory": directory,
            }
        )


@tool(
    id="copy_file",
    name="Copy File",
    description="Copy a file from source to destination",
    parameters={
        "source": {
            "type": "string",
            "description": "Source file path",
            "examples": ["src/file.txt", "data/input.csv"],
        },
        "destination": {
            "type": "string",
            "description": "Destination file path",
            "examples": ["backup/file.txt", "output/input_copy.csv"],
        },
        "overwrite": {
            "type": "boolean",
            "description": "Whether to overwrite the destination file if it exists",
            "examples": [True, False],
        },
    },
    required=["source", "destination"],
    category=ToolCategory.FILESYSTEM,
    tags=["filesystem", "copy", "file"],
)
def copy_file(
    source: str,
    destination: str,
    overwrite: bool = False,
) -> ToolResult:
    """Copy a file from source to destination.
    
    Args:
        source: Source file path
        destination: Destination file path
        overwrite: Whether to overwrite the destination file if it exists
        
    Returns:
        Result of the operation
    """
    try:
        # Normalize file paths
        source = os.path.normpath(source)
        destination = os.path.normpath(destination)
        
        # Check if source file exists
        if not os.path.isfile(source):
            return ToolResult(
                data={
                    "error": f"Source file not found: {source}",
                    "source": source,
                    "destination": destination,
                }
            )
        
        # Check if destination file exists
        if os.path.exists(destination) and not overwrite:
            return ToolResult(
                data={
                    "error": f"Destination file already exists: {destination}",
                    "source": source,
                    "destination": destination,
                }
            )
        
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)
        
        # Copy the file
        shutil.copy2(source, destination)
        
        return ToolResult(
            data={
                "success": True,
                "source": source,
                "destination": destination,
                "overwritten": os.path.exists(destination) and overwrite,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to copy file: {str(e)}",
                "source": source,
                "destination": destination,
            }
        )


@tool(
    id="move_file",
    name="Move File",
    description="Move a file from source to destination",
    parameters={
        "source": {
            "type": "string",
            "description": "Source file path",
            "examples": ["src/file.txt", "data/input.csv"],
        },
        "destination": {
            "type": "string",
            "description": "Destination file path",
            "examples": ["backup/file.txt", "output/input_moved.csv"],
        },
        "overwrite": {
            "type": "boolean",
            "description": "Whether to overwrite the destination file if it exists",
            "examples": [True, False],
        },
    },
    required=["source", "destination"],
    category=ToolCategory.FILESYSTEM,
    tags=["filesystem", "move", "file"],
)
def move_file(
    source: str,
    destination: str,
    overwrite: bool = False,
) -> ToolResult:
    """Move a file from source to destination.
    
    Args:
        source: Source file path
        destination: Destination file path
        overwrite: Whether to overwrite the destination file if it exists
        
    Returns:
        Result of the operation
    """
    try:
        # Normalize file paths
        source = os.path.normpath(source)
        destination = os.path.normpath(destination)
        
        # Check if source file exists
        if not os.path.isfile(source):
            return ToolResult(
                data={
                    "error": f"Source file not found: {source}",
                    "source": source,
                    "destination": destination,
                }
            )
        
        # Check if destination file exists
        if os.path.exists(destination) and not overwrite:
            return ToolResult(
                data={
                    "error": f"Destination file already exists: {destination}",
                    "source": source,
                    "destination": destination,
                }
            )
        
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)
        
        # Move the file
        shutil.move(source, destination)
        
        return ToolResult(
            data={
                "success": True,
                "source": source,
                "destination": destination,
                "overwritten": os.path.exists(destination) and overwrite,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to move file: {str(e)}",
                "source": source,
                "destination": destination,
            }
        )
