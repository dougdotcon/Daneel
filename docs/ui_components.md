# UI Components

This document describes the UI components in the Parlant framework.

## Overview

The UI components provide a way to create rich, interactive user interfaces for Parlant. They support:

1. Code highlighting and diff visualization
2. Interactive terminal interfaces
3. Debugging and inspection tools
4. Visual feedback for agent actions

## Components

### Code Components

#### CodeBlock

The `CodeBlock` component provides syntax highlighting for code snippets. It supports:

- Automatic language detection
- Line numbers
- Copy to clipboard functionality
- Code folding for large code blocks
- Highlighting specific lines
- Multiple themes

Example usage:

```python
from parlant.ui.components.code import CodeBlock, CodeBlockOptions
from parlant.core.loggers import ConsoleLogger

# Create a code block
code_block = CodeBlock(ConsoleLogger())

# Configure options
options = CodeBlockOptions(
    language="python",
    show_line_numbers=True,
    show_copy_button=True,
    show_collapse_button=True,
    max_height=500,
    file_name="example.py",
    highlight_lines=[3, 5],
    theme="default",
)

# Render the code block
code = """
def hello():
    print("Hello, world!")
    
if __name__ == "__main__":
    hello()
"""

html = code_block.render_html(code, options)
```

#### DiffViewer

The `DiffViewer` component visualizes differences between two pieces of code. It supports:

- Split view (side-by-side) and unified view
- Syntax highlighting
- Line numbers
- Color-coding for additions, deletions, and modifications
- Multiple themes

Example usage:

```python
from parlant.ui.components.code import DiffViewer, DiffViewerOptions, DiffMode
from parlant.core.loggers import ConsoleLogger

# Create a diff viewer
diff_viewer = DiffViewer(ConsoleLogger())

# Configure options
options = DiffViewerOptions(
    language="python",
    show_line_numbers=True,
    show_copy_button=True,
    file_name="example.py",
    diff_mode=DiffMode.SPLIT,
    theme="default",
    context_lines=3,
)

# Render the diff
old_code = """
def hello():
    print("Hello, world!")
"""

new_code = """
def hello():
    print("Hello, universe!")
"""

html = diff_viewer.render_html(old_code, new_code, options)
```

### Terminal Components

#### Terminal

The `Terminal` component provides an interactive terminal interface. It supports:

- Command execution
- Command history
- Syntax highlighting for terminal output
- Copy to clipboard functionality
- Fullscreen mode
- Custom command handlers
- Multiple themes

Example usage:

```python
from parlant.ui.components.terminal import Terminal, TerminalOptions, TerminalState
from parlant.core.loggers import ConsoleLogger

# Create a terminal
terminal = Terminal(ConsoleLogger())

# Register a custom command handler
def handle_hello(command):
    return "Hello, world!"
    
terminal.register_command_handler("hello", handle_hello)

# Configure options
options = TerminalOptions(
    prompt="$ ",
    initial_content="Welcome to the terminal!",
    max_height=300,
    title="Example Terminal",
    read_only=False,
    auto_focus=True,
    theme="dark",
    show_copy_button=True,
    show_clear_button=True,
    show_fullscreen_button=True,
    history_size=100,
    working_directory="/path/to/workspace",
)

# Render the terminal
html = terminal.render_html(options)

# Execute a command
output = await terminal.execute_command("echo Hello, world!")
```

### Debug Components

#### Inspector

The `Inspector` component provides a way to inspect variables and objects. It supports:

- Expandable object properties
- Syntax highlighting for values
- Customizable expansion level
- Multiple themes
- Filtering of private and method properties

Example usage:

```python
from parlant.ui.components.debug import Inspector, InspectorOptions
from parlant.core.loggers import ConsoleLogger

# Create an inspector
inspector = Inspector(ConsoleLogger())

# Configure options
options = InspectorOptions(
    expand_level=1,
    max_depth=10,
    max_string_length=100,
    max_array_length=100,
    title="Example Inspector",
    theme="default",
    show_private=False,
    show_methods=False,
    show_dunder=False,
)

# Render the inspector
data = {
    "string": "hello",
    "number": 123,
    "boolean": True,
    "null": None,
    "array": [1, 2, 3],
    "object": {"a": 1, "b": 2},
}

html = inspector.render_html(data, options)
```

