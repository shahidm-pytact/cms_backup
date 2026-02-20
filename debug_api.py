#!/usr/bin/env python3
"""Debug script to test query parameter handling."""

import asyncio
import httpx

# Configuration
BASE_URL = "http://192.168.1.17:8000"
VERIFICATION_SECRET = "3f8e9b1d2c7a4f6e9a0b5d8c1e4f2a7b6c9d0e1f3a5b7c8d9e2f4a6b8c0d1e2f"


async def test_debug_endpoints():
    """Test different endpoint variations."""
    
    async with httpx.AsyncClient() as client:
        # Test 1: List blogs with verification_secret
        print("Test 1: /v1/blogs?verification_secret=...")
        response = await client.get(
            f"{BASE_URL}/v1/blogs?verification_secret={VERIFICATION_SECRET}",
            timeout=10.0
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        print()
        
        # Test 2: List blogs with NEXT_API_SECRET
        print("Test 2: /v1/blogs?NEXT_API_SECRET=...")
        response = await client.get(
            f"{BASE_URL}/v1/blogs?NEXT_API_SECRET={VERIFICATION_SECRET}",
            timeout=10.0
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        print()
        
        # Test 3: Try with both parameters
        print("Test 3: /v1/blogs?NEXT_API_SECRET=...&verification_secret=...")
        response = await client.get(
            f"{BASE_URL}/v1/blogs?NEXT_API_SECRET={VERIFICATION_SECRET}&verification_secret={VERIFICATION_SECRET}",
            timeout=10.0
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        print()
        
        # Test 4: Try a different endpoint path
        print("Test 4: /v1/blogs/blog-1771415036909?verification_secret=...")
        response = await client.get(
            f"{BASE_URL}/v1/blogs/blog-1771415036909?verification_secret={VERIFICATION_SECRET}",
            timeout=10.0
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        print()


if __name__ == "__main__":
    asyncio.run(test_debug_endpoints())
