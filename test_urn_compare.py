#!/usr/bin/env python
"""Test script for URN-based product comparison"""
import requests
import json

# Base URL - adjust if needed
BASE_URL = "http://safco-dental-supply.localhost:8000"

# First, let's search for some products to get their URNs
print("1. Searching for products to get URNs...")
search_response = requests.get(f"{BASE_URL}/api/v1/query/search", params={"q": "syringe", "limit": 5})
search_data = search_response.json()

# Extract URNs from search results
urns = []
products_info = []
for item in search_data.get("itemListElement", [])[:3]:  # Get first 3 products
    product = item.get("item", {})
    urn = product.get("@id")
    if urn:
        urns.append(urn)
        products_info.append({
            "urn": urn,
            "name": product.get("name", "Unknown"),
            "price": product.get("offers", {}).get("price") if isinstance(product.get("offers"), dict) else None
        })

print(f"\nFound {len(urns)} products:")
for info in products_info:
    print(f"  - {info['name']} (URN: {info['urn']}, Price: ${info['price']})")

if len(urns) < 2:
    print("\nERROR: Not enough products found to compare")
    exit(1)

# Test 1: Compare by URNs without request ID
print("\n2. Testing URN comparison WITHOUT request ID...")
compare_data = {
    "urns": urns[:2],  # Compare first 2 products
    "comparison_aspects": ["price", "brand", "features"],
    "format": "table"
}

response = requests.post(
    f"{BASE_URL}/api/v1/query/compare/products",
    json=compare_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    result = response.json()
    print("✓ Success! Comparison completed")
    print(f"  New request ID: {result.get('cmp:requestId')}")
    print(f"  Compared aspects: {result.get('cmp:comparisonAspects')}")
    print(f"  Narrative preview: {result.get('narrative', '')[:100]}...")
else:
    print(f"✗ Failed with status {response.status_code}: {response.text}")

# Test 2: Compare by URNs WITH request ID from search
print("\n3. Testing URN comparison WITH request ID from search...")
search_request_id = search_data.get("cmp:requestId")
if search_request_id:
    compare_data_with_cache = {
        "urns": urns[:3],  # Compare 3 products
        "request_id": search_request_id,
        "format": "narrative"
    }
    
    response2 = requests.post(
        f"{BASE_URL}/api/v1/query/compare/products",
        json=compare_data_with_cache,
        headers={"Content-Type": "application/json"}
    )
    
    if response2.status_code == 200:
        result2 = response2.json()
        print("✓ Success! Comparison completed using cached data")
        print(f"  Used cache from: {search_request_id}")
        print(f"  New request ID: {result2.get('cmp:requestId')}")
        print(f"  Number of products compared: {len(result2.get('products', []))}")
    else:
        print(f"✗ Failed with status {response2.status_code}: {response2.text}")

# Test 3: Test with invalid URN
print("\n4. Testing with invalid URN (should fail)...")
invalid_compare = {
    "urns": [urns[0], "urn:invalid:product:123"],
    "format": "table"
}

response3 = requests.post(
    f"{BASE_URL}/api/v1/query/compare/products",
    json=invalid_compare,
    headers={"Content-Type": "application/json"}
)

if response3.status_code != 200:
    print(f"✓ Correctly failed with status {response3.status_code}")
    print(f"  Error: {response3.json().get('detail', 'Unknown error')}")
else:
    print("✗ Should have failed but didn't")

print("\n" + "="*50)
print("URN comparison tests completed!")