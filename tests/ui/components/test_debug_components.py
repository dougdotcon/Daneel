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

"""Tests for debugging UI components."""

import pytest
from unittest.mock import MagicMock, patch

from Daneel.ui.components.debug import Inspector, InspectorOptions, ValueType, CallStack, CallStackOptions, StackFrame


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    return logger


class TestInspector:
    """Tests for the Inspector component."""
    
    def test_get_value_type(self, mock_logger):
        """Test value type detection."""
        inspector = Inspector(mock_logger)
        
        # Test various types
        assert inspector.get_value_type(None) == ValueType.NULL
        assert inspector.get_value_type("hello") == ValueType.STRING
        assert inspector.get_value_type(123) == ValueType.NUMBER
        assert inspector.get_value_type(True) == ValueType.BOOLEAN
        assert inspector.get_value_type([1, 2, 3]) == ValueType.ARRAY
        assert inspector.get_value_type({"a": 1}) == ValueType.OBJECT
        assert inspector.get_value_type({1, 2, 3}) == ValueType.SET
        
    def test_format_value(self, mock_logger):
        """Test value formatting."""
        inspector = Inspector(mock_logger)
        options = InspectorOptions()
        
        # Test formatting various types
        assert inspector.format_value(None, ValueType.NULL, options) == "null"
        assert inspector.format_value("hello", ValueType.STRING, options) == '"hello"'
        assert inspector.format_value(123, ValueType.NUMBER, options) == "123"
        assert inspector.format_value(True, ValueType.BOOLEAN, options) == "true"
        assert inspector.format_value([1, 2, 3], ValueType.ARRAY, options) == "Array(3)"
        assert inspector.format_value({"a": 1}, ValueType.OBJECT, options) == "Object"
        
        # Test string truncation
        long_string = "a" * 200
        assert len(inspector.format_value(long_string, ValueType.STRING, options)) < 200
        
    def test_get_object_properties(self, mock_logger):
        """Test getting object properties."""
        inspector = Inspector(mock_logger)
        options = InspectorOptions()
        
        # Test getting properties of an array
        array = [1, 2, 3]
        properties = inspector.get_object_properties(array, ValueType.ARRAY, options)
        assert len(properties) == 3
        assert properties["0"] == 1
        assert properties["1"] == 2
        assert properties["2"] == 3
        
        # Test getting properties of an object
        obj = {"a": 1, "b": 2}
        properties = inspector.get_object_properties(obj, ValueType.OBJECT, options)
        assert len(properties) >= 2
        assert "a" in properties
        assert "b" in properties
        assert properties["a"] == 1
        assert properties["b"] == 2
        
    def test_is_expandable(self, mock_logger):
        """Test checking if a type is expandable."""
        inspector = Inspector(mock_logger)
        
        # Test expandable types
        assert inspector.is_expandable(ValueType.OBJECT)
        assert inspector.is_expandable(ValueType.ARRAY)
        assert inspector.is_expandable(ValueType.MAP)
        assert inspector.is_expandable(ValueType.SET)
        assert inspector.is_expandable(ValueType.CLASS)
        assert inspector.is_expandable(ValueType.DATACLASS)
        
        # Test non-expandable types
        assert not inspector.is_expandable(ValueType.STRING)
        assert not inspector.is_expandable(ValueType.NUMBER)
        assert not inspector.is_expandable(ValueType.BOOLEAN)
        assert not inspector.is_expandable(ValueType.NULL)
        
    def test_render_object(self, mock_logger):
        """Test rendering an object."""
        inspector = Inspector(mock_logger)
        options = InspectorOptions(expand_level=1)
        
        # Test rendering a simple object
        obj = {"a": 1, "b": "hello"}
        html = inspector.render_object("test", obj, 0, options)
        
        # Check that the HTML contains the expected elements
        assert "Daneel-inspector-property" in html
        assert "Daneel-inspector-property-header" in html
        assert "Daneel-inspector-property-name" in html
        assert "Daneel-inspector-property-value" in html
        assert "Daneel-inspector-property-children" in html
        assert "test" in html
        assert "Object" in html
        assert "a" in html
        assert "b" in html
        assert "1" in html
        assert "hello" in html
        
    def test_render_html(self, mock_logger):
        """Test HTML rendering."""
        inspector = Inspector(mock_logger)
        options = InspectorOptions(
            expand_level=1,
            title="Test Inspector",
            theme="dark",
        )
        
        # Test rendering a complex object
        data = {
            "string": "hello",
            "number": 123,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "object": {"a": 1, "b": 2},
        }
        
        html = inspector.render_html(data, options)
        
        # Check that the HTML contains the expected elements
        assert "Daneel-inspector-container" in html
        assert "Daneel-inspector-dark" in html
        assert "Daneel-inspector-title" in html
        assert "Daneel-inspector-content" in html
        assert "Test Inspector" in html
        assert "string" in html
        assert "number" in html
        assert "boolean" in html
        assert "null" in html
        assert "array" in html
        assert "object" in html
        
    def test_get_css(self, mock_logger):
        """Test CSS generation."""
        inspector = Inspector(mock_logger)
        css = inspector.get_css()
        
        # Check that the CSS contains the expected selectors
        assert ".Daneel-inspector-container" in css
        assert ".Daneel-inspector-light" in css
        assert ".Daneel-inspector-dark" in css
        assert ".Daneel-inspector-title" in css
        assert ".Daneel-inspector-content" in css
        assert ".Daneel-inspector-property" in css
        assert ".Daneel-inspector-property-header" in css
        assert ".Daneel-inspector-expand-button" in css
        assert ".Daneel-inspector-property-name" in css
        assert ".Daneel-inspector-property-value" in css
        assert ".Daneel-inspector-property-children" in css
        assert ".Daneel-inspector-string" in css
        assert ".Daneel-inspector-number" in css
        assert ".Daneel-inspector-boolean" in css
        assert ".Daneel-inspector-null" in css


