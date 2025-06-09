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

"""General utility tools for Daneel."""

import datetime
import json
import os
import platform
import random
import re
import string
import uuid
from typing import Dict, List, Optional, Union

from Daneel.core.tools import ToolResult
from Daneel.core.tools.tool_registry import ToolCategory, tool


@tool(
    id="get_current_time",
    name="Get Current Time",
    description="Get the current date and time",
    parameters={
        "format": {
            "type": "string",
            "description": "Format string for the date and time",
            "examples": ["%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%H:%M:%S"],
        },
        "timezone": {
            "type": "string",
            "description": "Timezone for the date and time",
            "examples": ["UTC", "America/New_York", "Europe/London"],
        },
    },
    required=[],
    category=ToolCategory.UTILS,
    tags=["time", "date", "utility"],
)
def get_current_time(
    format: str = "%Y-%m-%d %H:%M:%S",
    timezone: str = "UTC",
) -> ToolResult:
    """Get the current date and time.
    
    Args:
        format: Format string for the date and time
        timezone: Timezone for the date and time
        
    Returns:
        Current date and time
    """
    try:
        # Get current time in UTC
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Format the time
        formatted_time = now.strftime(format)
        
        return ToolResult(
            data={
                "time": formatted_time,
                "timestamp": now.timestamp(),
                "timezone": timezone,
                "format": format,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to get current time: {str(e)}",
                "format": format,
                "timezone": timezone,
            }
        )


@tool(
    id="generate_random_string",
    name="Generate Random String",
    description="Generate a random string",
    parameters={
        "length": {
            "type": "integer",
            "description": "Length of the random string",
            "examples": [8, 16, 32],
        },
        "include_digits": {
            "type": "boolean",
            "description": "Whether to include digits in the random string",
            "examples": [True, False],
        },
        "include_special_chars": {
            "type": "boolean",
            "description": "Whether to include special characters in the random string",
            "examples": [True, False],
        },
    },
    required=["length"],
    category=ToolCategory.UTILS,
    tags=["random", "string", "utility"],
)
def generate_random_string(
    length: int,
    include_digits: bool = True,
    include_special_chars: bool = False,
) -> ToolResult:
    """Generate a random string.
    
    Args:
        length: Length of the random string
        include_digits: Whether to include digits in the random string
        include_special_chars: Whether to include special characters in the random string
        
    Returns:
        Random string
    """
    try:
        # Validate length
        if length <= 0:
            return ToolResult(
                data={
                    "error": "Length must be a positive integer",
                    "length": length,
                }
            )
        
        # Define character sets
        chars = string.ascii_letters
        if include_digits:
            chars += string.digits
        if include_special_chars:
            chars += string.punctuation
        
        # Generate random string
        random_string = "".join(random.choice(chars) for _ in range(length))
        
        return ToolResult(
            data={
                "random_string": random_string,
                "length": length,
                "include_digits": include_digits,
                "include_special_chars": include_special_chars,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to generate random string: {str(e)}",
                "length": length,
            }
        )


