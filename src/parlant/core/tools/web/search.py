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

"""Web search tools for Daneel."""

import json
import os
import re
import urllib.parse
from typing import Dict, List, Optional, Union

import httpx

from Daneel.core.tools import ToolResult
from Daneel.core.tools.tool_registry import ToolCategory, tool


@tool(
    id="web_search",
    name="Web Search",
    description="Search the web for information",
    parameters={
        "query": {
            "type": "string",
            "description": "The search query",
            "examples": ["python asyncio tutorial", "climate change effects"],
        },
        "num_results": {
            "type": "integer",
            "description": "Number of results to return",
            "examples": [5, 10, 20],
        },
    },
    required=["query"],
    category=ToolCategory.WEB,
    tags=["search", "web"],
)
async def web_search(
    query: str,
    num_results: int = 5,
) -> ToolResult:
    """Search the web for information.
    
    Args:
        query: The search query
        num_results: Number of results to return
        
    Returns:
        Search results
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("SEARCH_API_KEY")
        cx = os.environ.get("SEARCH_ENGINE_ID")
        
        if not api_key or not cx:
            return ToolResult(
                data={
                    "error": "Search API key or engine ID not configured",
                    "query": query,
                }
            )
        
        # Build the search URL
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": min(num_results, 10),  # API limit is 10
        }
        
        # Make the request
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        # Extract the search results
        results = []
        if "items" in data:
            for item in data["items"]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })
        
        return ToolResult(
            data={
                "results": results,
                "total_results": len(results),
                "query": query,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to search the web: {str(e)}",
                "query": query,
            }
        )


@tool(
    id="fetch_webpage",
    name="Fetch Webpage",
    description="Fetch the content of a webpage",
    parameters={
        "url": {
            "type": "string",
            "description": "URL of the webpage to fetch",
            "examples": ["https://www.example.com", "https://en.wikipedia.org/wiki/Python_(programming_language)"],
        },
        "extract_text": {
            "type": "boolean",
            "description": "Whether to extract text content only",
            "examples": [True, False],
        },
    },
    required=["url"],
    category=ToolCategory.WEB,
    tags=["fetch", "web"],
)
async def fetch_webpage(
    url: str,
    extract_text: bool = True,
) -> ToolResult:
    """Fetch the content of a webpage.
    
    Args:
        url: URL of the webpage to fetch
        extract_text: Whether to extract text content only
        
    Returns:
        Webpage content
    """
    try:
        # Validate URL
        if not url.startswith(("http://", "https://")):
            return ToolResult(
                data={
                    "error": "Invalid URL: must start with http:// or https://",
                    "url": url,
                }
            )
        
        # Fetch the webpage
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            content = response.text
        
        if extract_text:
            # Simple HTML to text conversion
            # Remove scripts and styles
            content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL)
            content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL)
            
            # Remove HTML tags
            content = re.sub(r"<[^>]*>", "", content)
            
            # Decode HTML entities
            content = re.sub(r"&nbsp;", " ", content)
            content = re.sub(r"&lt;", "<", content)
            content = re.sub(r"&gt;", ">", content)
            content = re.sub(r"&amp;", "&", content)
            content = re.sub(r"&quot;", "\"", content)
            
            # Normalize whitespace
            content = re.sub(r"\s+", " ", content)
            
            # Split into paragraphs
            paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
            content = "\n\n".join(paragraphs)
        
        return ToolResult(
            data={
                "content": content,
                "url": url,
                "title": extract_title(content) if extract_text else None,
                "content_type": "text" if extract_text else "html",
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to fetch webpage: {str(e)}",
                "url": url,
            }
        )


def extract_title(html_content: str) -> str:
    """Extract the title from HTML content.
    
    Args:
        html_content: HTML content
        
    Returns:
        Title of the webpage
    """
    match = re.search(r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


@tool(
    id="search_wikipedia",
    name="Search Wikipedia",
    description="Search Wikipedia for information",
    parameters={
        "query": {
            "type": "string",
            "description": "The search query",
            "examples": ["Python programming language", "Albert Einstein"],
        },
        "num_results": {
            "type": "integer",
            "description": "Number of results to return",
            "examples": [1, 3, 5],
        },
        "language": {
            "type": "string",
            "description": "Language code for Wikipedia",
            "examples": ["en", "es", "fr", "de"],
        },
    },
    required=["query"],
    category=ToolCategory.WEB,
    tags=["search", "web", "wikipedia"],
)
async def search_wikipedia(
    query: str,
    num_results: int = 1,
    language: str = "en",
) -> ToolResult:
    """Search Wikipedia for information.
    
    Args:
        query: The search query
        num_results: Number of results to return
        language: Language code for Wikipedia
        
    Returns:
        Wikipedia search results
    """
    try:
        # Build the search URL
        search_url = f"https://{language}.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": num_results,
        }
        
        # Make the search request
        async with httpx.AsyncClient() as client:
            search_response = await client.get(search_url, params=search_params)
            search_response.raise_for_status()
            search_data = search_response.json()
        
        # Extract search results
        search_results = search_data.get("query", {}).get("search", [])
        if not search_results:
            return ToolResult(
                data={
                    "results": [],
                    "total_results": 0,
                    "query": query,
                }
            )
        
        # Get details for each result
        results = []
        for result in search_results:
            page_id = result.get("pageid")
            if page_id:
                # Build the content URL
                content_url = f"https://{language}.wikipedia.org/w/api.php"
                content_params = {
                    "action": "query",
                    "prop": "extracts|info",
                    "exintro": True,
                    "explaintext": True,
                    "inprop": "url",
                    "pageids": page_id,
                    "format": "json",
                }
                
                # Make the content request
                content_response = await client.get(content_url, params=content_params)
                content_response.raise_for_status()
                content_data = content_response.json()
                
                # Extract the content
                page = content_data.get("query", {}).get("pages", {}).get(str(page_id), {})
                
                results.append({
                    "title": page.get("title", result.get("title", "")),
                    "extract": page.get("extract", result.get("snippet", "")),
                    "url": page.get("fullurl", f"https://{language}.wikipedia.org/wiki/{urllib.parse.quote(result.get('title', ''))}"),
                })
        
        return ToolResult(
            data={
                "results": results,
                "total_results": len(results),
                "query": query,
            }
        )
    except Exception as e:
        return ToolResult(
            data={
                "error": f"Failed to search Wikipedia: {str(e)}",
                "query": query,
            }
        )