#### CallStack

The `CallStack` component visualizes a call stack for debugging. It supports:

- Stack frame visualization
- Source code display
- Variable inspection
- Multiple themes
- Filtering of library frames

Example usage:

```python
from parlant.ui.components.debug import CallStack, CallStackOptions, StackFrame
from parlant.core.loggers import ConsoleLogger

# Create a call stack
call_stack = CallStack(ConsoleLogger())

# Configure options
options = CallStackOptions(
    title="Example Call Stack",
    theme="default",
    max_height=500,
    show_library_frames=False,
    show_variables=True,
    show_source=True,
    context_lines=3,
)

# Create stack frames
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

# Get the current stack frames
current_frames = call_stack.get_current_stack_frames()

# Get stack frames from an exception
try:
    raise ValueError("Example error")
except ValueError as e:
    exception_frames = call_stack.get_exception_stack_frames(e)
```

## Integration with Parlant

The UI components are integrated with the Parlant framework:

1. **Web Interface**: The components are used in the web interface to provide a rich user experience
2. **Agent Feedback**: The components provide visual feedback for agent actions
3. **Debugging**: The components help with debugging agent behavior
4. **Code Editing**: The components enhance the code editing experience

## CSS Styling

Each component provides its own CSS styling through the `get_css()` method. This allows the components to be styled consistently across different environments.

Example:

```python
from parlant.ui.components.code import CodeBlock
from parlant.core.loggers import ConsoleLogger

# Create a code block
code_block = CodeBlock(ConsoleLogger())

# Get the CSS
css = code_block.get_css()

# Include the CSS in your HTML
html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        {css}
    </style>
</head>
<body>
    {code_block.render_html("print('Hello, world!')")}
</body>
</html>
"""
```

## JavaScript Integration

The UI components are designed to work with JavaScript for enhanced interactivity. The JavaScript code can be included in your HTML to enable features like:

- Expanding and collapsing code blocks
- Switching between split and unified diff views
- Executing commands in the terminal
- Expanding and collapsing object properties in the inspector
- Selecting stack frames in the call stack

Example JavaScript for the CodeBlock component:

```javascript
// Enable copy button functionality
document.querySelectorAll('.parlant-code-block-copy-button').forEach(button => {
    button.addEventListener('click', () => {
        const codeBlock = button.closest('.parlant-code-block-container');
        const code = codeBlock.querySelector('.parlant-code-block-content').textContent;
        
        navigator.clipboard.writeText(code).then(() => {
            button.textContent = 'Copied!';
            setTimeout(() => {
                button.textContent = 'Copy';
            }, 2000);
        });
    });
});

// Enable collapse button functionality
document.querySelectorAll('.parlant-code-block-collapse-button').forEach(button => {
    button.addEventListener('click', () => {
        const codeBlock = button.closest('.parlant-code-block-container');
        const content = codeBlock.querySelector('.parlant-code-block-content');
        
        if (content.style.maxHeight === '100px') {
            content.style.maxHeight = '500px';
            button.textContent = 'Collapse';
        } else {
            content.style.maxHeight = '100px';
            button.textContent = 'Expand';
        }
    });
});
```

## Accessibility

The UI components are designed with accessibility in mind. They include:

- Proper ARIA attributes
- Keyboard navigation
- High contrast themes
- Screen reader support

## Future Enhancements

Future enhancements to the UI components may include:

1. **More Themes**: Additional themes for different environments
2. **More Languages**: Support for more programming languages
3. **More Interactive Features**: Enhanced interactivity with JavaScript
4. **Mobile Support**: Better support for mobile devices
5. **Accessibility Improvements**: Enhanced accessibility features
