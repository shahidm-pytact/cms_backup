"""File storage utilities for blog images."""
import base64
import re
import uuid
from pathlib import Path
from typing import Optional, Tuple

# Constants
DATA_URL_PATTERN = re.compile(r'^data:image/(\w+);base64,(.+)$')
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def is_base64_image(src: str) -> bool:
    """Check if src is a base64 data URL.
    
    Args:
        src: Source string to check
        
    Returns:
        True if src is a base64 data URL, False otherwise
    """
    return bool(DATA_URL_PATTERN.match(src)) if src else False


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
