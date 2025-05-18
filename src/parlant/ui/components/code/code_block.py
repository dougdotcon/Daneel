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

"""Code block component for syntax highlighting."""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Union

import pygments
import pygments.formatters
import pygments.lexers
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.styles import get_style_by_name

from parlant.core.loggers import Logger


@dataclass
class CodeBlockOptions:
    """Options for the code block component."""
    
    language: Optional[str] = None
    show_line_numbers: bool = True
    show_copy_button: bool = True
    show_collapse_button: bool = True
    max_height: int = 500
    file_name: Optional[str] = None
    highlight_lines: List[int] = field(default_factory=list)
    theme: str = "default"
    line_start: int = 1


class CodeBlock:
    """Code block component for syntax highlighting."""
    
    # Map of file extensions to languages
    EXTENSION_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "jsx",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".json": "json",
        ".md": "markdown",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".cs": "csharp",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".sh": "bash",
        ".sql": "sql",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".dart": "dart",
    }
    
    # Available themes
    AVAILABLE_THEMES = {
        "default": "default",
        "monokai": "monokai",
        "solarized-dark": "solarized-dark",
        "solarized-light": "solarized-light",
        "dracula": "dracula",
        "vs": "vs",
        "vs-dark": "vs-dark",
    }
    
    def __init__(self, logger: Logger):
        """Initialize the code block component.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        
    def detect_language(self, code: str, file_name: Optional[str] = None) -> str:
        """Detect the language of the code.
        
        Args:
            code: Code to detect the language for
            file_name: Optional file name to help with detection
            
        Returns:
            Detected language
        """
        # Try to detect from file extension
        if file_name:
            _, ext = os.path.splitext(file_name)
            if ext.lower() in self.EXTENSION_MAP:
                return self.EXTENSION_MAP[ext.lower()]
        
        # Try to detect from code patterns
        if "import React" in code or "export default" in code or "const [" in code:
            return "jsx"
        elif "func " in code and "package " in code:
            return "go"
        elif "def " in code and "import " in code:
            return "python"
        elif "public class" in code or "private void" in code:
            return "java"
        elif "#include" in code or "int main(" in code:
            return "cpp"
        elif "<?php" in code:
            return "php"
        elif "<!DOCTYPE html>" in code or "<html>" in code:
            return "html"
        elif "SELECT " in code and " FROM " in code:
            return "sql"
        elif "async " in code and "await " in code:
            return "typescript"
        elif "function " in code or "const " in code or "let " in code:
            return "javascript"
        
        # Try to use pygments to guess
        try:
            lexer = guess_lexer(code)
            return lexer.name.lower().replace(" ", "-")
        except pygments.util.ClassNotFound:
            pass
        
        return "text"
    
    def highlight_code(self, code: str, options: CodeBlockOptions) -> str:
        """Highlight the code using pygments.
        
        Args:
            code: Code to highlight
            options: Options for highlighting
            
        Returns:
            HTML with highlighted code
        """
        language = options.language or self.detect_language(code, options.file_name)
        
        try:
            lexer = get_lexer_by_name(language)
        except pygments.util.ClassNotFound:
            self.logger.warning(f"Language not found: {language}, falling back to text")
            lexer = get_lexer_by_name("text")
        
        # Get the style
        theme = options.theme
        if theme not in self.AVAILABLE_THEMES:
            theme = "default"
        
        try:
            style = get_style_by_name(self.AVAILABLE_THEMES[theme])
        except pygments.util.ClassNotFound:
            self.logger.warning(f"Style not found: {theme}, falling back to default")
            style = get_style_by_name("default")
        
        # Create formatter with line numbers if requested
        formatter = HtmlFormatter(
            style=style,
            linenos="table" if options.show_line_numbers else False,
            linenostart=options.line_start,
            hl_lines=options.highlight_lines,
            cssclass="parlant-code-block",
            wrapcode=True,
        )
        
        # Highlight the code
        highlighted = pygments.highlight(code, lexer, formatter)
        
        return highlighted
    
    def render_html(self, code: str, options: Optional[CodeBlockOptions] = None) -> str:
        """Render the code block as HTML.
        
        Args:
            code: Code to render
            options: Options for rendering
            
        Returns:
            HTML representation of the code block
        """
        if options is None:
            options = CodeBlockOptions()
        
        highlighted = self.highlight_code(code, options)
        
        # Add container with file name and buttons
        html = []
        html.append('<div class="parlant-code-block-container">')
        
        # Add header with file name and language
        html.append('<div class="parlant-code-block-header">')
        
        if options.file_name:
            html.append(f'<div class="parlant-code-block-filename">{options.file_name}</div>')
        
        language = options.language or self.detect_language(code, options.file_name)
        html.append(f'<div class="parlant-code-block-language">{language.upper()}</div>')
        
        html.append('</div>')  # End header
        
        # Add the highlighted code
        max_height_style = f'style="max-height: {options.max_height}px; overflow: auto;"' if options.max_height > 0 else ''
        html.append(f'<div class="parlant-code-block-content" {max_height_style}>')
        html.append(highlighted)
        html.append('</div>')  # End content
        
        # Add footer with buttons
        html.append('<div class="parlant-code-block-footer">')
        
        if options.show_copy_button:
            html.append('<button class="parlant-code-block-copy-button">Copy</button>')
        
        if options.show_collapse_button and options.max_height > 0:
            html.append('<button class="parlant-code-block-collapse-button">Collapse</button>')
        
        html.append('</div>')  # End footer
        
        html.append('</div>')  # End container
        
        return "\n".join(html)
    
    def get_css(self) -> str:
        """Get the CSS for the code block component.
        
        Returns:
            CSS for the code block component
        """
        css = """
        .parlant-code-block-container {
            border: 1px solid #e2e8f0;
            border-radius: 0.375rem;
            margin: 1rem 0;
            overflow: hidden;
        }
        
        .parlant-code-block-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 1rem;
            background-color: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .parlant-code-block-filename {
            font-family: monospace;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .parlant-code-block-language {
            font-size: 0.75rem;
            color: #64748b;
        }
        
        .parlant-code-block-content {
            overflow: auto;
        }
        
        .parlant-code-block {
            margin: 0 !important;
        }
        
        .parlant-code-block .linenodiv pre {
            margin: 0;
            padding: 1rem 0.5rem;
            border-right: 1px solid #e2e8f0;
            background-color: #f8fafc;
            color: #64748b;
            text-align: right;
        }
        
        .parlant-code-block .code pre {
            margin: 0;
            padding: 1rem;
        }
        
        .parlant-code-block-footer {
            display: flex;
            justify-content: flex-end;
            padding: 0.5rem;
            background-color: #f8fafc;
            border-top: 1px solid #e2e8f0;
        }
        
        .parlant-code-block-copy-button,
        .parlant-code-block-collapse-button {
            background-color: transparent;
            border: 1px solid #e2e8f0;
            border-radius: 0.25rem;
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
            margin-left: 0.5rem;
            cursor: pointer;
        }
        
        .parlant-code-block-copy-button:hover,
        .parlant-code-block-collapse-button:hover {
            background-color: #e2e8f0;
        }
        
        /* Dark mode */
        @media (prefers-color-scheme: dark) {
            .parlant-code-block-container {
                border-color: #334155;
            }
            
            .parlant-code-block-header {
                background-color: #1e293b;
                border-bottom-color: #334155;
            }
            
            .parlant-code-block-language {
                color: #94a3b8;
            }
            
            .parlant-code-block .linenodiv pre {
                border-right-color: #334155;
                background-color: #1e293b;
                color: #94a3b8;
            }
            
            .parlant-code-block-footer {
                background-color: #1e293b;
                border-top-color: #334155;
            }
            
            .parlant-code-block-copy-button,
            .parlant-code-block-collapse-button {
                border-color: #334155;
                color: #e2e8f0;
            }
            
            .parlant-code-block-copy-button:hover,
            .parlant-code-block-collapse-button:hover {
                background-color: #334155;
            }
        }
        """
        
        return css
