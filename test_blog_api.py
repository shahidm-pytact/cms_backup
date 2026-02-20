#!/usr/bin/env python3
"""Test script to verify blog list endpoint with verification secret."""

import asyncio
import httpx
import json

# Configuration
BASE_URL = "http://192.168.1.17:8000"
VERIFICATION_SECRET = "3f8e9b1d2c7a4f6e9a0b5d8c1e4f2a7b6c9d0e1f3a5b7c8d9e2f4a6b8c0d1e2f"


async def test_blog_list_with_verification_secret():
    """Test blog list endpoint with verification_secret."""
    print("Testing blog list endpoint with verification_secret...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/v1/blogs/blog-1771415036909?verification_secret={VERIFICATION_SECRET}",
            timeout=10.0
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Blog list accessed with verification secret")
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False


async def test_blog_list_with_next_api_secret():
    """Test blog list endpoint with NEXT_API_SECRET (correct parameter)."""
    print("\nTesting blog list endpoint with NEXT_API_SECRET...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/v1/blogs?NEXT_API_SECRET={VERIFICATION_SECRET}",
            timeout=10.0
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success! Blog list accessed with NEXT_API_SECRET")
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False


async def test_blog_list_without_secret():
    """Test blog list endpoint without any secret."""
    print("\nTesting blog list endpoint without any secret...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/v1/blogs",
            timeout=10.0
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Correctly requires authentication without secret")
            return True
        else:
            print(f"❌ Expected 401, got {response.status_code}")
            print(f"Response: {response.text}")
            return False


async def test_specific_blog_with_verification_secret():
    """Test specific blog endpoint with verification_secret."""
    print("\nTesting specific blog endpoint with verification_secret...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/v1/blogs/blog-1771415036909?verification_secret={VERIFICATION_SECRET}",
            timeout=10.0
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success! Specific blog accessed with verification secret")
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False


async def main():
    """Run all tests."""
    print("Testing blog list endpoint with verification secret...")
    print("=" * 60)
    
    tests = [
        test_blog_list_with_verification_secret,
        test_blog_list_with_next_api_secret,
        test_blog_list_without_secret,
        test_specific_blog_with_verification_secret,
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed")


if __name__ == "__main__":
    asyncio.run(main())
