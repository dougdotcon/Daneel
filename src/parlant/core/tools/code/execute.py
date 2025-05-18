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

"""Code execution tools for Parlant."""

import os
import subprocess
import tempfile
from typing import Dict, List, Optional, Union

from parlant.core.tools import ToolResult
from parlant.core.tools.tool_registry import ToolCategory, tool


@tool(
    id="execute_python",
    name="Execute Python",
    description="Execute Python code and return the result",
    parameters={
        "code": {
            "type": "string",
            "description": "Python code to execute",
            "examples": ["print('Hello, world!')", "import math\nprint(math.sqrt(16))"],
        },
        "timeout": {
            "type": "integer",
            "description": "Timeout in seconds",
            "examples": [5, 10, 30],
        },
    },
    required=["code"],
    category=ToolCategory.CODE,
    tags=["execute", "python", "code"],
)
def execute_python(
    code: str,
    timeout: int = 10,
) -> ToolResult:
    """Execute Python code and return the result.
    
    Args:
        code: Python code to execute
        timeout: Timeout in seconds
        
    Returns:
        Execution result
    """
    try:
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name
        
        try:
            # Execute the code
            result = subprocess.run(
                ["python", temp_file_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            
            return ToolResult(
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode,
                    "success": result.returncode == 0,
                }
            )
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
    except subprocess.TimeoutExpired:
        return ToolResult(
            data={
                "error": f"Execution timed out after {timeout} seconds",
                "timeout": timeout,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to execute Python code: {str(e)}",
            }
        )


@tool(
    id="execute_shell",
    name="Execute Shell",
    description="Execute a shell command and return the result",
    parameters={
        "command": {
            "type": "string",
            "description": "Shell command to execute",
            "examples": ["ls -la", "echo 'Hello, world!'"],
        },
        "working_dir": {
            "type": "string",
            "description": "Working directory for the command",
            "examples": [".", "src", "/tmp"],
        },
        "timeout": {
            "type": "integer",
            "description": "Timeout in seconds",
            "examples": [5, 10, 30],
        },
    },
    required=["command"],
    category=ToolCategory.CODE,
    tags=["execute", "shell", "code"],
    consequential=True,
)
def execute_shell(
    command: str,
    working_dir: str = ".",
    timeout: int = 10,
) -> ToolResult:
    """Execute a shell command and return the result.
    
    Args:
        command: Shell command to execute
        working_dir: Working directory for the command
        timeout: Timeout in seconds
        
    Returns:
        Execution result
    """
    try:
        # Execute the command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            cwd=working_dir,
        )
        
        return ToolResult(
            data={
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "success": result.returncode == 0,
                "command": command,
                "working_dir": working_dir,
            }
        )
    except subprocess.TimeoutExpired:
        return ToolResult(
            data={
                "error": f"Execution timed out after {timeout} seconds",
                "timeout": timeout,
                "command": command,
                "working_dir": working_dir,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to execute shell command: {str(e)}",
                "command": command,
                "working_dir": working_dir,
            }
        )


