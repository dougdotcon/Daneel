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

"""Tests for code-related UI components."""

import pytest
from unittest.mock import MagicMock

from Daneel.ui.components.code import CodeBlock, CodeBlockOptions, DiffViewer, DiffViewerOptions, DiffMode


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    return logger


class TestCodeBlock:
    """Tests for the CodeBlock component."""
    
    def test_detect_language(self, mock_logger):
        """Test language detection."""
        code_block = CodeBlock(mock_logger)
        
        # Test detection from file name
        assert code_block.detect_language("print('Hello')", "test.py") == "python"
        assert code_block.detect_language("console.log('Hello')", "test.js") == "javascript"
        assert code_block.detect_language("<html></html>", "test.html") == "html"
        
        # Test detection from code patterns
        assert code_block.detect_language("import React from 'react'") == "jsx"
        assert code_block.detect_language("def hello():\n    print('Hello')") == "python"
        assert code_block.detect_language("public class Test {}") == "java"
        assert code_block.detect_language("#include <stdio.h>") == "cpp"
        assert code_block.detect_language("SELECT * FROM users") == "sql"
        
    def test_highlight_code(self, mock_logger):
        """Test code highlighting."""
        code_block = CodeBlock(mock_logger)
        options = CodeBlockOptions(language="python", show_line_numbers=True)
        
        code = "def hello():\n    print('Hello')"
        highlighted = code_block.highlight_code(code, options)
        
        # Check that the code was highlighted
        assert "def" in highlighted
        assert "print" in highlighted
        assert "Hello" in highlighted
        
        # Check that line numbers are included
        assert "1" in highlighted
        assert "2" in highlighted
        
    def test_render_html(self, mock_logger):
        """Test HTML rendering."""
        code_block = CodeBlock(mock_logger)
        options = CodeBlockOptions(
            language="python",
            show_line_numbers=True,
            show_copy_button=True,
            file_name="test.py",
        )
        
        code = "def hello():\n    print('Hello')"
        html = code_block.render_html(code, options)
        
        # Check that the HTML contains the expected elements
        assert "Daneel-code-block-container" in html
        assert "Daneel-code-block-header" in html
        assert "Daneel-code-block-filename" in html
        assert "Daneel-code-block-content" in html
        assert "Daneel-code-block-footer" in html
        assert "Daneel-code-block-copy-button" in html
        assert "test.py" in html
        assert "PYTHON" in html
        
    def test_get_css(self, mock_logger):
        """Test CSS generation."""
        code_block = CodeBlock(mock_logger)
        css = code_block.get_css()
        
        # Check that the CSS contains the expected selectors
        assert ".Daneel-code-block-container" in css
        assert ".Daneel-code-block-header" in css
        assert ".Daneel-code-block-filename" in css
        assert ".Daneel-code-block-content" in css
        assert ".Daneel-code-block-footer" in css
        assert ".Daneel-code-block-copy-button" in css


