#!/bin/bash
# Test script for creating a blog with base64 images
# Make sure to set your auth token and API base URL

API_BASE_URL="http://localhost:8000/v1"
AUTH_TOKEN="your-auth-token-here"

# Full test payload with multiple images
curl -X POST "${API_BASE_URL}/blogs" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -d @- << 'EOF'
{
  "slug": "test-blog-base64",
  "title": "Test Blog with Base64 Images",
  "author": "Test Author",
  "status": "draft",
  "sections": [
    {
      "id": "intro",
      "title": "Introduction",
      "order_index": 1,
      "blocks": [
        {
          "id": "intro-text",
          "type": "text",
          "order_index": 10,
          "content": "This blog demonstrates base64 image uploads."
        },
        {
          "id": "intro-image",
          "type": "image",
          "order_index": 20,
          "src": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
          "alt": "Test image",
          "caption": "This is a 1x1 red pixel test image"
        }
      ]
    }
  ]
}

