"""Migration script to import blogs from JSON files and images from blog_image folder.

This script:
1. Reads JSON files from blog_migration/blogs/
2. Reads image files from blog_migration/blog_image/
3. Transforms data structure to match BlogCreate schema
4. Processes images and saves them to static folder
5. Creates blogs in database using BlogService (same logic as create endpoint)
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from src.database import AsyncSessionLocal, engine
from src.cms.service import BlogService
from src.cms.schemas import BlogCreate, SectionSchema, BlockSchema
from src.cms.exceptions import BlogSlugExists, BlogValidationError
from src.schemas import AuthContext
from src.user.models import User
from src.config import settings
from src.cms.utils.storage import save_image

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
BLOG_MIGRATION_DIR = project_root / "blog_migration"
BLOGS_DIR = BLOG_MIGRATION_DIR / "blogs"
IMAGES_DIR = BLOG_MIGRATION_DIR / "blog_image"


def find_image_file(image_path: str) -> Optional[Path]:
    """Find image file in blog_image directory.
    
    Args:
        image_path: Image path from JSON (e.g., "/images/blog/xxx.webp" or "/images/blog/lovable-blog/xxx.png")
        
    Returns:
        Path to image file if found, None otherwise
    """
    # Remove leading slash and "images/blog/" prefix
    path_parts = image_path.lstrip("/").split("/")
    
    # Skip "images" and "blog" parts
    if len(path_parts) >= 3 and path_parts[0] == "images" and path_parts[1] == "blog":
        # Get the rest of the path (e.g., "xxx.webp" or "lovable-blog/xxx.png")
        relative_path = "/".join(path_parts[2:])
        image_file = IMAGES_DIR / relative_path
        
        if image_file.exists() and image_file.is_file():
            return image_file
    
    # Try direct lookup in images directory
    # Handle paths like "/images/shahidProfile.webp"
    if len(path_parts) >= 2 and path_parts[0] == "images":
        relative_path = "/".join(path_parts[1:])
        image_file = IMAGES_DIR / relative_path
        
        if image_file.exists() and image_file.is_file():
            return image_file
    
    # Try direct filename lookup
    filename = Path(image_path).name
    image_file = IMAGES_DIR / filename
    if image_file.exists() and image_file.is_file():
        return image_file
    
    return None


async def process_image_to_static(image_path: str, blog_slug: str) -> Optional[str]:
    """Process image file and save to static folder, returning the saved path.
    
    Args:
        image_path: Image path from JSON
        blog_slug: Blog slug for organizing images
        
    Returns:
        Saved image path (e.g., "/images/blogs/{blog_slug}/{uuid}.{ext}") or None if not found
    """
    image_file = find_image_file(image_path)
    
    if not image_file:
        logger.warning(f"Image not found: {image_path}")
        return None
    
    try:
        # Read image binary data
        binary_data = image_file.read_bytes()
        
        # Determine image type from file extension
        image_type = image_file.suffix.lstrip(".").lower()
        if image_type not in ["png", "jpg", "jpeg", "gif", "webp"]:
            # Default to webp if unknown
            image_type = "webp"
        
        # Save image using the same utility as create endpoint
        saved_path = await save_image(
            binary_data=binary_data,
            blog_slug=blog_slug,
            image_id=None,  # Generate UUID automatically
            image_type=image_type,
            storage_base_path=settings.storage_base_path
        )
        
        logger.info(f"Saved image: {image_path} -> {saved_path}")
        return saved_path
        
    except Exception as e:
        logger.error(f"Failed to process image {image_path}: {e}", exc_info=True)
        return None


def transform_blog_data(source_data: Dict[str, Any], blog_slug: str) -> Dict[str, Any]:
    """Transform blog data from source format to BlogCreate format.
    
    Source format: {metadata: {...}, sections: [...]}
    Target format: flat structure matching BlogCreate schema
    
    Args:
        source_data: Source JSON data
        blog_slug: Blog slug
        
    Returns:
        Transformed data dict ready for BlogCreate
    """
    metadata = source_data.get("metadata", {})
    sections_data = source_data.get("sections", [])
    
    # Transform sections - add order_index if missing
    transformed_sections = []
    for section_idx, section in enumerate(sections_data, start=1):
        # Create a copy to avoid modifying original
        transformed_section = section.copy()
        
        # Add order_index if missing
        if "order_index" not in transformed_section:
            transformed_section["order_index"] = section_idx
        
        # Transform blocks - add order_index if missing and fix code blocks
        blocks = transformed_section.get("blocks", [])
        transformed_blocks = []
        for block_idx, block in enumerate(blocks, start=1):
            # Create a copy to avoid modifying original
            transformed_block = block.copy()
            
            # Add order_index if missing (use gap-based: 10, 20, 30...)
            if "order_index" not in transformed_block:
                transformed_block["order_index"] = block_idx * 10
            
            # Fix code blocks: if type is "code" and has "content" but no "code", move content to code
            if transformed_block.get("type") == "code":
                if "content" in transformed_block and "code" not in transformed_block:
                    transformed_block["code"] = transformed_block.pop("content")
                elif "content" in transformed_block and "code" in transformed_block:
                    # Both exist - prefer code, remove content
                    transformed_block.pop("content", None)
            
            transformed_blocks.append(transformed_block)
        
        transformed_section["blocks"] = transformed_blocks
        transformed_sections.append(transformed_section)
    
    # Build transformed data
    transformed = {
        "slug": metadata.get("slug", blog_slug),
        "title": metadata.get("title", ""),
        "subtitle": metadata.get("subtitle"),
        "description": metadata.get("description"),
        "author": metadata.get("author", ""),
        "authorImg": metadata.get("authorImg"),  # Will be processed separately
        "publishedDate": metadata.get("publishedDate"),
        "readingTime": metadata.get("readingTime"),
        "heroQuote": metadata.get("heroQuote"),
        "blogImage": metadata.get("blogImage"),  # Will be processed separately
        "metaDescription": metadata.get("metaDescription"),
        "keywords": metadata.get("keywords"),
        "status": metadata.get("status", "draft"),  # Default to draft
        "sections": transformed_sections,
    }
    
    return transformed


async def process_images_in_sections(
    sections: list[Dict[str, Any]],
    blog_slug: str
) -> list[Dict[str, Any]]:
    """Process images in section blocks.
    
    Args:
        sections: List of section dicts
        blog_slug: Blog slug for organizing images
        
    Returns:
        Sections with processed image paths
    """
    processed_sections = []
    
    for section in sections:
        # Create a copy to avoid modifying original
        processed_section = section.copy()
        processed_blocks = []
        
        for block in section.get("blocks", []):
            # Create a copy to avoid modifying original
            processed_block = block.copy()
            
            if processed_block.get("type") == "image" and processed_block.get("src"):
                src = processed_block["src"]
                
                # Skip if already base64
                if src.startswith("data:"):
                    processed_blocks.append(processed_block)
                    continue
                
                # Process image file
                saved_path = await process_image_to_static(src, blog_slug)
                if saved_path:
                    processed_block["src"] = saved_path
                else:
                    logger.warning(f"Could not process image in block {processed_block.get('id')}: {src}")
            
            processed_blocks.append(processed_block)
        
        processed_section["blocks"] = processed_blocks
        processed_sections.append(processed_section)
    
    return processed_sections


async def migrate_blog(
    json_file: Path,
    session: AsyncSession,
    auth_context: AuthContext
) -> tuple[bool, str]:
    """Migrate a single blog from JSON file.
    
    Args:
        json_file: Path to JSON file
        session: Database session
        auth_context: Auth context for service calls
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Read JSON file
        with open(json_file, "r", encoding="utf-8") as f:
            source_data = json.load(f)
        
        # Extract slug from metadata or filename
        metadata = source_data.get("metadata", {})
        blog_slug = metadata.get("slug")
        if not blog_slug:
            # Fallback to filename without extension
            blog_slug = json_file.stem
        
        logger.info(f"Processing blog: {blog_slug}")
        
        # Check if blog already exists
        service = BlogService(session)
        existing_blog = await service.repository.get_by_slug(blog_slug)
        if existing_blog:
            logger.info(f"Skipping {blog_slug} - already exists")
            return (True, f"Skipped (already exists)")
        
        # Transform data structure
        transformed_data = transform_blog_data(source_data, blog_slug)
        
        # Process images in sections
        transformed_data["sections"] = await process_images_in_sections(
            transformed_data["sections"],
            blog_slug
        )
        
        # Process authorImg if present
        if transformed_data.get("authorImg"):
            author_img_path = transformed_data["authorImg"]
            if not author_img_path.startswith("data:"):
                saved_path = await process_image_to_static(author_img_path, blog_slug)
                if saved_path:
                    transformed_data["authorImg"] = saved_path
        
        # Process blogImage if present
        if transformed_data.get("blogImage"):
            blog_image_path = transformed_data["blogImage"]
            if not blog_image_path.startswith("data:"):
                saved_path = await process_image_to_static(blog_image_path, blog_slug)
                if saved_path:
                    transformed_data["blogImage"] = saved_path
        
        # Convert to BlogCreate schema
        blog_create = BlogCreate(**transformed_data)
        
        # Create blog using service (reuses all validation and processing logic)
        result = await service.create_blog(
            data=blog_create,
            ctx=auth_context,
            request=None  # No request object for migration
        )
        
        logger.info(f"✓ Successfully migrated: {blog_slug} (ID: {result.id})")
        return (True, f"Migrated successfully (ID: {result.id})")
        
    except BlogSlugExists as e:
        # Rollback session after duplicate slug error
        await session.rollback()
        logger.warning(f"Skipping {json_file.name} - slug already exists: {e}")
        return (True, "Skipped (duplicate slug)")
    except IntegrityError as e:
        # Rollback session after integrity error (duplicate key, etc.)
        await session.rollback()
        # Check if it's a duplicate slug error
        if "slug" in str(e.orig).lower() or "unique constraint" in str(e.orig).lower():
            logger.warning(f"Skipping {json_file.name} - duplicate slug (IntegrityError)")
            return (True, "Skipped (duplicate slug)")
        else:
            logger.error(f"Integrity error for {json_file.name}: {e}")
            return (False, f"Integrity error: {str(e)}")
    except BlogValidationError as e:
        # Rollback session after validation error
        await session.rollback()
        logger.error(f"Validation error for {json_file.name}: {e}")
        return (False, f"Validation error: {str(e)}")
    except Exception as e:
        # Rollback session after any other error
        await session.rollback()
        logger.error(f"Error migrating {json_file.name}: {e}", exc_info=True)
        return (False, f"Error: {str(e)}")