class TestDiffViewer:
    """Tests for the DiffViewer component."""
    
    def test_compute_diff(self, mock_logger):
        """Test diff computation."""
        diff_viewer = DiffViewer(mock_logger)
        
        old_code = "line 1\nline 2\nline 3"
        new_code = "line 1\nmodified line\nline 3"
        
        old_lines, new_lines = diff_viewer.compute_diff(old_code, new_code)
        
        # Check that the diff was computed correctly
        assert len(old_lines) == 3
        assert len(new_lines) == 3
        
        assert old_lines[0].type == "unchanged"
        assert old_lines[0].content == "line 1"
        
        assert old_lines[1].type == "removed"
        assert old_lines[1].content == "line 2"
        
        assert old_lines[2].type == "unchanged"
        assert old_lines[2].content == "line 3"
        
        assert new_lines[0].type == "unchanged"
        assert new_lines[0].content == "line 1"
        
        assert new_lines[1].type == "added"
        assert new_lines[1].content == "modified line"
        
        assert new_lines[2].type == "unchanged"
        assert new_lines[2].content == "line 3"
        
    def test_compute_unified_diff(self, mock_logger):
        """Test unified diff computation."""
        diff_viewer = DiffViewer(mock_logger)
        
        old_code = "line 1\nline 2\nline 3"
        new_code = "line 1\nmodified line\nline 3"
        
        unified_lines = diff_viewer.compute_unified_diff(old_code, new_code)
        
        # Check that the unified diff was computed correctly
        assert len(unified_lines) > 0
        
        # Find the removed and added lines
        removed_line = None
        added_line = None
        
        for line in unified_lines:
            if line.type == "removed":
                removed_line = line
            elif line.type == "added":
                added_line = line
                
        assert removed_line is not None
        assert removed_line.content == "line 2"
        
        assert added_line is not None
        assert added_line.content == "modified line"
        
    def test_render_split_view(self, mock_logger):
        """Test split view rendering."""
        diff_viewer = DiffViewer(mock_logger)
        options = DiffViewerOptions(
            language="python",
            show_line_numbers=True,
            diff_mode=DiffMode.SPLIT,
        )
        
        old_code = "def hello():\n    print('Hello')"
        new_code = "def hello():\n    print('Hello, world!')"
        
        html = diff_viewer.render_split_view(old_code, new_code, options)
        
        # Check that the HTML contains the expected elements
        assert "Daneel-diff-split-view" in html
        assert "Daneel-diff-old" in html
        assert "Daneel-diff-new" in html
        assert "Daneel-diff-header" in html
        assert "Old" in html
        assert "New" in html
        
    def test_render_unified_view(self, mock_logger):
        """Test unified view rendering."""
        diff_viewer = DiffViewer(mock_logger)
        options = DiffViewerOptions(
            language="python",
            show_line_numbers=True,
            diff_mode=DiffMode.UNIFIED,
        )
        
        old_code = "def hello():\n    print('Hello')"
        new_code = "def hello():\n    print('Hello, world!')"
        
        html = diff_viewer.render_unified_view(old_code, new_code, options)
        
        # Check that the HTML contains the expected elements
        assert "Daneel-diff-unified-view" in html
        
    def test_render_html(self, mock_logger):
        """Test HTML rendering."""
        diff_viewer = DiffViewer(mock_logger)
        options = DiffViewerOptions(
            language="python",
            show_line_numbers=True,
            show_copy_button=True,
            file_name="test.py",
            diff_mode=DiffMode.SPLIT,
        )
        
        old_code = "def hello():\n    print('Hello')"
        new_code = "def hello():\n    print('Hello, world!')"
        
        html = diff_viewer.render_html(old_code, new_code, options)
        
        # Check that the HTML contains the expected elements
        assert "Daneel-diff-container" in html
        assert "Daneel-diff-top-header" in html
        assert "Daneel-diff-filename" in html
        assert "Daneel-diff-content" in html
        assert "Daneel-diff-mode-selector" in html
        assert "Daneel-diff-copy-button" in html
        assert "test.py" in html
        assert "PYTHON" in html
        assert "Split View" in html
        assert "Unified View" in html
        
    def test_get_css(self, mock_logger):
        """Test CSS generation."""
        diff_viewer = DiffViewer(mock_logger)
        css = diff_viewer.get_css()
        
        # Check that the CSS contains the expected selectors
        assert ".Daneel-diff-container" in css
        assert ".Daneel-diff-top-header" in css
        assert ".Daneel-diff-filename" in css
        assert ".Daneel-diff-content" in css
        assert ".Daneel-diff-mode-selector" in css
        assert ".Daneel-diff-copy-button" in css
        assert ".Daneel-diff-split-view" in css
        assert ".Daneel-diff-unified-view" in css
        assert ".Daneel-diff-old" in css
        assert ".Daneel-diff-new" in css
        assert ".Daneel-diff-line-added" in css
        assert ".Daneel-diff-line-removed" in css
