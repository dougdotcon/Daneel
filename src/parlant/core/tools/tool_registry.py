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

"""Tool registry for managing and accessing tools."""

import asyncio
import importlib
import inspect
import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Set, Type, Union, cast

from parlant.core.loggers import Logger
from parlant.core.tools import (
    LocalToolService,
    Tool,
    ToolContext,
    ToolError,
    ToolExecutionError,
    ToolId,
    ToolParameterDescriptor,
    ToolParameterOptions,
    ToolResult,
    ToolService,
)


class ToolCategory(str, Enum):
    """Categories of tools."""
    CODE = "code"
    WEB = "web"
    FILESYSTEM = "filesystem"
    UTILS = "utils"
    CUSTOM = "custom"


@dataclass
class ToolMetadata:
    """Metadata for a tool."""
    id: str
    name: str
    description: str
    category: ToolCategory
    version: str
    author: str
    tags: List[str]
    documentation_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "documentation_url": self.documentation_url,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolMetadata":
        """Create metadata from a dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            category=ToolCategory(data["category"]),
            version=data["version"],
            author=data["author"],
            tags=data["tags"],
            documentation_url=data.get("documentation_url"),
        )


class ToolRegistry:
    """Registry for tools in Parlant.
    
    This class manages the registration, discovery, and access of tools.
    It provides a unified interface for accessing tools from different sources.
    """
    
    def __init__(
        self,
        logger: Logger,
        tool_service: LocalToolService,
    ):
        """Initialize the tool registry.
        
        Args:
            logger: Logger instance
            tool_service: Local tool service
        """
        self.logger = logger
        self.tool_service = tool_service
        self._tools: Dict[str, ToolMetadata] = {}
        self._tool_modules: Dict[str, str] = {}
        
    async def register_tool(
        self,
        tool_id: str,
        module_path: str,
        name: str,
        description: str,
        parameters: Mapping[str, Union[ToolParameterDescriptor, tuple[ToolParameterDescriptor, ToolParameterOptions]]],
        required: Sequence[str],
        category: ToolCategory,
        version: str = "1.0.0",
        author: str = "Parlant",
        tags: List[str] = None,
        documentation_url: Optional[str] = None,
        consequential: bool = False,
    ) -> Tool:
        """Register a tool with the registry.
        
        Args:
            tool_id: ID of the tool
            module_path: Path to the module containing the tool
            name: Name of the tool
            description: Description of the tool
            parameters: Parameters for the tool
            required: Required parameters
            category: Category of the tool
            version: Version of the tool
            author: Author of the tool
            tags: Tags for the tool
            documentation_url: URL to the tool's documentation
            consequential: Whether the tool is consequential
            
        Returns:
            The registered tool
        """
        # Create tool metadata
        metadata = ToolMetadata(
            id=tool_id,
            name=name,
            description=description,
            category=category,
            version=version,
            author=author,
            tags=tags or [],
            documentation_url=documentation_url,
        )
        
        # Register the tool with the local tool service
        tool = await self.tool_service.create_tool(
            name=tool_id,
            module_path=module_path,
            description=description,
            parameters=parameters,
            required=required,
            consequential=consequential,
        )
        
        # Store the tool metadata and module path
        self._tools[tool_id] = metadata
        self._tool_modules[tool_id] = module_path
        
        self.logger.info(f"Registered tool: {tool_id}")
        
        return tool
        
    async def get_tool(self, tool_id: str) -> Tool:
        """Get a tool by ID.
        
        Args:
            tool_id: ID of the tool
            
        Returns:
            The tool
            
        Raises:
            ToolError: If the tool is not found
        """
        try:
            return await self.tool_service.read_tool(tool_id)
        except Exception as e:
            self.logger.error(f"Failed to get tool {tool_id}: {e}")
            raise ToolError(tool_id, f"Tool not found: {tool_id}")
            
    async def list_tools(
        self,
        category: Optional[ToolCategory] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Tool]:
        """List tools.
        
        Args:
            category: Filter by category
            tags: Filter by tags
            
        Returns:
            List of tools
        """
        tools = await self.tool_service.list_tools()
        
        if category:
            # Filter by category
            tool_ids = [
                tool_id for tool_id, metadata in self._tools.items()
                if metadata.category == category
            ]
            tools = [tool for tool in tools if tool.name in tool_ids]
            
        if tags:
            # Filter by tags
            tool_ids = [
                tool_id for tool_id, metadata in self._tools.items()
                if all(tag in metadata.tags for tag in tags)
            ]
            tools = [tool for tool in tools if tool.name in tool_ids]
            
        return tools
        
    async def call_tool(
        self,
        tool_id: str,
        context: ToolContext,
        arguments: Mapping[str, Any],
    ) -> ToolResult:
        """Call a tool.
        
        Args:
            tool_id: ID of the tool
            context: Tool context
            arguments: Tool arguments
            
        Returns:
            Tool result
            
        Raises:
            ToolError: If the tool call fails
        """
        try:
            return await self.tool_service.call_tool(tool_id, context, arguments)
        except Exception as e:
            self.logger.error(f"Failed to call tool {tool_id}: {e}")
            raise ToolExecutionError(tool_id, f"Tool call failed: {e}")
            
    async def get_tool_metadata(self, tool_id: str) -> ToolMetadata:
        """Get metadata for a tool.
        
        Args:
            tool_id: ID of the tool
            
        Returns:
            Tool metadata
            
        Raises:
            ToolError: If the tool is not found
        """
        if tool_id not in self._tools:
            self.logger.error(f"Tool metadata not found: {tool_id}")
            raise ToolError(tool_id, f"Tool metadata not found: {tool_id}")
            
        return self._tools[tool_id]
        
    async def list_tool_metadata(
        self,
        category: Optional[ToolCategory] = None,
        tags: Optional[List[str]] = None,
    ) -> List[ToolMetadata]:
        """List metadata for tools.
        
        Args:
            category: Filter by category
            tags: Filter by tags
            
        Returns:
            List of tool metadata
        """
        metadata = list(self._tools.values())
        
        if category:
            metadata = [m for m in metadata if m.category == category]
            
        if tags:
            metadata = [m for m in metadata if all(tag in m.tags for tag in tags)]
            
        return metadata
        
    async def discover_tools(self, package_path: str) -> List[Tool]:
        """Discover tools in a package.
        
        Args:
            package_path: Path to the package
            
        Returns:
            List of discovered tools
        """
        tools = []
        
        # Import the package
        package = importlib.import_module(package_path)
        
        # Get the package directory
        package_dir = os.path.dirname(package.__file__)
        
        # Find all Python files in the package
        for root, _, files in os.walk(package_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    # Get the module path
                    rel_path = os.path.relpath(os.path.join(root, file), package_dir)
                    module_name = os.path.splitext(rel_path.replace(os.path.sep, "."))[0]
                    module_path = f"{package_path}.{module_name}"
                    
                    try:
                        # Import the module
                        module = importlib.import_module(module_path)
                        
                        # Find all functions in the module
                        for name, obj in inspect.getmembers(module):
                            if inspect.isfunction(obj) and hasattr(obj, "__tool_metadata__"):
                                # Get the tool metadata
                                metadata = getattr(obj, "__tool_metadata__")
                                
                                # Register the tool
                                tool = await self.register_tool(
                                    tool_id=metadata["id"],
                                    module_path=module_path,
                                    name=metadata["name"],
                                    description=metadata["description"],
                                    parameters=metadata["parameters"],
                                    required=metadata["required"],
                                    category=ToolCategory(metadata["category"]),
                                    version=metadata.get("version", "1.0.0"),
                                    author=metadata.get("author", "Parlant"),
                                    tags=metadata.get("tags", []),
                                    documentation_url=metadata.get("documentation_url"),
                                    consequential=metadata.get("consequential", False),
                                )
                                
                                tools.append(tool)
                    except Exception as e:
                        self.logger.error(f"Failed to discover tools in {module_path}: {e}")
                        
        return tools


def tool(
    id: str,
    name: str,
    description: str,
    parameters: Dict[str, Dict[str, Any]],
    required: List[str],
    category: ToolCategory,
    version: str = "1.0.0",
    author: str = "Parlant",
    tags: List[str] = None,
    documentation_url: Optional[str] = None,
    consequential: bool = False,
) -> Callable[[Callable], Callable]:
    """Decorator for registering a function as a tool.
    
    Args:
        id: ID of the tool
        name: Name of the tool
        description: Description of the tool
        parameters: Parameters for the tool
        required: Required parameters
        category: Category of the tool
        version: Version of the tool
        author: Author of the tool
        tags: Tags for the tool
        documentation_url: URL to the tool's documentation
        consequential: Whether the tool is consequential
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        # Convert parameters to the format expected by the tool service
        tool_parameters = {}
        for param_name, param_def in parameters.items():
            param_type = param_def.get("type", "string")
            param_desc = ToolParameterDescriptor(
                type=param_type,
                description=param_def.get("description", ""),
            )
            
            if param_type == "array":
                param_desc["item_type"] = param_def.get("item_type", "string")
                
            if "enum" in param_def:
                param_desc["enum"] = param_def["enum"]
                
            if "examples" in param_def:
                param_desc["examples"] = param_def["examples"]
                
            param_options = ToolParameterOptions(
                hidden=param_def.get("hidden", False),
                source=param_def.get("source", "any"),
                description=param_def.get("description"),
                significance=param_def.get("significance"),
                examples=param_def.get("examples", []),
                precedence=param_def.get("precedence"),
                display_name=param_def.get("display_name"),
            )
            
            tool_parameters[param_name] = (param_desc, param_options)
            
        # Store the tool metadata on the function
        func.__tool_metadata__ = {
            "id": id,
            "name": name,
            "description": description,
            "parameters": tool_parameters,
            "required": required,
            "category": category,
            "version": version,
            "author": author,
            "tags": tags or [],
            "documentation_url": documentation_url,
            "consequential": consequential,
        }
        
        return func
        
    return decorator
