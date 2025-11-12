from langchain_core.tools import tool
import requests
import re
from markdownify import markdownify

@tool
def visit_web(url: str) -> str:
    """
    Use this tool to visit a web page and extract its text content in markdown format.
    Best used after finding relevant URLs through search.
    
    Arguments:
        url: The URL of the web page to visit.
    """
    
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
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Convert HTML content to markdown
        markdown_content = markdownify(response.text).strip()
        
        # Clean up excessive newlines
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
        
        # Limit content length to avoid overwhelming the LLM
        if len(markdown_content) > 10000:
            markdown_content = markdown_content[:10000] + "\n\n[Content truncated due to length...]"
        
        return markdown_content
        
    except requests.exceptions.Timeout:
        return f"Error: The request to {url} timed out. The website may be slow or blocking automated requests."
    except requests.exceptions.RequestException as e:
        return f"Error visiting {url}: {str(e)}"

#print(visit_web.invoke("https://www.facebook.com/"))