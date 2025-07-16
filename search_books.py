#!/usr/bin/env python3
"""Search for books using the MCP server."""

import asyncio
import aiohttp
import json
import time

async def search_books():
    """Search for books using the MCP server"""
    
    print("🔍 Searching for books in your product database...")
    print("📡 Connecting to MCP server at http://localhost:3001/sse")
    
    # MCP initialization request
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
                "name": "book-search-client",
                "version": "1.0.0"
            }
        }
    }
    
    # MCP search request
    search_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "search-products",
            "arguments": {
                "query": "books",
                "limit": 10
            }
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Step 1: Initialize MCP connection
            print("\n🔌 Initializing MCP connection...")
            async with session.post(
                "http://localhost:3001/sse",
                json=init_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            ) as response:
                print(f"📊 Init response status: {response.status}")
                if response.status != 200:
                    print(f"❌ Init failed: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    return
                else:
                    print("✅ MCP connection initialized")
            
            # Step 2: Search for books
            print("\n🔍 Searching for books...")
            async with session.post(
                "http://localhost:3001/sse",
                json=search_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            ) as response:
                print(f"📊 Search response status: {response.status}")
                if response.status == 200:
                    result = await response.text()
                    print("✅ Search completed successfully!")
                    print(f"📝 Results: {result}")
                else:
                    print(f"❌ Search failed: {response.status}")
                    error_text = await response.text()
                    print(f"Error details: {error_text}")
                    
    except aiohttp.ClientConnectorError:
        print("❌ Cannot connect to MCP server")
        print("💡 Make sure the server is running: python run_mcp.py --port 3001")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Book Search via MCP Server")
    print("=" * 40)
    asyncio.run(search_books()) 