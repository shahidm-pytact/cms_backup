#!/usr/bin/env python3
"""Test script to verify blog revalidation webhook functionality."""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils import call_blog_revalidation_webhook
from src.config import settings


async def test_webhook():
    """Test the blog revalidation webhook call."""
    print("Testing blog revalidation webhook...")
    
    # Set test values
    settings.blog_revalidation_webhook_secret = "0f9b2e8e7c4a6d9a1b3c5f0d2a7e4c6b9d1f3a8e6c2b5d7f9a0e4c1b3d6f8a2e"
    settings.blog_revalidation_webhook_url = "http://192.168.1.27:3000/api/revalidate"
    
    # Test with a sample blog slug
    test_slug = "ssr-vs-ssg"
    
    print(f"Calling webhook for blog slug: {test_slug}")
    print(f"Webhook URL: {settings.blog_revalidation_webhook_url}")
    print(f"Secret configured: {'Yes' if settings.blog_revalidation_webhook_secret else 'No'}")
    
    try:
        result = await call_blog_revalidation_webhook(test_slug)
        if result:
            print("✅ Webhook call successful!")
        else:
            print("❌ Webhook call failed!")
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_webhook())