async def get_migration_user(session: AsyncSession) -> Optional[User]:
    """Get a user for migration (prefer superadmin, fallback to any active user).
    
    Args:
        session: Database session
        
    Returns:
        User model or None
    """
    # Try to find superadmin user
    from src.roles.models import Role
    result = await session.execute(
        select(User)
        .options(selectinload(User.role))
        .join(Role, User.role_id == Role.id)
        .where(
            Role.slug == "superadmin",
            User.status == "active",
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if user:
        return user
    
    # Fallback to any active user
    result = await session.execute(
        select(User)
        .options(selectinload(User.role))
        .where(
            User.status == "active",
            User.deleted_at.is_(None)
        )
        .limit(1)
    )
    user = result.scalar_one_or_none()
    
    return user


async def migrate_all_blogs() -> None:
    """Migrate all blogs from JSON files."""
    logger.info("=" * 60)
    logger.info("Blog Migration Script")
    logger.info("=" * 60)
    
    # Check directories exist
    if not BLOGS_DIR.exists():
        logger.error(f"Blogs directory not found: {BLOGS_DIR}")
        return
    
    if not IMAGES_DIR.exists():
        logger.error(f"Images directory not found: {IMAGES_DIR}")
        return
    
    # Get JSON files
    json_files = sorted(BLOGS_DIR.glob("*.json"))
    if not json_files:
        logger.warning("No JSON files found in blogs directory")
        return
    
    logger.info(f"Found {len(json_files)} blog JSON files")
    
    async with AsyncSessionLocal() as session:
        try:
            # Get user for AuthContext
            user = await get_migration_user(session)
            if not user:
                logger.error("No active user found. Cannot create blogs without AuthContext.")
                return
            
            # Create AuthContext
            auth_context = AuthContext(
                user_id=user.id,
                role_id=user.role_id,
                role=user.role.slug if user.role else None,
                permissions_json=user.role.permissions_json if user.role else None
            )
            
            logger.info(f"Using user: {user.email} (Role: {user.role.slug if user.role else 'None'})")
            logger.info("")
            
            # Track results
            success_count = 0
            skip_count = 0
            error_count = 0
            results = []
            
            # Process each blog
            for idx, json_file in enumerate(json_files, 1):
                logger.info(f"[{idx}/{len(json_files)}] Processing: {json_file.name}")
                
                success, message = await migrate_blog(json_file, session, auth_context)
                
                # Note: create_blog already commits internally on success
                # We just need to ensure session is in good state after errors
                # (rollback is handled in migrate_blog exception handlers)
                
                if success:
                    if "Skipped" in message:
                        skip_count += 1
                    else:
                        success_count += 1
                else:
                    error_count += 1
                
                results.append((json_file.name, success, message))
                logger.info("")
            
            # Print summary
            logger.info("=" * 60)
            logger.info("Migration Summary")
            logger.info("=" * 60)
            logger.info(f"Total files: {len(json_files)}")
            logger.info(f"✓ Successfully migrated: {success_count}")
            logger.info(f"⊘ Skipped: {skip_count}")
            logger.info(f"✗ Errors: {error_count}")
            logger.info("")
            
            if error_count > 0:
                logger.info("Failed migrations:")
                for filename, success, message in results:
                    if not success:
                        logger.info(f"  - {filename}: {message}")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Fatal error during migration: {e}", exc_info=True)
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate_all_blogs())
