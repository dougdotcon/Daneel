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

"""Inspector component for debugging."""

import datetime
import inspect
import json
import re
from dataclasses import dataclass, field, is_dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, get_type_hints

from parlant.core.loggers import Logger


@dataclass
class InspectorOptions:
    """Options for the inspector component."""
    
    expand_level: int = 1
    max_depth: int = 10
    max_string_length: int = 100
    max_array_length: int = 100
    title: Optional[str] = None
    theme: str = "default"
    show_private: bool = False
    show_methods: bool = False
    show_dunder: bool = False


class ValueType(str, Enum):
    """Types of values in the inspector."""
    
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    NULL = "null"
    UNDEFINED = "undefined"
    FUNCTION = "function"
    SYMBOL = "symbol"
    OBJECT = "object"
    ARRAY = "array"
    DATE = "date"
    REGEXP = "regexp"
    ERROR = "error"
    MAP = "map"
    SET = "set"
    BIGINT = "bigint"
    CLASS = "class"
    DATACLASS = "dataclass"
    ENUM = "enum"
    BYTES = "bytes"
    COMPLEX = "complex"


class Inspector:
    """Inspector component for debugging."""
    
    def __init__(self, logger: Logger):
        """Initialize the inspector component.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        
    def get_value_type(self, value: Any) -> ValueType:
        """Get the type of a value.
        
        Args:
            value: Value to get the type of
            
        Returns:
            Type of the value
        """
        if value is None:
            return ValueType.NULL
        elif isinstance(value, str):
            return ValueType.STRING
        elif isinstance(value, (int, float)):
            return ValueType.NUMBER
        elif isinstance(value, bool):
            return ValueType.BOOLEAN
        elif isinstance(value, list):
            return ValueType.ARRAY
        elif isinstance(value, dict):
            return ValueType.OBJECT
        elif isinstance(value, (set, frozenset)):
            return ValueType.SET
        elif isinstance(value, (map, filter, zip)):
            return ValueType.MAP
        elif isinstance(value, datetime.datetime):
            return ValueType.DATE
        elif isinstance(value, re.Pattern):
            return ValueType.REGEXP
        elif isinstance(value, Exception):
            return ValueType.ERROR
        elif isinstance(value, bytes):
            return ValueType.BYTES
        elif isinstance(value, complex):
            return ValueType.COMPLEX
        elif inspect.isfunction(value) or inspect.ismethod(value):
            return ValueType.FUNCTION
        elif inspect.isclass(value):
            return ValueType.CLASS
        elif is_dataclass(value):
            return ValueType.DATACLASS
        elif isinstance(value, Enum):
            return ValueType.ENUM
        else:
            return ValueType.OBJECT
            
    def format_value(self, value: Any, value_type: ValueType, options: InspectorOptions) -> str:
        """Format a value for display.
        
        Args:
            value: Value to format
            value_type: Type of the value
            options: Options for formatting
            
        Returns:
            Formatted value
        """
        if value_type == ValueType.NULL:
            return "null"
        elif value_type == ValueType.UNDEFINED:
            return "undefined"
        elif value_type == ValueType.STRING:
            if len(value) > options.max_string_length:
                return f'"{value[:options.max_string_length]}..."'
            return f'"{value}"'
        elif value_type == ValueType.NUMBER:
            return str(value)
        elif value_type == ValueType.BOOLEAN:
            return str(value).lower()
        elif value_type == ValueType.FUNCTION:
            name = value.__name__ if hasattr(value, "__name__") else "anonymous"
            return f"ƒ {name}()"
        elif value_type == ValueType.DATE:
            return value.isoformat()
        elif value_type == ValueType.REGEXP:
            return str(value)
        elif value_type == ValueType.ERROR:
            return f"{type(value).__name__}: {str(value)}"
        elif value_type == ValueType.MAP:
            return f"Map({len(list(value))})"
        elif value_type == ValueType.SET:
            return f"Set({len(value)})"
        elif value_type == ValueType.ARRAY:
            return f"Array({len(value)})"
        elif value_type == ValueType.OBJECT:
            return "Object"
        elif value_type == ValueType.CLASS:
            return f"Class {value.__name__}"
        elif value_type == ValueType.DATACLASS:
            return f"DataClass {type(value).__name__}"
        elif value_type == ValueType.ENUM:
            return f"Enum {type(value).__name__}.{value.name}"
        elif value_type == ValueType.BYTES:
            return f"Bytes({len(value)})"
        elif value_type == ValueType.COMPLEX:
            return str(value)
        else:
            return str(value)
            
    def get_object_properties(self, value: Any, value_type: ValueType, options: InspectorOptions) -> Dict[str, Any]:
        """Get the properties of an object.
        
        Args:
            value: Object to get properties of
            value_type: Type of the object
            options: Options for getting properties
            
        Returns:
            Dictionary of property names to values
        """
        properties = {}
        
        if value_type == ValueType.ARRAY:
            # For arrays, use indices as property names
            for i, item in enumerate(value):
                if i >= options.max_array_length:
                    break
                properties[str(i)] = item
        elif value_type == ValueType.SET:
            # For sets, use indices as property names
            for i, item in enumerate(value):
                if i >= options.max_array_length:
                    break
                properties[str(i)] = item
        elif value_type == ValueType.MAP:
            # For maps, use string representation of keys as property names
            for i, (key, val) in enumerate(value):
                if i >= options.max_array_length:
                    break
                properties[str(key)] = val
        elif value_type == ValueType.DATACLASS:
            # For dataclasses, use field names as property names
            properties = asdict(value)
        elif value_type == ValueType.OBJECT or value_type == ValueType.CLASS:
            # For objects, use attribute names as property names
            for name in dir(value):
                # Skip private attributes if not showing them
                if name.startswith("_") and not options.show_dunder and not options.show_private:
                    continue
                    
                # Skip dunder methods if not showing them
                if name.startswith("__") and name.endswith("__") and not options.show_dunder:
                    continue
                    
                # Skip methods if not showing them
                try:
                    attr = getattr(value, name)
                    if callable(attr) and not options.show_methods:
                        continue
                except Exception:
                    # Skip attributes that can't be accessed
                    continue
                    
                properties[name] = attr
                
        return properties
        
    def is_expandable(self, value_type: ValueType) -> bool:
        """Check if a value type is expandable.
        
        Args:
            value_type: Type to check
            
        Returns:
            True if the type is expandable, False otherwise
        """
        return value_type in [
            ValueType.OBJECT,
            ValueType.ARRAY,
            ValueType.MAP,
            ValueType.SET,
            ValueType.CLASS,
            ValueType.DATACLASS,
        ]
        
    def render_object(self, name: Optional[str], value: Any, depth: int, options: InspectorOptions, path: str = "root") -> str:
        """Render an object as HTML.
        
        Args:
            name: Name of the object
            value: Object to render
            depth: Current depth in the object hierarchy
            options: Options for rendering
            path: Path to the object in the hierarchy
            
        Returns:
            HTML representation of the object
        """
        if depth > options.max_depth:
            return f'<div class="parlant-inspector-property parlant-inspector-max-depth">Maximum depth reached</div>'
            
        value_type = self.get_value_type(value)
        is_expandable = self.is_expandable(value_type)
        is_expanded = depth < options.expand_level
        
        # Get the value color class
        color_class = self._get_value_color_class(value_type)
        
        html = []
        
        # Property container
        html.append(f'<div class="parlant-inspector-property" data-path="{path}">')
        
        # Property header
        html.append('<div class="parlant-inspector-property-header">')
        
        # Expand/collapse button
        if is_expandable:
            if is_expanded:
                html.append('<button class="parlant-inspector-expand-button parlant-inspector-expanded" aria-label="Collapse">▼</button>')
            else:
                html.append('<button class="parlant-inspector-expand-button" aria-label="Expand">▶</button>')
        else:
            html.append('<span class="parlant-inspector-expand-placeholder"></span>')
            
        # Property name
        if name is not None:
            html.append(f'<span class="parlant-inspector-property-name">{name}:</span>')
            
        # Property value
        formatted_value = self.format_value(value, value_type, options)
        html.append(f'<span class="parlant-inspector-property-value {color_class}">{formatted_value}</span>')
        
        html.append('</div>')  # End property header
        
        # Property children
        if is_expandable and is_expanded:
            properties = self.get_object_properties(value, value_type, options)
            
            if properties:
                html.append('<div class="parlant-inspector-property-children">')
                
                for prop_name, prop_value in properties.items():
                    child_path = f"{path}.{prop_name}"
                    html.append(self.render_object(prop_name, prop_value, depth + 1, options, child_path))
                    
                html.append('</div>')  # End property children
            else:
                html.append('<div class="parlant-inspector-property-empty">No properties</div>')
                
        html.append('</div>')  # End property container
        
        return "\n".join(html)
        
    def _get_value_color_class(self, value_type: ValueType) -> str:
        """Get the color class for a value type.
        
        Args:
            value_type: Type to get the color class for
            
        Returns:
            Color class for the type
        """
        if value_type == ValueType.STRING:
            return "parlant-inspector-string"
        elif value_type == ValueType.NUMBER or value_type == ValueType.BIGINT:
            return "parlant-inspector-number"
        elif value_type == ValueType.BOOLEAN:
            return "parlant-inspector-boolean"
        elif value_type == ValueType.NULL or value_type == ValueType.UNDEFINED:
            return "parlant-inspector-null"
        elif value_type == ValueType.FUNCTION:
            return "parlant-inspector-function"
        elif value_type == ValueType.SYMBOL:
            return "parlant-inspector-symbol"
        elif value_type == ValueType.DATE or value_type == ValueType.REGEXP:
            return "parlant-inspector-date"
        elif value_type == ValueType.ERROR:
            return "parlant-inspector-error"
        else:
            return ""
            
    def render_html(self, data: Any, options: Optional[InspectorOptions] = None) -> str:
        """Render the inspector as HTML.
        
        Args:
            data: Data to inspect
            options: Options for rendering
            
        Returns:
            HTML representation of the inspector
        """
        if options is None:
            options = InspectorOptions()
            
        # Add container
        html = []
        
        theme_class = "parlant-inspector-dark" if options.theme == "dark" else "parlant-inspector-light"
        html.append(f'<div class="parlant-inspector-container {theme_class}">')
        
        # Add title if specified
        if options.title:
            html.append(f'<div class="parlant-inspector-title">{options.title}</div>')
            
        # Add content
        html.append('<div class="parlant-inspector-content">')
        html.append(self.render_object(None, data, 0, options))
        html.append('</div>')  # End content
        
        html.append('</div>')  # End container
        
        return "\n".join(html)
        
    def get_css(self) -> str:
        """Get the CSS for the inspector component.
        
        Returns:
            CSS for the inspector component
        """
        css = """
        .parlant-inspector-container {
            border: 1px solid #e2e8f0;
            border-radius: 0.375rem;
            margin: 1rem 0;
            overflow: hidden;
            font-family: monospace;
            font-size: 0.875rem;
        }
        
        .parlant-inspector-light {
            background-color: #ffffff;
            color: #1e293b;
        }
        
        .parlant-inspector-dark {
            background-color: #1e293b;
            color: #e2e8f0;
        }
        
        .parlant-inspector-title {
            padding: 0.5rem 1rem;
            font-weight: 500;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .parlant-inspector-light .parlant-inspector-title {
            background-color: #f8fafc;
            border-bottom-color: #e2e8f0;
        }
        
        .parlant-inspector-dark .parlant-inspector-title {
            background-color: #0f172a;
            border-bottom-color: #334155;
        }
        
        .parlant-inspector-content {
            padding: 0.5rem;
            overflow: auto;
            max-height: 500px;
        }
        
        .parlant-inspector-property {
            margin-bottom: 0.25rem;
        }
        
        .parlant-inspector-property-header {
            display: flex;
            align-items: center;
        }
        
        .parlant-inspector-expand-button,
        .parlant-inspector-expand-placeholder {
            width: 1rem;
            height: 1rem;
            margin-right: 0.25rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            cursor: pointer;
            background: none;
            border: none;
            padding: 0;
            color: inherit;
        }
        
        .parlant-inspector-expand-placeholder {
            visibility: hidden;
        }
        
        .parlant-inspector-property-name {
            margin-right: 0.5rem;
            font-weight: 500;
        }
        
        .parlant-inspector-property-children {
            margin-left: 1.25rem;
            border-left: 1px solid #e2e8f0;
            padding-left: 0.5rem;
        }
        
        .parlant-inspector-dark .parlant-inspector-property-children {
            border-left-color: #334155;
        }
        
        .parlant-inspector-property-empty {
            margin-left: 1.25rem;
            padding-left: 0.5rem;
            font-style: italic;
            color: #64748b;
        }
        
        .parlant-inspector-max-depth {
            margin-left: 1.25rem;
            padding-left: 0.5rem;
            font-style: italic;
            color: #64748b;
        }
        
        /* Value colors */
        .parlant-inspector-string {
            color: #10b981;
        }
        
        .parlant-inspector-number {
            color: #3b82f6;
        }
        
        .parlant-inspector-boolean {
            color: #8b5cf6;
        }
        
        .parlant-inspector-null {
            color: #64748b;
        }
        
        .parlant-inspector-function {
            color: #f59e0b;
        }
        
        .parlant-inspector-symbol {
            color: #ec4899;
        }
        
        .parlant-inspector-date {
            color: #ef4444;
        }
        
        .parlant-inspector-error {
            color: #ef4444;
        }
        
        /* Dark mode value colors */
        .parlant-inspector-dark .parlant-inspector-string {
            color: #34d399;
        }
        
        .parlant-inspector-dark .parlant-inspector-number {
            color: #60a5fa;
        }
        
        .parlant-inspector-dark .parlant-inspector-boolean {
            color: #a78bfa;
        }
        
        .parlant-inspector-dark .parlant-inspector-null {
            color: #94a3b8;
        }
        
        .parlant-inspector-dark .parlant-inspector-function {
            color: #fbbf24;
        }
        
        .parlant-inspector-dark .parlant-inspector-symbol {
            color: #f472b6;
        }
        
        .parlant-inspector-dark .parlant-inspector-date {
            color: #f87171;
        }
        
        .parlant-inspector-dark .parlant-inspector-error {
            color: #f87171;
        }
        """
        
        return css
