# Base64 Image Handling Implementation Plan

## Overview

This document outlines the implementation plan for handling base64-encoded images in JSON payloads for blog creation. The system will accept images as base64 data URLs in the `src` field of image blocks, decode them, store the binary files, and replace the `src` with generated URLs before saving to the database.

## Architecture

### Flow Diagram

```
POST /v1/blogs (JSON body)
    ↓
Router receives BlogCreate schema
    ↓
Service.create_blog() processes data
    ↓
[New] Process base64 images in sections
    ├─ Detect data:image/*;base64, pattern
    ├─ Decode base64 to binary
    ├─ Generate UUID for filename
    ├─ Save binary to storage: static/images/blogs/{slug}/{uuid}.{ext}
    ├─ Generate full path: /images/blogs/{slug}/{uuid}.{ext}
    └─ Replace src in JSON with generated path (stored in DB)
    ↓
Validate content structure
    ↓
Save to database (JSON contains paths for easy retrieval)
    ↓
Retrieval: JSON already has paths → Direct file access via path
```

## Implementation Steps

### Step 1: Create File Storage Utility

**File:** `src/cms/utils/storage.py`

Create a utility module for handling file storage operations:

```python
"""File storage utilities for blog images."""
import base64
import re
import uuid
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

# Constants
DATA_URL_PATTERN = re.compile(r'^data:image/(\w+);base64,(.+)$')
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def is_base64_image(src: str) -> bool:
    """Check if src is a base64 data URL."""
    return bool(DATA_URL_PATTERN.match(src))


def decode_base64_image(data_url: str) -> Tuple[bytes, str]:
    """
    Decode base64 image data URL.
    
    Args:
        data_url: Base64 data URL (e.g., "data:image/png;base64,iVBORw0KG...")
        
    Returns:
        Tuple of (binary_data, image_extension)
        
    Raises:
        ValueError: If data URL format is invalid or image type not allowed
    """
    match = DATA_URL_PATTERN.match(data_url)
    if not match:
        raise ValueError("Invalid base64 data URL format")
    
    image_type = match.group(1).lower()
    if image_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(f"Image type '{image_type}' not allowed. Allowed: {ALLOWED_IMAGE_TYPES}")
    
    base64_data = match.group(2)
    try:
        binary_data = base64.b64decode(base64_data)
    except Exception as e:
        raise ValueError(f"Failed to decode base64 data: {str(e)}")
    
    # Validate size
    if len(binary_data) > MAX_IMAGE_SIZE:
        raise ValueError(f"Image size exceeds maximum allowed size of {MAX_IMAGE_SIZE / 1024 / 1024}MB")
    
    return binary_data, image_type


def generate_image_path(blog_slug: str, image_id: Optional[str] = None) -> str:
    """
    Generate image storage path.
    
    Args:
        blog_slug: Blog slug for organizing images
        image_id: Optional image identifier (defaults to UUID)
        
    Returns:
        Relative path (e.g., "images/blogs/my-blog-slug/abc123.png")
    """
    if image_id is None:
        image_id = str(uuid.uuid4())
    
    return f"images/blogs/{blog_slug}/{image_id}"


async def save_image(
    binary_data: bytes,
    blog_slug: str,
    image_id: Optional[str] = None,
    image_type: str = "png",
    storage_base_path: str = "static"
) -> str:
    """
    Save image binary data to storage and return URL path.
    
    Uses UUID for filename to ensure uniqueness, but stores the full path
    in JSON so it's easy to identify which file belongs to which block.
    
    Args:
        binary_data: Image binary data
        blog_slug: Blog slug for organizing images
        image_id: Optional image identifier (defaults to UUID)
        image_type: Image file extension
        storage_base_path: Base path for file storage
        
    Returns:
        Full URL path stored in JSON (e.g., "/images/blogs/my-blog-slug/550e8400-e29b-41d4-a716-446655440000.png")
        This path is stored in the JSON src field for easy retrieval.
    """
    # Generate UUID for filename (ensures uniqueness)
    image_id = image_id or str(uuid.uuid4())
    
    # Generate relative path
    relative_path = f"images/blogs/{blog_slug}/{image_id}.{image_type}"
    full_path = Path(storage_base_path) / relative_path
    
    # Create directory if it doesn't exist
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write file
    full_path.write_bytes(binary_data)
    
    # Return full URL path (this will be stored in JSON src field)
    # When retrieving blog, JSON already contains this path for easy file identification
    return f"/{relative_path}"
```

### Step 2: Add Image Processing to Service Layer

**File:** `src/cms/service.py`

Add a helper function to process base64 images in sections:

