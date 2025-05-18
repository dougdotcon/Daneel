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

"""Diff viewer component for code comparison."""

import difflib
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

import pygments
import pygments.formatters
import pygments.lexers
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.styles import get_style_by_name

from parlant.core.loggers import Logger
from parlant.ui.components.code.code_block import CodeBlock


class DiffMode(str, Enum):
    """Diff display modes."""
    
    SPLIT = "split"
    UNIFIED = "unified"


@dataclass
class DiffLine:
    """A line in a diff."""
    
    content: str
    line_number: int
    type: str  # "added", "removed", "unchanged"


@dataclass
class DiffViewerOptions:
    """Options for the diff viewer component."""
    
    language: Optional[str] = None
    show_line_numbers: bool = True
    show_copy_button: bool = True
    file_name: Optional[str] = None
    diff_mode: DiffMode = DiffMode.SPLIT
    theme: str = "default"
    context_lines: int = 3  # Number of context lines to show around changes


class DiffViewer:
    """Diff viewer component for code comparison."""
    
    def __init__(self, logger: Logger):
        """Initialize the diff viewer component.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.code_block = CodeBlock(logger)
        
    def compute_diff(self, old_code: str, new_code: str, context_lines: int = 3) -> Tuple[List[DiffLine], List[DiffLine]]:
        """Compute the diff between two pieces of code.
        
        Args:
            old_code: Old version of the code
            new_code: New version of the code
            context_lines: Number of context lines to show around changes
            
        Returns:
            Tuple of (old_lines, new_lines) where each is a list of DiffLine objects
        """
        old_lines = old_code.splitlines()
        new_lines = new_code.splitlines()
        
        # Use Python's difflib to compute the diff
        differ = difflib.Differ()
        diff = list(differ.compare(old_lines, new_lines))
        
        # Process the diff to create DiffLine objects
        result_old = []
        result_new = []
        
        old_line_num = 0
        new_line_num = 0
        
        for line in diff:
            code = line[2:]
            
            if line.startswith("  "):  # Unchanged line
                old_line_num += 1
                new_line_num += 1
                result_old.append(DiffLine(content=code, line_number=old_line_num, type="unchanged"))
                result_new.append(DiffLine(content=code, line_number=new_line_num, type="unchanged"))
            elif line.startswith("- "):  # Removed line
                old_line_num += 1
                result_old.append(DiffLine(content=code, line_number=old_line_num, type="removed"))
            elif line.startswith("+ "):  # Added line
                new_line_num += 1
                result_new.append(DiffLine(content=code, line_number=new_line_num, type="added"))
            elif line.startswith("? "):  # Hint line, ignore
                pass
        
        return result_old, result_new
    
    def compute_unified_diff(self, old_code: str, new_code: str, context_lines: int = 3) -> List[DiffLine]:
        """Compute a unified diff between two pieces of code.
        
        Args:
            old_code: Old version of the code
            new_code: New version of the code
            context_lines: Number of context lines to show around changes
            
        Returns:
            List of DiffLine objects for the unified diff
        """
        old_lines = old_code.splitlines()
        new_lines = new_code.splitlines()
        
        # Use Python's difflib to compute the unified diff
        diff = difflib.unified_diff(
            old_lines, 
            new_lines, 
            n=context_lines,
            lineterm=""
        )
        
        # Skip the first two lines (header)
        next(diff, None)
        next(diff, None)
        
        # Process the diff to create DiffLine objects
        result = []
        line_num = 0
        
        for line in diff:
            if line.startswith("+"):
                line_num += 1
                result.append(DiffLine(content=line[1:], line_number=line_num, type="added"))
            elif line.startswith("-"):
                line_num += 1
                result.append(DiffLine(content=line[1:], line_number=line_num, type="removed"))
            elif line.startswith(" "):
                line_num += 1
                result.append(DiffLine(content=line[1:], line_number=line_num, type="unchanged"))
            else:
                # Skip hunk headers
                pass
        
        return result
    
    def highlight_diff(self, diff_lines: List[DiffLine], language: str, theme: str) -> str:
        """Highlight a diff.
        
        Args:
            diff_lines: List of DiffLine objects
            language: Language for syntax highlighting
            theme: Theme for syntax highlighting
            
        Returns:
            HTML with highlighted diff
        """
        # Combine the lines into a single string
        code = "\n".join(line.content for line in diff_lines)
        
        try:
            lexer = get_lexer_by_name(language)
        except pygments.util.ClassNotFound:
            self.logger.warning(f"Language not found: {language}, falling back to text")
            lexer = get_lexer_by_name("text")
        
        # Get the style
        try:
            style = get_style_by_name(theme)
        except pygments.util.ClassNotFound:
            self.logger.warning(f"Style not found: {theme}, falling back to default")
            style = get_style_by_name("default")
        
        # Create formatter with line numbers
        formatter = HtmlFormatter(
            style=style,
            linenos="table",
            cssclass="parlant-diff-code",
            wrapcode=True,
        )
        
        # Highlight the code
        highlighted = pygments.highlight(code, lexer, formatter)
        
        # Add diff styling
        html_lines = highlighted.splitlines()
        result_lines = []
        
        # Find the line number and code parts
        in_tbody = False
        line_index = 0
        
        for html_line in html_lines:
            if "<tbody>" in html_line:
                in_tbody = True
                result_lines.append(html_line)
            elif "</tbody>" in html_line:
                in_tbody = False
                result_lines.append(html_line)
            elif in_tbody and "<tr>" in html_line:
                # This is a code line
                if line_index < len(diff_lines):
                    diff_type = diff_lines[line_index].type
                    line_class = f"parlant-diff-line-{diff_type}"
                    html_line = html_line.replace("<tr>", f'<tr class="{line_class}">')
                    line_index += 1
                result_lines.append(html_line)
            else:
                result_lines.append(html_line)
        
        return "\n".join(result_lines)
    
    def render_split_view(self, old_code: str, new_code: str, options: DiffViewerOptions) -> str:
        """Render a split view diff.
        
        Args:
            old_code: Old version of the code
            new_code: New version of the code
            options: Options for rendering
            
        Returns:
            HTML with split view diff
        """
        language = options.language or self.code_block.detect_language(new_code, options.file_name)
        old_lines, new_lines = self.compute_diff(old_code, new_code, options.context_lines)
        
        # Highlight both sides
        old_html = self.highlight_diff(old_lines, language, options.theme)
        new_html = self.highlight_diff(new_lines, language, options.theme)
        
        # Combine into a split view
        html = []
        html.append('<div class="parlant-diff-split-view">')
        
        # Old code side
        html.append('<div class="parlant-diff-old">')
        html.append('<div class="parlant-diff-header">Old</div>')
        html.append(old_html)
        html.append('</div>')
        
        # New code side
        html.append('<div class="parlant-diff-new">')
        html.append('<div class="parlant-diff-header">New</div>')
        html.append(new_html)
        html.append('</div>')
        
        html.append('</div>')
        
        return "\n".join(html)
    
    def render_unified_view(self, old_code: str, new_code: str, options: DiffViewerOptions) -> str:
        """Render a unified view diff.
        
        Args:
            old_code: Old version of the code
            new_code: New version of the code
            options: Options for rendering
            
        Returns:
            HTML with unified view diff
        """
        language = options.language or self.code_block.detect_language(new_code, options.file_name)
        unified_lines = self.compute_unified_diff(old_code, new_code, options.context_lines)
        
        # Highlight the unified diff
        unified_html = self.highlight_diff(unified_lines, language, options.theme)
        
        # Wrap in a container
        html = []
        html.append('<div class="parlant-diff-unified-view">')
        html.append(unified_html)
        html.append('</div>')
        
        return "\n".join(html)
    
    def render_html(self, old_code: str, new_code: str, options: Optional[DiffViewerOptions] = None) -> str:
        """Render the diff viewer as HTML.
        
        Args:
            old_code: Old version of the code
            new_code: New version of the code
            options: Options for rendering
            
        Returns:
            HTML representation of the diff viewer
        """
        if options is None:
            options = DiffViewerOptions()
        
        # Detect language if not specified
        language = options.language or self.code_block.detect_language(new_code, options.file_name)
        
        # Add container with file name and buttons
        html = []
        html.append('<div class="parlant-diff-container">')
        
        # Add header with file name and language
        html.append('<div class="parlant-diff-top-header">')
        
        if options.file_name:
            html.append(f'<div class="parlant-diff-filename">{options.file_name}</div>')
        
        html.append(f'<div class="parlant-diff-language">{language.upper()}</div>')
        
        html.append('</div>')  # End header
        
        # Add the diff view mode selector
        html.append('<div class="parlant-diff-mode-selector">')
        html.append('<label class="parlant-diff-mode-label">')
        html.append('<input type="radio" name="diff-mode" value="split" class="parlant-diff-mode-radio"')
        if options.diff_mode == DiffMode.SPLIT:
            html.append(' checked')
        html.append('> Split View')
        html.append('</label>')
        
        html.append('<label class="parlant-diff-mode-label">')
        html.append('<input type="radio" name="diff-mode" value="unified" class="parlant-diff-mode-radio"')
        if options.diff_mode == DiffMode.UNIFIED:
            html.append(' checked')
        html.append('> Unified View')
        html.append('</label>')
        
        if options.show_copy_button:
            html.append('<button class="parlant-diff-copy-button">Copy New</button>')
        
        html.append('</div>')  # End mode selector
        
        # Add the diff content
        html.append('<div class="parlant-diff-content">')
        
        if options.diff_mode == DiffMode.SPLIT:
            html.append(self.render_split_view(old_code, new_code, options))
        else:
            html.append(self.render_unified_view(old_code, new_code, options))
        
        html.append('</div>')  # End content
        
        html.append('</div>')  # End container
        
        return "\n".join(html)
    
    def get_css(self) -> str:
        """Get the CSS for the diff viewer component.
        
        Returns:
            CSS for the diff viewer component
        """
        css = """
        .parlant-diff-container {
            border: 1px solid #e2e8f0;
            border-radius: 0.375rem;
            margin: 1rem 0;
            overflow: hidden;
        }
        
        .parlant-diff-top-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 1rem;
            background-color: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .parlant-diff-filename {
            font-family: monospace;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .parlant-diff-language {
            font-size: 0.75rem;
            color: #64748b;
        }
        
        .parlant-diff-mode-selector {
            display: flex;
            align-items: center;
            padding: 0.5rem 1rem;
            background-color: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .parlant-diff-mode-label {
            margin-right: 1rem;
            font-size: 0.875rem;
            display: flex;
            align-items: center;
        }
        
        .parlant-diff-mode-radio {
            margin-right: 0.25rem;
        }
        
        .parlant-diff-copy-button {
            background-color: transparent;
            border: 1px solid #e2e8f0;
            border-radius: 0.25rem;
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
            margin-left: auto;
            cursor: pointer;
        }
        
        .parlant-diff-copy-button:hover {
            background-color: #e2e8f0;
        }
        
        .parlant-diff-content {
            overflow: auto;
        }
        
        .parlant-diff-split-view {
            display: flex;
            width: 100%;
        }
        
        .parlant-diff-old,
        .parlant-diff-new {
            flex: 1;
            overflow: auto;
            border-right: 1px solid #e2e8f0;
        }
        
        .parlant-diff-new {
            border-right: none;
        }
        
        .parlant-diff-header {
            padding: 0.5rem;
            background-color: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
            font-weight: 500;
            text-align: center;
        }
        
        .parlant-diff-code {
            margin: 0 !important;
        }
        
        .parlant-diff-code .linenodiv pre {
            margin: 0;
            padding: 0.5rem;
            border-right: 1px solid #e2e8f0;
            background-color: #f8fafc;
            color: #64748b;
            text-align: right;
        }
        
        .parlant-diff-code .code pre {
            margin: 0;
            padding: 0.5rem;
        }
        
        .parlant-diff-line-added {
            background-color: rgba(0, 255, 0, 0.1);
        }
        
        .parlant-diff-line-removed {
            background-color: rgba(255, 0, 0, 0.1);
        }
        
        /* Dark mode */
        @media (prefers-color-scheme: dark) {
            .parlant-diff-container {
                border-color: #334155;
            }
            
            .parlant-diff-top-header,
            .parlant-diff-mode-selector,
            .parlant-diff-header {
                background-color: #1e293b;
                border-bottom-color: #334155;
            }
            
            .parlant-diff-language {
                color: #94a3b8;
            }
            
            .parlant-diff-copy-button {
                border-color: #334155;
                color: #e2e8f0;
            }
            
            .parlant-diff-copy-button:hover {
                background-color: #334155;
            }
            
            .parlant-diff-old,
            .parlant-diff-new {
                border-right-color: #334155;
            }
            
            .parlant-diff-code .linenodiv pre {
                border-right-color: #334155;
                background-color: #1e293b;
                color: #94a3b8;
            }
            
            .parlant-diff-line-added {
                background-color: rgba(0, 255, 0, 0.05);
            }
            
            .parlant-diff-line-removed {
                background-color: rgba(255, 0, 0, 0.05);
            }
        }
        """
        
        return css
