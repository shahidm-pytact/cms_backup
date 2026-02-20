#!/usr/bin/env python3
"""Simple test script to verify blog revalidation webhook functionality."""

import asyncio
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_webhook_direct():
    """Test the blog revalidation webhook call directly."""
    print("Testing blog revalidation webhook directly...")
    
    # Configuration
    webhook_secret = "0f9b2e8e7c4a6d9a1b3c5f0d2a7e4c6b9d1f3a8e6c2b5d7f9a0e4c1b3d6f8a2e"
    webhook_url = "http://192.168.1.27:3000/api/revalidate"
    test_slug = "test-blog-slug"
    
    print(f"Webhook URL: {webhook_url}")
    print(f"Secret configured: {'Yes' if webhook_secret else 'No'}")
    print(f"Testing with slug: {test_slug}")
    
    if not webhook_secret:
        print("❌ Webhook secret not configured, skipping test")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                headers={
                    "Authorization": f"Bearer {webhook_secret}"
                },
                json={"slug": test_slug},
                timeout=10.0
            )
            
            if response.status_code == 200:
                print("✅ Webhook call successful!")
                print(f"Response: {response.text}")
                return True
            else:
                print(f"❌ Webhook call failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        return False


if __name__ == "__main__":
    asyncio.run(test_webhook_direct())
