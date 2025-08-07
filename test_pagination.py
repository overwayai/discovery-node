#!/usr/bin/env python
"""Test script for search pagination functionality"""
import requests
import json

# Base URL - adjust if needed
BASE_URL = "http://localhost:8000/api/v1/query/search"

# Test different skip/limit combinations
test_cases = [
    {"skip": 0, "limit": 5, "q": "product"},
    {"skip": 5, "limit": 5, "q": "product"},
    {"skip": 10, "limit": 5, "q": "product"},
    {"skip": 0, "limit": 10, "q": "product"},
    {"skip": 10, "limit": 10, "q": "product"},
]

print("Testing Search API Pagination")
print("=" * 50)

for test in test_cases:
    print(f"\nTest: skip={test['skip']}, limit={test['limit']}, query='{test['q']}'")
    
    params = {
        "q": test["q"],
        "skip": test["skip"],
        "limit": test["limit"]
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Check results
        items = data.get("itemListElement", [])
        print(f"  Results returned: {len(items)}")
        
        # Check pagination metadata
        print(f"  cmp:skip: {data.get('cmp:skip')}")
        print(f"  cmp:limit: {data.get('cmp:limit')}")
        print(f"  cmp:hasNext: {data.get('cmp:hasNext')}")
        print(f"  cmp:hasPrevious: {data.get('cmp:hasPrevious')}")
        
        if data.get('cmp:hasNext'):
            print(f"  cmp:nextSkip: {data.get('cmp:nextSkip')}")
        if data.get('cmp:hasPrevious'):
            print(f"  cmp:previousSkip: {data.get('cmp:previousSkip')}")
            
        # Show first few product names
        if items:
            print("  First few products:")
            for i, item in enumerate(items[:3]):
                product = item.get("item", {})
                print(f"    {i+1}. {product.get('name', 'Unknown')}")
                
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: {str(e)}")
    except Exception as e:
        print(f"  ERROR: {str(e)}")

print("\n" + "=" * 50)
print("Pagination test completed")