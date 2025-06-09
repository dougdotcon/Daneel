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

"""Tests for the code tools."""

import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from Daneel.core.tools.code import (
    code_search,
    code_semantic_search,
    find_definition,
    read_file,
    write_file,
    edit_file,
    create_file,
    delete_file,
    execute_python,
    execute_shell,
    run_tests,
    execute_code_snippet,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        with open(os.path.join(temp_dir, "test_file.py"), "w") as f:
            f.write("def test_function():\n    return 'Hello, world!'\n")
        
        # Create a test directory
        os.makedirs(os.path.join(temp_dir, "test_dir"))
        
        # Change to the temporary directory
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        yield temp_dir
        
        # Change back to the original directory
        os.chdir(old_cwd)


def test_read_file(temp_dir):
    """Test reading a file."""
    # Read the test file
    result = read_file("test_file.py")
    
    # Check that the file was read
    assert result.data["content"] == "def test_function():\n    return 'Hello, world!'\n"
    assert result.data["file_path"] == "test_file.py"
    assert result.data["line_range"]["start"] == 1
    assert result.data["line_range"]["end"] == 2
    assert result.data["total_lines"] == 2
    
    # Read a specific line range
    result = read_file("test_file.py", start_line=1, end_line=1)
    
    # Check that the line range was read
    assert result.data["content"] == "def test_function():\n"
    assert result.data["line_range"]["start"] == 1
    assert result.data["line_range"]["end"] == 1
    
    # Read a non-existent file
    result = read_file("non_existent_file.py")
    
    # Check that an error was returned
    assert "error" in result.data
    assert "File not found" in result.data["error"]


def test_write_file(temp_dir):
    """Test writing a file."""
    # Write a new file
    result = write_file("new_file.py", "print('Hello, world!')")
    
    # Check that the file was written
    assert result.data["success"] is True
    assert result.data["file_path"] == "new_file.py"
    assert os.path.exists("new_file.py")
    
    # Check the file content
    with open("new_file.py", "r") as f:
        content = f.read()
    assert content == "print('Hello, world!')"
    
    # Append to the file
    result = write_file("new_file.py", "\nprint('Goodbye, world!')", mode="a")
    
    # Check that the file was appended
    assert result.data["success"] is True
    
    # Check the file content
    with open("new_file.py", "r") as f:
        content = f.read()
    assert content == "print('Hello, world!')\nprint('Goodbye, world!')"


def test_edit_file(temp_dir):
    """Test editing a file."""
    # Edit the test file
    result = edit_file(
        "test_file.py",
        start_line=1,
        end_line=2,
        new_content="def new_function():\n    return 'Goodbye, world!'\n",
    )
    
    # Check that the file was edited
    assert result.data["success"] is True
    assert result.data["file_path"] == "test_file.py"
    assert result.data["line_range"]["start"] == 1
    assert result.data["line_range"]["end"] == 2
    
    # Check the file content
    with open("test_file.py", "r") as f:
        content = f.read()
    assert content == "def new_function():\n    return 'Goodbye, world!'\n"
    
    # Edit a non-existent file
    result = edit_file(
        "non_existent_file.py",
        start_line=1,
        end_line=1,
        new_content="print('Hello, world!')",
    )
    
    # Check that an error was returned
    assert "error" in result.data
    assert "File not found" in result.data["error"]
    
    # Edit with invalid line range
    result = edit_file(
        "test_file.py",
        start_line=10,
        end_line=20,
        new_content="print('Hello, world!')",
    )
    
    # Check that an error was returned
    assert "error" in result.data
    assert "Invalid line range" in result.data["error"]


def test_create_file(temp_dir):
    """Test creating a file."""
    # Create a new file
    result = create_file("new_file.py", "print('Hello, world!')")
    
    # Check that the file was created
    assert result.data["success"] is True
    assert result.data["file_path"] == "new_file.py"
    assert os.path.exists("new_file.py")
    
    # Check the file content
    with open("new_file.py", "r") as f:
        content = f.read()
    assert content == "print('Hello, world!')"
    
    # Create a file that already exists
    result = create_file("new_file.py", "print('Goodbye, world!')")
    
    # Check that an error was returned
    assert "error" in result.data
    assert "File already exists" in result.data["error"]
    
    # Create a file with overwrite
    result = create_file("new_file.py", "print('Goodbye, world!')", overwrite=True)
    
    # Check that the file was overwritten
    assert result.data["success"] is True
    assert result.data["overwritten"] is True
    
    # Check the file content
    with open("new_file.py", "r") as f:
        content = f.read()
    assert content == "print('Goodbye, world!')"


def test_delete_file(temp_dir):
    """Test deleting a file."""
    # Create a new file
    with open("file_to_delete.py", "w") as f:
        f.write("print('Hello, world!')")
    
    # Delete the file
    result = delete_file("file_to_delete.py")
    
    # Check that the file was deleted
    assert result.data["success"] is True
    assert result.data["file_path"] == "file_to_delete.py"
    assert not os.path.exists("file_to_delete.py")
    
    # Delete a non-existent file
    result = delete_file("non_existent_file.py")
    
    # Check that an error was returned
    assert "error" in result.data
    assert "File not found" in result.data["error"]


@patch("subprocess.run")
def test_execute_python(mock_run, temp_dir):
    """Test executing Python code."""
    # Mock the subprocess.run result
    mock_result = MagicMock()
    mock_result.stdout = "Hello, world!"
    mock_result.stderr = ""
    mock_result.returncode = 0
    mock_run.return_value = mock_result
    
    # Execute Python code
    result = execute_python("print('Hello, world!')")
    
    # Check that the code was executed
    assert result.data["stdout"] == "Hello, world!"
    assert result.data["stderr"] == ""
    assert result.data["exit_code"] == 0
    assert result.data["success"] is True
    
    # Check that subprocess.run was called
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert len(args) == 1
    assert args[0][0] == "python"
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["timeout"] == 10
    assert kwargs["check"] is False


@patch("subprocess.run")
def test_execute_shell(mock_run, temp_dir):
    """Test executing a shell command."""
    # Mock the subprocess.run result
    mock_result = MagicMock()
    mock_result.stdout = "Hello, world!"
    mock_result.stderr = ""
    mock_result.returncode = 0
    mock_run.return_value = mock_result
    
    # Execute a shell command
    result = execute_shell("echo 'Hello, world!'")
    
    # Check that the command was executed
    assert result.data["stdout"] == "Hello, world!"
    assert result.data["stderr"] == ""
    assert result.data["exit_code"] == 0
    assert result.data["success"] is True
    assert result.data["command"] == "echo 'Hello, world!'"
    assert result.data["working_dir"] == "."
    
    # Check that subprocess.run was called
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert args[0] == "echo 'Hello, world!'"
    assert kwargs["shell"] is True
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["timeout"] == 10
    assert kwargs["check"] is False
    assert kwargs["cwd"] == "."


@patch("subprocess.run")
def test_run_tests(mock_run, temp_dir):
    """Test running tests."""
    # Mock the subprocess.run result
    mock_result = MagicMock()
    mock_result.stdout = "Ran 1 test in 0.001s\n\nOK"
    mock_result.stderr = ""
    mock_result.returncode = 0
    mock_run.return_value = mock_result
    
    # Run tests
    result = run_tests("tests/")
    
    # Check that the tests were run
    assert result.data["stdout"] == "Ran 1 test in 0.001s\n\nOK"
    assert result.data["stderr"] == ""
    assert result.data["exit_code"] == 0
    assert result.data["success"] is True
    assert result.data["test_path"] == "tests/"
    assert result.data["test_framework"] == "pytest"
    
    # Check that subprocess.run was called
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert args[0] == "python -m pytest tests/ "
    assert kwargs["shell"] is True
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["timeout"] == 60
    assert kwargs["check"] is False


@patch("subprocess.run")
def test_execute_code_snippet(mock_run, temp_dir):
    """Test executing a code snippet."""
    # Mock the subprocess.run result
    mock_result = MagicMock()
    mock_result.stdout = "Hello, world!"
    mock_result.stderr = ""
    mock_result.returncode = 0
    mock_run.return_value = mock_result
    
    # Execute a code snippet
    result = execute_code_snippet("print('Hello, world!')", "python")
    
    # Check that the code was executed
    assert result.data["stdout"] == "Hello, world!"
    assert result.data["stderr"] == ""
    assert result.data["exit_code"] == 0
    assert result.data["success"] is True
    assert result.data["language"] == "python"
    
    # Check that subprocess.run was called
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert len(args) == 1
    assert args[0][0] == "python"
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["timeout"] == 10
    assert kwargs["check"] is False