```python
from src.cms.utils.storage import (
    is_base64_image,
    decode_base64_image,
    save_image,
)
from src.cms.schemas import SectionSchema, BlockSchema


async def process_base64_images_in_sections(
    sections: list[SectionSchema],
    blog_slug: str,
    storage_base_path: str = "static"
) -> list[SectionSchema]:
    """
    Process base64 images in blog sections.
    
    Detects image blocks with base64 src, decodes them, saves to storage using UUID,
    and replaces src with generated URLs. The URL path is stored in JSON for easy
    file identification during retrieval.
    
    Args:
        sections: List of sections with potential base64 images
        blog_slug: Blog slug for organizing images
        storage_base_path: Base path for file storage
        
    Returns:
        Processed sections with base64 images replaced by URLs (paths stored in JSON)
    """
    processed_sections = []
    
    for section in sections:
        processed_blocks = []
        
        for block in section.blocks:
            # Check if this is an image block with base64 data
            if block.type == "image" and block.src and is_base64_image(block.src):
                try:
                    # Decode base64 image
                    binary_data, image_type = decode_base64_image(block.src)
                    
                    # Save image with UUID filename (ensures uniqueness)
                    # The returned path will be stored in JSON src field
                    image_url = await save_image(
                        binary_data=binary_data,
                        blog_slug=blog_slug,
                        image_id=None,  # Generate UUID automatically
                        image_type=image_type,
                        storage_base_path=storage_base_path
                    )
                    
                    # Create new block with processed URL
                    # This path is stored in JSON, making it easy to identify
                    # which file belongs to this block during retrieval
                    block_dict = block.model_dump()
                    block_dict["src"] = image_url  # Store full path in JSON
                    processed_block = BlockSchema(**block_dict)
                    processed_blocks.append(processed_block)
                    
                except Exception as e:
                    # Log error and keep original block (or raise exception)
                    raise BlogValidationError(
                        f"Failed to process image in block '{block.id}': {str(e)}",
                        details=[{"field": f"sections[].blocks[].src", "issue": str(e)}]
                    )
            else:
                # Keep block as-is (already has URL or no src)
                processed_blocks.append(block)
        
        # Create new section with processed blocks
        section_dict = section.model_dump()
        section_dict["blocks"] = processed_blocks
        processed_section = SectionSchema(**section_dict)
        processed_sections.append(processed_section)
    
    return processed_sections
```

### Step 3: Update create_blog Method

**File:** `src/cms/service.py`

Modify the `create_blog` method to process images before validation:

```python
async def create_blog(
    self,
    data: BlogCreate,
) -> BlogCreateResponse:
    """Create a new blog post.
    
    Args:
        data: Blog creation data
        
    Returns:
        BlogCreateResponse with created blog details
        
    Raises:
        BlogSlugExists: If slug already exists
        BlogValidationError: If content structure is invalid
    """
    # Check if slug already exists
    existing_blog = await self.repository.get_by_slug_for_update(data.slug)
    if existing_blog:
        raise BlogSlugExists(data.slug)
    
    # Process base64 images in sections (replace with URLs)
    processed_sections = await process_base64_images_in_sections(
        sections=data.sections,
        blog_slug=data.slug,
        storage_base_path="static"  # TODO: Get from config
    )
    
    # Validate content structure (after image processing)
    validate_content_structure(processed_sections)
    
    # Convert sections to content dict
    content_dict = sections_to_content_dict(processed_sections)
    
    # Create blog
    blog = Blog(
        slug=data.slug,
        title=data.title,
        subtitle=data.subtitle,
        description=data.description,
        author=data.author,
        author_img=data.author_img,
        published_at=data.published_date,
        reading_time=data.reading_time,
        hero_quote=data.hero_quote,
        blog_image=data.blog_image,
        meta_description=data.meta_description,
        keywords=data.keywords,
        status=data.status or STATUS_DRAFT,
        content=content_dict,
    )
    
    # Save blog
    blog = await self.repository.create(blog)
    
    # Commit transaction
    await self.session.commit()
    await self.session.refresh(blog)
    
    # Build response (minimal fields per API spec)
    result = BlogCreateResponse.model_validate(blog)
    # Attach ETag
    result._etag = generate_etag(blog.updated_at or blog.created_at)
    result._last_modified = blog.updated_at or blog.created_at
    return result
```

### Step 4: Update update_blog Method

**File:** `src/cms/service.py`

Similarly update the `update_blog` method to handle base64 images:

```python
async def update_blog(
    self,
    slug: str,
    data: BlogUpdate,
    is_full_update: bool = False,
) -> BlogUpdateResponse:
    """Update blog post (partial or full update)."""
    # ... existing validation code ...
    
    # Process base64 images if sections are being updated
    if data.sections is not None:
        # Use existing slug or new slug if being changed
        target_slug = data.slug if data.slug else slug
        processed_sections = await process_base64_images_in_sections(
            sections=data.sections,
            blog_slug=target_slug,
            storage_base_path="static"
        )
        data.sections = processed_sections
    
    # ... rest of existing code ...
```

