"""Tool for retrieving HTML pages and converting them to Markdown."""

import re

import requests
from langchain_core.tools import tool
from markdownify import markdownify

from .llm_cache import cached_tool


@tool
@cached_tool(ttl_seconds=60 * 60, cache_type="visit_web", write_to_query_store=True)
def visit_web(url: str) -> str:
    """Fetch *url*, convert the HTML to Markdown, and return the content.

    Args:
        url: Public HTTP or HTTPS URL to download.

    Returns:
        Markdown string describing the page or an error message if fetching
        fails.
    """
    print(f"\n[visit_web] Input: url={url}")
    
    # Add headers to avoid bot detection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    try:
        # Send request to the URL with headers
        response = requests.get(url, timeout=30, headers=headers)
        print(f"[visit_web] Raw HTTP response status: {response.status_code}")
        # Check if the request was successful
        response.raise_for_status()
        # Convert HTML content to markdown
        markdown_content = markdownify(response.text).strip()
        print(f"[visit_web] Raw markdown content length: {len(markdown_content)}")
        # Clean up excessive newlines
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
        # Limit content length to avoid overwhelming the LLM
        if len(markdown_content) > 10000:
            markdown_content = markdown_content[:10000] + "\n\n[Content truncated due to length...]"
        print(f"[visit_web] Output: {markdown_content[:200]}..." if len(markdown_content) > 200 else f"[visit_web] Output: {markdown_content}")
        return markdown_content
    except requests.exceptions.Timeout:
        print(f"[visit_web] Timeout error for url: {url}")
        return f"Error: The request to {url} timed out. The website may be slow or blocking automated requests."
    except requests.exceptions.RequestException as e:
        print(f"[visit_web] RequestException for url: {url}, error: {str(e)}")
        return f"Error visiting {url}: {str(e)}"
