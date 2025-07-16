#!/usr/bin/env python3
"""Test MCP client for the discovery node server."""

import asyncio
import aiohttp
import json
import uuid

class MCPClient:
    def __init__(self, url: str = "http://localhost:3001/sse"):
        self.url = url
        self.session_id = str(uuid.uuid4())
        
    async def initialize(self):
        """Initialize MCP connection"""
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print(f"🔌 Initializing MCP connection to {self.url}")
        print(f"📝 Init request: {json.dumps(init_request, indent=2)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.url,
                json=init_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"📊 Init response status: {response.status}")
                if response.status == 200:
                    result = await response.text()
                    print(f"✅ Init response: {result}")
                    return True
                else:
                    print(f"❌ Init failed: {response.status}")
                    return False
    
    async def list_tools(self):
        """List available tools"""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        print(f"\n🔧 Listing tools...")
        print(f"📝 Request: {json.dumps(request, indent=2)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.url,
                json=request,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"📊 Response status: {response.status}")
                if response.status == 200:
                    result = await response.text()
                    print(f"✅ Tools response: {result}")
                    return result
                else:
                    print(f"❌ Failed to list tools: {response.status}")
                    return None
    
    async def search_products(self, query: str, limit: int = 5):
        """Search for products"""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search-products",
                "arguments": {
                    "query": query,
                    "limit": limit
                }
            }
        }
        
        print(f"\n🔍 Searching for: '{query}'")
        print(f"📝 Request: {json.dumps(request, indent=2)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.url,
                json=request,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"📊 Response status: {response.status}")
                if response.status == 200:
                    result = await response.text()
                    print(f"✅ Search response: {result}")
                    return result
                else:
                    print(f"❌ Search failed: {response.status}")
                    error_text = await response.text()
                    print(f"Error details: {error_text}")
                    return None

async def main():
    """Test the MCP server"""
    client = MCPClient()
    
    print("🚀 Testing MCP Discovery Node Server")
    print("=" * 50)
    
    # Initialize connection
    if not await client.initialize():
        print("❌ Failed to initialize MCP connection")
        return
    
    # List available tools
    await client.list_tools()
    
    # Test search
    await client.search_products("books", 3)

if __name__ == "__main__":
    asyncio.run(main()) 