class TestCallStack:
    """Tests for the CallStack component."""
    
    def test_get_current_stack_frames(self, mock_logger):
        """Test getting current stack frames."""
        call_stack = CallStack(mock_logger)
        
        # Get the current stack frames
        frames = call_stack.get_current_stack_frames()
        
        # Check that we got some frames
        assert len(frames) > 0
        
        # Check that the frames have the expected properties
        for frame in frames:
            assert frame.function_name
            assert frame.file_name
            assert frame.line_number > 0
            
    def test_get_exception_stack_frames(self, mock_logger):
        """Test getting exception stack frames."""
        call_stack = CallStack(mock_logger)
        
        try:
            # Generate an exception
            raise ValueError("Test exception")
        except ValueError as e:
            # Get the stack frames from the exception
            frames = call_stack.get_exception_stack_frames(e)
            
            # Check that we got some frames
            assert len(frames) > 0
            
            # Check that the frames have the expected properties
            for frame in frames:
                assert frame.function_name
                assert frame.file_name
                assert frame.line_number > 0
                
    def test_render_frame(self, mock_logger):
        """Test rendering a stack frame."""
        call_stack = CallStack(mock_logger)
        options = CallStackOptions()
        
        # Create a stack frame
        frame = StackFrame(
            function_name="test_function",
            file_name="test_file.py",
            line_number=42,
            source="print('Hello')",
            variables={"x": 1, "y": "hello"},
        )
        
        # Render the frame
        html = call_stack.render_frame(frame, 0, True, options)
        
        # Check that the HTML contains the expected elements
        assert "Daneel-call-stack-frame" in html
        assert "Daneel-call-stack-frame-selected" in html
        assert "Daneel-call-stack-frame-header" in html
        assert "Daneel-call-stack-function-name" in html
        assert "Daneel-call-stack-location" in html
        assert "Daneel-call-stack-frame-details" in html
        assert "Daneel-call-stack-source" in html
        assert "Daneel-call-stack-variables" in html
        assert "test_function" in html
        assert "test_file.py:42" in html
        assert "x" in html
        assert "y" in html
        assert "1" in html
        assert "hello" in html
        
    def test_render_html(self, mock_logger):
        """Test HTML rendering."""
        call_stack = CallStack(mock_logger)
        options = CallStackOptions(
            title="Test Call Stack",
            theme="dark",
        )
        
        # Create some stack frames
        frames = [
            StackFrame(
                function_name="main",
                file_name="main.py",
                line_number=10,
                source="result = calculate(x, y)",
            ),
            StackFrame(
                function_name="calculate",
                file_name="math_utils.py",
                line_number=42,
                source="return x + y",
                variables={"x": 1, "y": 2},
            ),
        ]
        
        # Render the call stack
        html = call_stack.render_html(frames, options)
        
        # Check that the HTML contains the expected elements
        assert "Daneel-call-stack-container" in html
        assert "Daneel-call-stack-dark" in html
        assert "Daneel-call-stack-title" in html
        assert "Daneel-call-stack-content" in html
        assert "Test Call Stack" in html
        assert "main" in html
        assert "calculate" in html
        assert "main.py:10" in html
        assert "math_utils.py:42" in html
        
    def test_get_css(self, mock_logger):
        """Test CSS generation."""
        call_stack = CallStack(mock_logger)
        css = call_stack.get_css()
        
        # Check that the CSS contains the expected selectors
        assert ".Daneel-call-stack-container" in css
        assert ".Daneel-call-stack-light" in css
        assert ".Daneel-call-stack-dark" in css
        assert ".Daneel-call-stack-title" in css
        assert ".Daneel-call-stack-content" in css
        assert ".Daneel-call-stack-frame" in css
        assert ".Daneel-call-stack-frame-header" in css
        assert ".Daneel-call-stack-function-name" in css
        assert ".Daneel-call-stack-location" in css
        assert ".Daneel-call-stack-frame-details" in css
        assert ".Daneel-call-stack-source" in css
        assert ".Daneel-call-stack-variables" in css
