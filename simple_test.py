#!/usr/bin/env python3
"""Simple test to verify MCP server is running."""

import requests
import json

def test_server():
    """Test if the MCP server is responding"""
    
    # Test 1: Basic connectivity
    try:
        response = requests.get("http://localhost:3001/sse", timeout=5)
        print(f"✅ Server is responding on /sse endpoint")
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to MCP server")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Try a simple POST request
    try:
        test_data = {"test": "data"}
        response = requests.post(
            "http://localhost:3001/sse",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"✅ POST request to /sse endpoint")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"⚠️  POST test error: {e}")
    
    print("\n🎉 MCP server appears to be running!")
    print("💡 To use it properly, you need:")
    print("   1. Use Cursor's MCP integration with URL: http://localhost:3001/sse")
    print("   2. Or use a proper MCP client that handles SSE protocol")
    
    return True

if __name__ == "__main__":
    test_server() 