@tool(
    id="generate_uuid",
    name="Generate UUID",
    description="Generate a UUID",
    parameters={
        "version": {
            "type": "integer",
            "description": "UUID version (1, 4, or 5)",
            "examples": [1, 4, 5],
            "enum": [1, 4, 5],
        },
        "namespace": {
            "type": "string",
            "description": "Namespace for version 5 UUID",
            "examples": ["dns", "url", "oid", "x500"],
        },
        "name": {
            "type": "string",
            "description": "Name for version 5 UUID",
            "examples": ["example.com", "user123"],
        },
    },
    required=["version"],
    category=ToolCategory.UTILS,
    tags=["uuid", "utility"],
)
def generate_uuid(
    version: int,
    namespace: Optional[str] = None,
    name: Optional[str] = None,
) -> ToolResult:
    """Generate a UUID.
    
    Args:
        version: UUID version (1, 4, or 5)
        namespace: Namespace for version 5 UUID
        name: Name for version 5 UUID
        
    Returns:
        Generated UUID
    """
    try:
        # Validate version
        if version not in [1, 4, 5]:
            return ToolResult(
                data={
                    "error": "Invalid UUID version. Must be 1, 4, or 5.",
                    "version": version,
                }
            )
        
        # Generate UUID
        if version == 1:
            # Version 1: Time-based
            generated_uuid = uuid.uuid1()
        elif version == 4:
            # Version 4: Random
            generated_uuid = uuid.uuid4()
        elif version == 5:
            # Version 5: Namespace and name
            if not namespace or not name:
                return ToolResult(
                    data={
                        "error": "Namespace and name are required for version 5 UUID",
                        "version": version,
                    }
                )
            
            # Get namespace UUID
            namespace_uuid = None
            if namespace == "dns":
                namespace_uuid = uuid.NAMESPACE_DNS
            elif namespace == "url":
                namespace_uuid = uuid.NAMESPACE_URL
            elif namespace == "oid":
                namespace_uuid = uuid.NAMESPACE_OID
            elif namespace == "x500":
                namespace_uuid = uuid.NAMESPACE_X500
            else:
                try:
                    namespace_uuid = uuid.UUID(namespace)
                except ValueError:
                    return ToolResult(
                        data={
                            "error": f"Invalid namespace: {namespace}",
                            "version": version,
                        }
                    )
            
            # Generate version 5 UUID
            generated_uuid = uuid.uuid5(namespace_uuid, name)
        
        return ToolResult(
            data={
                "uuid": str(generated_uuid),
                "version": version,
                "namespace": namespace,
                "name": name,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to generate UUID: {str(e)}",
                "version": version,
            }
        )


@tool(
    id="get_system_info",
    name="Get System Info",
    description="Get information about the system",
    parameters={},
    required=[],
    category=ToolCategory.UTILS,
    tags=["system", "info", "utility"],
)
def get_system_info() -> ToolResult:
    """Get information about the system.
    
    Returns:
        System information
    """
    try:
        # Get system information
        system_info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
        }
        
        return ToolResult(
            data=system_info
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to get system information: {str(e)}",
            }
        )


@tool(
    id="parse_json",
    name="Parse JSON",
    description="Parse a JSON string",
    parameters={
        "json_string": {
            "type": "string",
            "description": "JSON string to parse",
            "examples": ["{\"name\": \"John\", \"age\": 30}", "[1, 2, 3, 4, 5]"],
        },
    },
    required=["json_string"],
    category=ToolCategory.UTILS,
    tags=["json", "parse", "utility"],
)
def parse_json(
    json_string: str,
) -> ToolResult:
    """Parse a JSON string.
    
    Args:
        json_string: JSON string to parse
        
    Returns:
        Parsed JSON
    """
    try:
        # Parse JSON
        parsed_json = json.loads(json_string)
        
        return ToolResult(
            data={
                "parsed": parsed_json,
                "type": type(parsed_json).__name__,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to parse JSON: {str(e)}",
                "json_string": json_string,
            }
        )


@tool(
    id="format_json",
    name="Format JSON",
    description="Format a JSON string",
    parameters={
        "json_string": {
            "type": "string",
            "description": "JSON string to format",
            "examples": ["{\"name\":\"John\",\"age\":30}", "[1,2,3,4,5]"],
        },
        "indent": {
            "type": "integer",
            "description": "Number of spaces for indentation",
            "examples": [2, 4],
        },
        "sort_keys": {
            "type": "boolean",
            "description": "Whether to sort keys alphabetically",
            "examples": [True, False],
        },
    },
    required=["json_string"],
    category=ToolCategory.UTILS,
    tags=["json", "format", "utility"],
)
def format_json(
    json_string: str,
    indent: int = 2,
    sort_keys: bool = False,
) -> ToolResult:
    """Format a JSON string.
    
    Args:
        json_string: JSON string to format
        indent: Number of spaces for indentation
        sort_keys: Whether to sort keys alphabetically
        
    Returns:
        Formatted JSON string
    """
    try:
        # Parse JSON
        parsed_json = json.loads(json_string)
        
        # Format JSON
        formatted_json = json.dumps(parsed_json, indent=indent, sort_keys=sort_keys)
        
        return ToolResult(
            data={
                "formatted": formatted_json,
                "indent": indent,
                "sort_keys": sort_keys,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to format JSON: {str(e)}",
                "json_string": json_string,
            }
        )
