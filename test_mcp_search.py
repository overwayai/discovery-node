#!/usr/bin/env python3
import requests
import json

def test_mcp_server():
    """Test if the MCP server is responding"""
    try:
        # Test basic connectivity
        response = requests.get("http://localhost:3001/health")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Test tools endpoint
        response = requests.get("http://localhost:3001/tools")
        print(f"\nTools endpoint: {response.status_code}")
        if response.status_code == 200:
            tools = response.json()
            print(f"Available tools: {list(tools.keys())}")
        
    except requests.exceptions.ConnectionError:
        print("❌ MCP server is not running or not accessible")
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")

if __name__ == "__main__":
    test_mcp_server() 