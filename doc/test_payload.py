"""
Test payload for base64 image upload functionality.

Usage:
    python test_payload.py

Or use the payload in your API client (Postman, Insomnia, etc.)
"""
import json
import requests

# Configuration
API_BASE_URL = "http://localhost:8000/v1"
AUTH_TOKEN = "your-auth-token-here"  # Replace with actual token

# Test payload with base64 image
# Note: The base64 string below is a minimal 1x1 red pixel PNG for testing
PAYLOAD = {
    "slug": "test-blog-base64-images",
    "title": "Test Blog with Base64 Images",
    "subtitle": "Testing base64 image upload",
    "description": "This blog post tests the base64 image handling functionality",
    "author": "Test Author",
    "authorImg": "/images/authors/test.webp",
    "publishedDate": "2026-01-15T10:00:00.000Z",
    "readingTime": "3 min read",
    "heroQuote": "Testing base64 image uploads",
    "blogImage": "/images/blog/test-hero.webp",
    "metaDescription": "Test blog for base64 images",
    "keywords": ["test", "base64", "images"],
    "status": "draft",
    "sections": [
        {
            "id": "introduction",
            "title": "Introduction",
            "order_index": 1,
            "blocks": [
                {
                    "id": "intro-text-1",
                    "type": "text",
                    "order_index": 10,
                    "content": "This blog post demonstrates base64 image uploads in JSON payloads."
                },
                {
                    "id": "intro-image-1",
                    "type": "image",
                    "order_index": 20,
                    "src": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                    "alt": "Test image - 1x1 red pixel",
                    "caption": "This is a minimal test image (1x1 red pixel)"
                },
                {
                    "id": "intro-text-2",
                    "type": "text",
                    "order_index": 30,
                    "content": "The image above was uploaded as base64 and will be automatically processed."
                }
            ]
        },
        {
            "id": "main-content",
            "title": "Main Content",
            "order_index": 2,
            "blocks": [
                {
                    "id": "main-image-1",
                    "type": "image",
                    "order_index": 10,
                    "src": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77yAAAAABJRU5ErkJggg==",
                    "alt": "Test image 2",
                    "caption": "Another test image"
                }
            ]
        }
    ]
}


def test_create_blog():
    """Test creating a blog with base64 images."""
    url = f"{API_BASE_URL}/blogs"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    print("Sending POST request to create blog with base64 images...")
    print(f"URL: {url}")
    print(f"Payload size: {len(json.dumps(PAYLOAD))} bytes")
    
    try:
        response = requests.post(url, json=PAYLOAD, headers=headers)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 201:
            result = response.json()
            print("\n✅ Success! Blog created:")
            print(json.dumps(result, indent=2))
            
            # Check if images were processed
            if "data" in result and "id" in result["data"]:
                blog_id = result["data"]["id"]
                print(f"\n📝 Blog ID: {blog_id}")
                print(f"📝 Blog Slug: {result['data'].get('slug')}")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {str(e)}")


def print_payload():
    """Print the payload as JSON for manual testing."""
    print("=" * 80)
    print("TEST PAYLOAD (JSON)")
    print("=" * 80)
    print(json.dumps(PAYLOAD, indent=2))
    print("=" * 80)
    print("\nYou can copy this payload and use it in:")
    print("  - Postman")
    print("  - Insomnia")
    print("  - curl command")
    print("  - Any REST client")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "print":
        print_payload()
    else:
        print("=" * 80)
        print("BASE64 IMAGE UPLOAD TEST")
        print("=" * 80)
        print("\nMake sure to:")
        print("  1. Update AUTH_TOKEN in this script")
        print("  2. Ensure the API server is running")
        print("  3. Check API_BASE_URL is correct")
        print("\n" + "=" * 80 + "\n")
        
        # Uncomment to run the test
        # test_create_blog()
        
        # Or just print the payload
        print_payload()
        
        print("\n" + "=" * 80)
        print("To run the actual test, uncomment test_create_blog() in the code")
        print("=" * 80)
