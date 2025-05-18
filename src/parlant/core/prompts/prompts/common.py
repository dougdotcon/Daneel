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

"""Common prompt structures and utilities for Parlant."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
import json
import re


class PromptType(str, Enum):
    """Types of prompts."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    TEMPLATE = "template"


class PromptFormat(str, Enum):
    """Formats for prompts."""
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


class PromptCategory(str, Enum):
    """Categories of prompts."""
    GENERAL = "general"
    CODING = "coding"
    REASONING = "reasoning"
    CONVERSATION = "conversation"
    TOOL_USE = "tool_use"
    AGENT = "agent"
    CUSTOM = "custom"


@dataclass
class PromptMetadata:
    """Metadata for a prompt."""
    id: str
    name: str
    description: str
    version: str
    author: str
    created_at: str
    updated_at: str
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None
    license: Optional[str] = None
    model_compatibility: List[str] = field(default_factory=list)
    prompt_type: PromptType = PromptType.SYSTEM
    prompt_format: PromptFormat = PromptFormat.TEXT
    prompt_category: PromptCategory = PromptCategory.GENERAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": self.tags,
            "source": self.source,
            "license": self.license,
            "model_compatibility": self.model_compatibility,
            "prompt_type": self.prompt_type,
            "prompt_format": self.prompt_format,
            "prompt_category": self.prompt_category,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptMetadata":
        """Create metadata from a dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            version=data["version"],
            author=data["author"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            tags=data.get("tags", []),
            source=data.get("source"),
            license=data.get("license"),
            model_compatibility=data.get("model_compatibility", []),
            prompt_type=PromptType(data.get("prompt_type", PromptType.SYSTEM)),
            prompt_format=PromptFormat(data.get("prompt_format", PromptFormat.TEXT)),
            prompt_category=PromptCategory(data.get("prompt_category", PromptCategory.GENERAL)),
        )


@dataclass
class PromptVariable:
    """A variable in a prompt template."""
    name: str
    description: str
    default_value: Optional[str] = None
    required: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert variable to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "default_value": self.default_value,
            "required": self.required,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptVariable":
        """Create variable from a dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            default_value=data.get("default_value"),
            required=data.get("required", True),
        )


@dataclass
class Prompt:
    """A prompt with metadata and content."""
    metadata: PromptMetadata
    content: str
    variables: List[PromptVariable] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert prompt to a dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "content": self.content,
            "variables": [v.to_dict() for v in self.variables],
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Prompt":
        """Create prompt from a dictionary."""
        return cls(
            metadata=PromptMetadata.from_dict(data["metadata"]),
            content=data["content"],
            variables=[PromptVariable.from_dict(v) for v in data.get("variables", [])],
        )
        
    def render(self, variables: Dict[str, str] = None) -> str:
        """Render the prompt with variables.
        
        Args:
            variables: Dictionary of variable values
            
        Returns:
            Rendered prompt
            
        Raises:
            ValueError: If a required variable is missing
        """
        variables = variables or {}
        content = self.content
        
        # Check for missing required variables
        missing_vars = []
        for var in self.variables:
            if var.required and var.name not in variables and var.default_value is None:
                missing_vars.append(var.name)
                
        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
            
        # Replace variables in the content
        for var in self.variables:
            value = variables.get(var.name, var.default_value or "")
            content = content.replace(f"{{{var.name}}}", value)
            
        return content


def extract_variables_from_template(template: str) -> List[str]:
    """Extract variable names from a template string.
    
    Args:
        template: Template string with variables in {variable_name} format
        
    Returns:
        List of variable names
    """
    pattern = r"\{([a-zA-Z0-9_]+)\}"
    matches = re.findall(pattern, template)
    return list(set(matches))  # Remove duplicates
