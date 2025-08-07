"""Content negotiation utilities for handling different response formats."""

from typing import Optional, Tuple
from fastapi import Request
import logging

logger = logging.getLogger(__name__)


def parse_accept_header(accept_header: str) -> list:
    """
    Parse the Accept header and return a list of media types with their quality values.
    
    Args:
        accept_header: The Accept header string
        
    Returns:
        List of tuples (media_type, quality) sorted by quality in descending order
    """
    if not accept_header:
        return [("*/*", 1.0)]
    
    media_types = []
    
    for item in accept_header.split(","):
        parts = item.split(";")
        media_type = parts[0].strip()
        
        # Default quality is 1.0
        quality = 1.0
        
        # Check for quality parameter
        for param in parts[1:]:
            param = param.strip()
            if param.startswith("q="):
                try:
                    quality = float(param[2:])
                except ValueError:
                    quality = 1.0
                break
        
        media_types.append((media_type, quality))
    
    # Sort by quality (highest first)
    media_types.sort(key=lambda x: x[1], reverse=True)
    
    return media_types


def should_return_html(request: Request) -> bool:
    """
    Determine if HTML should be returned based on the Accept header.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        True if HTML should be returned, False for JSON
    """
    # Check if this is a browser request (typically includes text/html in Accept)
    accept_header = request.headers.get("accept", "*/*")
    
    # Parse the accept header
    media_types = parse_accept_header(accept_header)
    
    # Check the preferred media types
    for media_type, quality in media_types:
        # If quality is 0, skip this type
        if quality == 0:
            continue
            
        # Check for HTML preference
        if media_type in ["text/html", "application/xhtml+xml"]:
            return True
        
        # Check for JSON preference
        if media_type in ["application/json", "application/ld+json"]:
            return False
        
        # Check for wildcard
        if media_type == "*/*":
            # Default to JSON for wildcard (API behavior)
            return False
        
        # Check for text/* wildcard
        if media_type == "text/*":
            return True
    
    # Default to JSON
    return False


def get_preferred_content_type(request: Request) -> str:
    """
    Get the preferred content type for the response.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Content-Type string
    """
    if should_return_html(request):
        return "text/html; charset=utf-8"
    else:
        return "application/json"


def is_browser_request(request: Request) -> bool:
    """
    Check if the request is likely from a web browser.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        True if likely a browser request
    """
    user_agent = request.headers.get("user-agent", "").lower()
    
    # Common browser indicators
    browser_indicators = [
        "mozilla", "chrome", "safari", "firefox", "opera", "edge"
    ]
    
    # Check if any browser indicator is in the user agent
    is_browser = any(indicator in user_agent for indicator in browser_indicators)
    
    # Also check if Accept header prefers HTML
    accept_header = request.headers.get("accept", "")
    prefers_html = "text/html" in accept_header
    
    return is_browser and prefers_html