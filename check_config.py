#!/usr/bin/env python3
"""Test script to check if NEXT_API_SECRET is configured."""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import settings

print("Checking configuration...")
print(f"NEXT_API_SECRET: {'Set' if settings.next_api_secret else 'Not set'}")
print(f"BLOG_REVALIDATION_WEBHOOK_SECRET: {'Set' if settings.blog_revalidation_webhook_secret else 'Not set'}")
print(f"BLOG_REVALIDATION_WEBHOOK_URL: {settings.blog_revalidation_webhook_url}")

if not settings.next_api_secret:
    print("\n❌ NEXT_API_SECRET is not configured!")
    print("Please set NEXT_API_SECRET environment variable and restart the container.")
else:
    print("\n✅ NEXT_API_SECRET is configured!")
