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

"""Code search tools for Daneel."""

import os
import re
import subprocess
from typing import Dict, List, Optional, Union

from Daneel.core.tools import ToolResult
from Daneel.core.tools.tool_registry import ToolCategory, tool


@tool(
    id="code_search",
    name="Code Search",
    description="Search for code in the workspace using a query string",
    parameters={
        "query": {
            "type": "string",
            "description": "The search query",
            "examples": ["function calculateTotal", "class User", "import numpy"],
        },
        "file_pattern": {
            "type": "string",
            "description": "Optional file pattern to filter results (e.g., '*.py', '*.js')",
            "examples": ["*.py", "*.js", "*.ts"],
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results to return",
            "examples": [10, 20, 50],
        },
    },
    required=["query"],
    category=ToolCategory.CODE,
    tags=["search", "code"],
)
def code_search(
    query: str,
    file_pattern: Optional[str] = None,
    max_results: int = 10,
) -> ToolResult:
    """Search for code in the workspace using a query string.
    
    Args:
        query: The search query
        file_pattern: Optional file pattern to filter results
        max_results: Maximum number of results to return
        
    Returns:
        Search results
    """
    try:
        # Build the grep command
        grep_cmd = ["grep", "-r", "-n", "--include"]
        
        # Add file pattern if provided, otherwise search all files
        grep_cmd.append(file_pattern if file_pattern else "*")
        
        # Add the query and current directory
        grep_cmd.extend([query, "."])
        
        # Run the grep command
        result = subprocess.run(
            grep_cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        
        # Parse the results
        matches = []
        for line in result.stdout.splitlines()[:max_results]:
            # Parse the grep output (file:line:content)
            parts = line.split(":", 2)
            if len(parts) >= 3:
                file_path, line_number, content = parts
                matches.append({
                    "file": file_path,
                    "line": int(line_number),
                    "content": content.strip(),
                })
        
        return ToolResult(
            data={
                "matches": matches,
                "total_matches": len(result.stdout.splitlines()),
                "query": query,
                "file_pattern": file_pattern,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to search code: {str(e)}",
                "query": query,
                "file_pattern": file_pattern,
            }
        )


@tool(
    id="code_semantic_search",
    name="Code Semantic Search",
    description="Search for code semantically using natural language",
    parameters={
        "description": {
            "type": "string",
            "description": "Natural language description of the code to find",
            "examples": ["function that calculates total price", "user authentication logic"],
        },
        "language": {
            "type": "string",
            "description": "Programming language to search in",
            "examples": ["python", "javascript", "typescript"],
            "enum": ["python", "javascript", "typescript", "java", "c#", "c++", "go", "rust", "any"],
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results to return",
            "examples": [5, 10, 20],
        },
    },
    required=["description"],
    category=ToolCategory.CODE,
    tags=["search", "code", "semantic"],
)
def code_semantic_search(
    description: str,
    language: str = "any",
    max_results: int = 5,
) -> ToolResult:
    """Search for code semantically using natural language.
    
    Args:
        description: Natural language description of the code to find
        language: Programming language to search in
        max_results: Maximum number of results to return
        
    Returns:
        Search results
    """
    try:
        # Get file extensions for the specified language
        extensions = {
            "python": [".py"],
            "javascript": [".js"],
            "typescript": [".ts"],
            "java": [".java"],
            "c#": [".cs"],
            "c++": [".cpp", ".cc", ".cxx", ".h", ".hpp"],
            "go": [".go"],
            "rust": [".rs"],
            "any": [".py", ".js", ".ts", ".java", ".cs", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".go", ".rs"],
        }.get(language.lower(), [])
        
        # Find all matching files
        matching_files = []
        for root, _, files in os.walk("."):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    matching_files.append(os.path.join(root, file))
        
        # Simple keyword-based search (in a real implementation, this would use embeddings)
        keywords = description.lower().split()
        matches = []
        
        for file_path in matching_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Split the content into chunks (e.g., functions, classes)
                chunks = re.split(r"\n\s*\n", content)
                
                for chunk in chunks:
                    # Calculate a simple relevance score based on keyword matches
                    score = sum(1 for keyword in keywords if keyword.lower() in chunk.lower())
                    
                    if score > 0:
                        # Find the line number of the chunk
                        chunk_start = content.find(chunk)
                        line_number = content[:chunk_start].count("\n") + 1
                        
                        matches.append({
                            "file": file_path,
                            "line": line_number,
                            "content": chunk[:200] + ("..." if len(chunk) > 200 else ""),
                            "score": score,
                        })
            except Exception:
                # Skip files that can't be read
                continue
        
        # Sort by relevance score and limit results
        matches.sort(key=lambda x: x["score"], reverse=True)
        matches = matches[:max_results]
        
        return ToolResult(
            data={
                "matches": matches,
                "total_matches": len(matches),
                "description": description,
                "language": language,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to search code semantically: {str(e)}",
                "description": description,
                "language": language,
            }
        )


@tool(
    id="find_definition",
    name="Find Definition",
    description="Find the definition of a symbol in the codebase",
    parameters={
        "symbol": {
            "type": "string",
            "description": "The symbol to find (function, class, variable, etc.)",
            "examples": ["UserService", "calculate_total", "MAX_RETRIES"],
        },
        "language": {
            "type": "string",
            "description": "Programming language of the symbol",
            "examples": ["python", "javascript", "typescript"],
            "enum": ["python", "javascript", "typescript", "java", "c#", "c++", "go", "rust", "any"],
        },
    },
    required=["symbol"],
    category=ToolCategory.CODE,
    tags=["search", "code", "definition"],
)
def find_definition(
    symbol: str,
    language: str = "any",
) -> ToolResult:
    """Find the definition of a symbol in the codebase.
    
    Args:
        symbol: The symbol to find (function, class, variable, etc.)
        language: Programming language of the symbol
        
    Returns:
        Definition of the symbol
    """
    try:
        # Get file extensions and definition patterns for the specified language
        language_info = {
            "python": {
                "extensions": [".py"],
                "patterns": [
                    rf"(class\s+{re.escape(symbol)}\s*[:(])",
                    rf"(def\s+{re.escape(symbol)}\s*\()",
                    rf"({re.escape(symbol)}\s*=)",
                ],
            },
            "javascript": {
                "extensions": [".js"],
                "patterns": [
                    rf"(class\s+{re.escape(symbol)}\s*[{{\(])",
                    rf"(function\s+{re.escape(symbol)}\s*\()",
                    rf"(const|let|var)\s+{re.escape(symbol)}\s*=",
                ],
            },
            "typescript": {
                "extensions": [".ts"],
                "patterns": [
                    rf"(class\s+{re.escape(symbol)}\s*[{{\(])",
                    rf"(function\s+{re.escape(symbol)}\s*\()",
                    rf"(const|let|var)\s+{re.escape(symbol)}\s*:",
                    rf"(interface|type)\s+{re.escape(symbol)}\s*[{{\(]",
                ],
            },
            # Add patterns for other languages as needed
        }
        
        # Use default patterns if language not specified or not supported
        if language.lower() not in language_info:
            language = "any"
            
        if language.lower() == "any":
            extensions = [ext for lang in language_info.values() for ext in lang["extensions"]]
            patterns = [pattern for lang in language_info.values() for pattern in lang["patterns"]]
        else:
            extensions = language_info[language.lower()]["extensions"]
            patterns = language_info[language.lower()]["patterns"]
        
        # Find all matching files
        matching_files = []
        for root, _, files in os.walk("."):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    matching_files.append(os.path.join(root, file))
        
        # Search for the symbol definition
        definitions = []
        for file_path in matching_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.splitlines()
                    
                for i, line in enumerate(lines):
                    for pattern in patterns:
                        if re.search(pattern, line):
                            # Get context (a few lines before and after)
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            context = "\n".join(lines[start:end])
                            
                            definitions.append({
                                "file": file_path,
                                "line": i + 1,
                                "content": line.strip(),
                                "context": context,
                            })
            except Exception:
                # Skip files that can't be read
                continue
        
        return ToolResult(
            data={
                "definitions": definitions,
                "total_definitions": len(definitions),
                "symbol": symbol,
                "language": language,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to find definition: {str(e)}",
                "symbol": symbol,
                "language": language,
            }
        )