@tool(
    id="run_tests",
    name="Run Tests",
    description="Run tests for a project",
    parameters={
        "test_path": {
            "type": "string",
            "description": "Path to the test file or directory",
            "examples": ["tests/", "tests/test_main.py"],
        },
        "test_framework": {
            "type": "string",
            "description": "Test framework to use",
            "examples": ["pytest", "unittest", "jest"],
            "enum": ["pytest", "unittest", "jest", "mocha", "auto"],
        },
        "options": {
            "type": "string",
            "description": "Additional options for the test command",
            "examples": ["-v", "--verbose", "-k test_specific"],
        },
        "timeout": {
            "type": "integer",
            "description": "Timeout in seconds",
            "examples": [30, 60, 120],
        },
    },
    required=["test_path"],
    category=ToolCategory.CODE,
    tags=["test", "execute", "code"],
)
def run_tests(
    test_path: str,
    test_framework: str = "auto",
    options: str = "",
    timeout: int = 60,
) -> ToolResult:
    """Run tests for a project.
    
    Args:
        test_path: Path to the test file or directory
        test_framework: Test framework to use
        options: Additional options for the test command
        timeout: Timeout in seconds
        
    Returns:
        Test results
    """
    try:
        # Normalize test path
        test_path = os.path.normpath(test_path)
        
        # Determine the test framework if auto
        if test_framework == "auto":
            if os.path.exists("pytest.ini") or os.path.exists("conftest.py"):
                test_framework = "pytest"
            elif os.path.exists("package.json"):
                with open("package.json", "r") as f:
                    content = f.read()
                    if "jest" in content:
                        test_framework = "jest"
                    elif "mocha" in content:
                        test_framework = "mocha"
                    else:
                        test_framework = "jest"  # Default for JavaScript
            else:
                test_framework = "pytest"  # Default
        
        # Build the test command
        if test_framework == "pytest":
            command = f"python -m pytest {test_path} {options}"
        elif test_framework == "unittest":
            if os.path.isdir(test_path):
                command = f"python -m unittest discover {test_path} {options}"
            else:
                command = f"python -m unittest {test_path} {options}"
        elif test_framework == "jest":
            command = f"npx jest {test_path} {options}"
        elif test_framework == "mocha":
            command = f"npx mocha {test_path} {options}"
        else:
            return ToolResult(
                data={
                    "error": f"Unsupported test framework: {test_framework}",
                    "test_path": test_path,
                }
            )
        
        # Execute the test command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        
        return ToolResult(
            data={
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "success": result.returncode == 0,
                "command": command,
                "test_framework": test_framework,
                "test_path": test_path,
            }
        )
    except subprocess.TimeoutExpired:
        return ToolResult(
            data={
                "error": f"Tests timed out after {timeout} seconds",
                "timeout": timeout,
                "test_path": test_path,
                "test_framework": test_framework,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to run tests: {str(e)}",
                "test_path": test_path,
                "test_framework": test_framework,
            }
        )


@tool(
    id="execute_code_snippet",
    name="Execute Code Snippet",
    description="Execute a code snippet in a specific language",
    parameters={
        "code": {
            "type": "string",
            "description": "Code snippet to execute",
            "examples": ["print('Hello, world!')", "console.log('Hello, world!');"],
        },
        "language": {
            "type": "string",
            "description": "Programming language of the code",
            "examples": ["python", "javascript", "typescript"],
            "enum": ["python", "javascript", "typescript", "bash", "ruby", "php"],
        },
        "timeout": {
            "type": "integer",
            "description": "Timeout in seconds",
            "examples": [5, 10, 30],
        },
    },
    required=["code", "language"],
    category=ToolCategory.CODE,
    tags=["execute", "code", "snippet"],
)
def execute_code_snippet(
    code: str,
    language: str,
    timeout: int = 10,
) -> ToolResult:
    """Execute a code snippet in a specific language.
    
    Args:
        code: Code snippet to execute
        language: Programming language of the code
        timeout: Timeout in seconds
        
    Returns:
        Execution result
    """
    try:
        # Create a temporary file for the code
        file_extension = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "bash": ".sh",
            "ruby": ".rb",
            "php": ".php",
        }.get(language.lower(), ".txt")
        
        with tempfile.NamedTemporaryFile(suffix=file_extension, mode="w", delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name
        
        try:
            # Build the execution command
            command = {
                "python": ["python", temp_file_path],
                "javascript": ["node", temp_file_path],
                "typescript": ["npx", "ts-node", temp_file_path],
                "bash": ["bash", temp_file_path],
                "ruby": ["ruby", temp_file_path],
                "php": ["php", temp_file_path],
            }.get(language.lower())
            
            if not command:
                return ToolResult(
                    data={
                        "error": f"Unsupported language: {language}",
                        "language": language,
                    }
                )
            
            # Execute the code
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            
            return ToolResult(
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode,
                    "success": result.returncode == 0,
                    "language": language,
                }
            )
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
    except subprocess.TimeoutExpired:
        return ToolResult(
            data={
                "error": f"Execution timed out after {timeout} seconds",
                "timeout": timeout,
                "language": language,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to execute code snippet: {str(e)}",
                "language": language,
            }
        )
