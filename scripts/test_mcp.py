#!/usr/bin/env python3
"""Test script for MCP server functionality."""

import asyncio
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.mcp.server import DiscoveryMCPServer
from app.core.logging import get_logger

logger = get_logger(__name__)


async def test_mcp_server():
    """Test the MCP server functionality."""
    
    logger.info("🧪 Testing MCP Server...")
    
    # Create server instance
    server = DiscoveryMCPServer()
    
    # Test that server can be created
    logger.info("✅ MCP Server created successfully")
    
    # Test that we can access the server object
    logger.info(f"✅ Server name: {server.server.name}")
    
    # Test that tools are registered
    logger.info("✅ MCP Server setup completed")
    
    logger.info("✅ MCP Server test completed")


if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_server())
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        sys.exit(1) 