### Step 5: Add Configuration

**File:** `src/config.py`

Add storage configuration:

```python
class Settings(BaseSettings):
    # ... existing fields ...
    
    # File Storage Configuration
    storage_base_path: str = "static"
    max_image_size_mb: int = 10
    allowed_image_types: list[str] = ["png", "jpg", "jpeg", "gif", "webp"]
```

### Step 6: Add Static File Serving (if not already present)

**File:** `src/main.py` or router setup

Ensure static files are served:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")
```

## Example Request Payload

```json
{
  "slug": "my-blog-post",
  "title": "My Blog Post",
  "author": "John Doe",
  "sections": [
    {
      "id": "intro",
      "title": "Introduction",
      "order_index": 1,
      "blocks": [
        {
          "id": "intro-image-1",
          "type": "image",
          "order_index": 20,
          "src": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgA...",
          "alt": "Example image",
          "caption": "This is an example"
        }
      ]
    }
  ]
}
```

## Example Response

After processing, the `src` field will be replaced with the full path (stored in JSON):

```json
{
  "id": "...",
  "slug": "my-blog-post",
  "title": "My Blog Post",
  "status": "draft",
  "createdAt": "2026-01-15T10:00:00Z",
  "content": {
    "sections": [{
      "id": "intro",
      "blocks": [{
        "id": "intro-image-1",
        "type": "image",
        "src": "/images/blogs/my-blog-post/550e8400-e29b-41d4-a716-446655440000.png",
        "alt": "Example",
        "caption": "Caption text"
      }]
    }]
  }
}
```

**Key Points:**
- Image stored with UUID filename: `550e8400-e29b-41d4-a716-446655440000.png`
- Full path stored in JSON `src` field: `/images/blogs/my-blog-post/550e8400-e29b-41d4-a716-446655440000.png`
- During retrieval, JSON already contains the path, making it easy to identify and serve the file
- No need for separate mapping table - path is directly in the JSON structure

## Retrieval Flow

When retrieving a blog post:

1. **Database Query**: Fetch blog from database (includes JSON content)
2. **JSON Contains Paths**: The `content.sections[].blocks[].src` fields already contain the full paths
   ```json
   {
     "src": "/images/blogs/my-blog-post/550e8400-e29b-41d4-a716-446655440000.png"
   }
   ```
3. **Direct File Access**: Frontend/client can directly use the path from JSON to:
   - Display images: `<img src="/images/blogs/my-blog-post/550e8400-e29b-41d4-a716-446655440000.png" />`
   - Serve via static file server (FastAPI StaticFiles)
   - No additional lookup needed - path is self-contained in JSON

**Benefits:**
- ✅ UUID ensures unique filenames (no collisions)
- ✅ Path stored in JSON makes it easy to identify which file belongs to which block
- ✅ No separate file mapping table required
- ✅ Self-documenting - JSON structure shows file locations
- ✅ Easy to migrate/backup - paths are part of the data structure

## Error Handling

- **Invalid base64 format**: Return 400 with validation error
- **Unsupported image type**: Return 400 with validation error
- **Image too large**: Return 400 with validation error
- **Storage write failure**: Return 500 with server error

## Testing Considerations

1. **Unit Tests**: Test base64 detection, decoding, and path generation
2. **Integration Tests**: Test full blog creation flow with base64 images
3. **Edge Cases**: 
   - Multiple images in one blog
   - Mixed base64 and URL images
   - Invalid base64 data
   - Very large images
   - Unsupported formats

## Performance Considerations

- **Large Payloads**: Base64 increases payload size by ~33%. Consider:
  - Client-side compression before encoding
  - Streaming uploads for very large images
  - Async processing for multiple images
  
- **Storage**: Images are saved synchronously before database commit. Consider:
  - Background job for large batches
  - CDN integration for production

## Security Considerations

1. **File Type Validation**: Only allow whitelisted image types
2. **Size Limits**: Enforce maximum file size
3. **Path Traversal**: Use blog_slug and image_id to prevent path manipulation
4. **Content Validation**: Consider image content validation (magic bytes)

## Future Enhancements

1. **Image Optimization**: Resize/compress images on upload
2. **Thumbnail Generation**: Create thumbnails for listings
3. **CDN Integration**: Upload to S3/CloudFront instead of local storage
4. **Image Metadata**: Extract and store EXIF data
5. **Duplicate Detection**: Hash images to avoid storing duplicates
