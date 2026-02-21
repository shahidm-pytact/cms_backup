"""File storage utilities for blog images."""
import base64
import re
import uuid
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Constants
DATA_URL_PATTERN = re.compile(r'^data:image/(\w+);base64,(.+)$')
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Magic bytes (file signatures) for image validation
# These are the first few bytes that identify the actual file type
IMAGE_MAGIC_BYTES = {
    'png': [b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'],  # PNG: \x89PNG\r\n\x1a\n
    'jpg': [b'\xFF\xD8\xFF'],  # JPEG: starts with \xFF\xD8\xFF
    'jpeg': [b'\xFF\xD8\xFF'],  # JPEG: same as jpg
    'gif': [b'GIF87a', b'GIF89a'],  # GIF: GIF87a or GIF89a
    'webp': [b'RIFF'],  # WebP: starts with RIFF, followed by WEBP at offset 8
}


def is_base64_image(src: str) -> bool:
    """Check if src is a base64 data URL.
    
    Args:
        src: Source string to check
        
    Returns:
        True if src is a base64 data URL, False otherwise
    """
    return bool(DATA_URL_PATTERN.match(src)) if src else False


def validate_image_content(binary_data: bytes, claimed_type: str) -> None:
    """
    Validate image content using multiple security layers:
    1. Magic bytes (file signature) validation
    2. Pillow image library parsing
    
    This prevents malicious files (e.g., PHP scripts) from being uploaded
    by renaming them with image extensions.
    
    Args:
        binary_data: Image binary data to validate
        claimed_type: Claimed image type (extension)
        
    Raises:
        ValueError: If file content doesn't match claimed type or is not a valid image
    """
    if not binary_data:
        raise ValueError("Image data is empty")
    
    # Normalize claimed type (jpg -> jpeg)
    normalized_type = 'jpeg' if claimed_type == 'jpg' else claimed_type.lower()
    
    if normalized_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(f"Image type '{claimed_type}' not allowed. Allowed: {ALLOWED_IMAGE_TYPES}")
    
    # Layer 1: Magic Bytes Validation (File Signature)
    # Check if file starts with correct magic bytes for claimed type
    magic_bytes_list = IMAGE_MAGIC_BYTES.get(normalized_type, [])
    
    if not magic_bytes_list:
        raise ValueError(f"No magic bytes defined for image type '{claimed_type}'")
    
    # Check if file starts with any of the expected magic bytes
    magic_match = False
    
    # Special handling for WebP (RIFF at start, WEBP at offset 8)
    if normalized_type == 'webp':
        if binary_data.startswith(b'RIFF') and len(binary_data) >= 12:
            if binary_data[8:12] == b'WEBP':
                magic_match = True
    else:
        # For other image types, check standard magic bytes
        for magic_bytes in magic_bytes_list:
            if binary_data.startswith(magic_bytes):
                magic_match = True
                break
    
    if not magic_match:
        raise ValueError(
            f"File content does not match claimed image type '{claimed_type}'. "
            f"File may be malicious or corrupted. Expected magic bytes for {claimed_type} not found."
        )
    
    # Layer 2: Pillow Image Library Validation
    # Try to parse the file as an image - if it fails, it's not a valid image
    if PIL_AVAILABLE:
        try:
            # Open image from bytes
            image = Image.open(BytesIO(binary_data))
            
            # Verify it's actually an image format we support
            image_format = image.format
            if image_format:
                image_format_lower = image_format.lower()
                # Pillow returns formats like 'PNG', 'JPEG', 'GIF', 'WEBP'
                # Map to our normalized types
                format_map = {
                    'png': 'png',
                    'jpeg': 'jpeg',
                    'jpg': 'jpeg',
                    'gif': 'gif',
                    'webp': 'webp',
                }
                
                detected_type = format_map.get(image_format_lower)
                if detected_type != normalized_type:
                    raise ValueError(
                        f"Image format mismatch: detected '{image_format}' but claimed type is '{claimed_type}'. "
                        f"File may be malicious or incorrectly labeled."
                    )
            
            # Verify image can be loaded (prevents corrupted files)
            image.verify()
            
            # Reopen after verify (verify() closes the image)
            image = Image.open(BytesIO(binary_data))
            
            # Additional security: ensure image is actually valid
            # Try to get image size - if this fails, it's not a valid image
            image.size
            
        except Exception as e:
            raise ValueError(
                f"File is not a valid {claimed_type} image. "
                f"Image library validation failed: {str(e)}. "
                f"File may be malicious, corrupted, or not an image."
            )
    else:
        # If Pillow is not available, we rely on magic bytes only
        # Log a warning that full validation is not available
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            "Pillow is not available. Image validation is limited to magic bytes only. "
            "Install Pillow for full image content validation."
        )


def contains_base64_data(image_value: str) -> bool:
    """Check if image value contains base64 data.
    
    This function checks for the presence of ';base64,' marker which indicates
    base64 encoded data. It handles both standard format (data:image/png;base64,...)
    and custom format (data:/path/to/image;base64,...).
    
    Args:
        image_value: Image value to check
        
    Returns:
        True if value contains ';base64,' marker, False otherwise
    """
    return ";base64," in image_value if image_value else False


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
    
    # CRITICAL SECURITY: Validate file content matches claimed type
    # This prevents malicious files (e.g., PHP scripts) from being uploaded
    # by renaming them with image extensions
    validate_image_content(binary_data, image_type)
    
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
    
    CRITICAL SECURITY: Validates file content before saving to prevent
    malicious files from being uploaded by renaming them with image extensions.
    
    Args:
        binary_data: Image binary data
        blog_slug: Blog slug for organizing images
        image_id: Optional image identifier (defaults to UUID)
        image_type: Image file extension
        storage_base_path: Base path for file storage
        
    Returns:
        Full URL path stored in JSON (e.g., "/images/blogs/my-blog-slug/550e8400-e29b-41d4-a716-446655440000.png")
        This path is stored in the JSON src field for easy retrieval.
        
    Raises:
        ValueError: If file content doesn't match claimed type or is not a valid image
    """
    # CRITICAL SECURITY: Validate file content matches claimed type
    # This prevents malicious files (e.g., PHP scripts) from being uploaded
    # by renaming them with image extensions
    validate_image_content(binary_data, image_type)
    
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
