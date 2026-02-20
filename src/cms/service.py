"""Blog service for business logic."""
import base64
import re
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from pathlib import Path
from fastapi.responses import Response as FastAPIResponse
from fastapi import status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.cms.repository import BlogRepository
from src.cms.models import Blog
from src.audit_logs.utils import create_audit_log
from src.schemas import AuthContext
import logging
from src.cms.schemas import (
    BlogCreate,
    BlogUpdate,
    BlogPatchUpdate,
    BlogListQuery,
    BlogRead,
    BlogListItem,
    BlogPaginatedResponse,
    BlogPaginationInfo,
    BlogCreateResponse,
    BlogUpdateResponse,
    BlogDeleteResponse,
    SectionSchema,
    BlockSchema,
)
from src.cms.exceptions import (
    BlogNotFound,
    BlogSlugExists,
    BlogValidationError,
)
from src.cms.constants import (
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    ERROR_INVALID_SECTION_STRUCTURE,
    ERROR_INVALID_BLOCK_STRUCTURE,
    ERROR_DUPLICATE_SECTION_ID,
    ERROR_DUPLICATE_BLOCK_ID,
)
from src.cms.utils.storage import (
    is_base64_image,
    contains_base64_data,
    decode_base64_image,
    save_image,
    MAX_IMAGE_SIZE,
    ALLOWED_IMAGE_TYPES,
)
from src.config import settings
from src.utils import generate_etag, format_last_modified, set_304_response_headers, call_blog_revalidation_webhook


def validate_content_structure(sections: list[SectionSchema]) -> None:
    """Validate blog content structure (sections and blocks).
    
    Args:
        sections: List of sections to validate
        
    Raises:
        BlogValidationError: If structure is invalid
    """
    if not sections:
        raise BlogValidationError(
            "Blog must have at least one section",
            details=[{"field": "sections", "issue": "At least one section is required"}],
        )
    
    section_ids = set()
    block_type_requirements = {
        "text": ["content"],
        "code": ["language", "code"],
        "list": ["variant", "items"],
        "highlight": ["content"],
        "quote": ["content"],
        "image": ["src", "alt"],
        "cards": ["columns", "items"],
        "steps": ["steps"],
        "step": ["stepNumber", "title"],
        "comparison": ["options", "items"],
    }
    
    for section in sections:
        # Validate section structure
        if not section.id:
            raise BlogValidationError(
                ERROR_INVALID_SECTION_STRUCTURE,
                details=[{"field": "sections[].id", "issue": "Section ID is required"}],
            )
        if not section.title:
            raise BlogValidationError(
                ERROR_INVALID_SECTION_STRUCTURE,
                details=[{"field": "sections[].title", "issue": "Section title is required"}],
            )
        if section.order_index < 1:
            raise BlogValidationError(
                ERROR_INVALID_SECTION_STRUCTURE,
                details=[{"field": "sections[].order_index", "issue": "Section order_index must be ≥ 1"}],
            )
        if not section.blocks:
            raise BlogValidationError(
                ERROR_INVALID_SECTION_STRUCTURE,
                details=[{"field": "sections[].blocks", "issue": "Section must have at least one block"}],
            )
        
        # Check for duplicate section IDs
        if section.id in section_ids:
            raise BlogValidationError(
                ERROR_DUPLICATE_SECTION_ID,
                details=[{"field": "sections[].id", "issue": f"Duplicate section ID: {section.id}"}],
            )
        section_ids.add(section.id)
        
        # Validate blocks
        block_ids = set()
        for block in section.blocks:
            # Validate block structure
            if not block.id:
                raise BlogValidationError(
                    ERROR_INVALID_BLOCK_STRUCTURE,
                    details=[{"field": "sections[].blocks[].id", "issue": "Block ID is required"}],
                )
            if not block.type:
                raise BlogValidationError(
                    ERROR_INVALID_BLOCK_STRUCTURE,
                    details=[{"field": "sections[].blocks[].type", "issue": "Block type is required"}],
                )
            if block.order_index < 1:
                raise BlogValidationError(
                    ERROR_INVALID_BLOCK_STRUCTURE,
                    details=[{"field": "sections[].blocks[].order_index", "issue": "Block order_index must be ≥ 1"}],
                )
            
            # Check for duplicate block IDs within section
            if block.id in block_ids:
                raise BlogValidationError(
                    ERROR_DUPLICATE_BLOCK_ID,
                    details=[{"field": "sections[].blocks[].id", "issue": f"Duplicate block ID: {block.id} in section {section.id}"}],
                )
            block_ids.add(block.id)
            
            # Validate block type-specific requirements
            if block.type in block_type_requirements:
                required_fields = block_type_requirements[block.type]
                for field in required_fields:
                    if not hasattr(block, field) or getattr(block, field) is None:
                        raise BlogValidationError(
                            f"Block type '{block.type}' requires field '{field}'",
                            details=[{"field": f"sections[].blocks[].{field}", "issue": f"Field '{field}' is required for block type '{block.type}'"}],
                        )


def sections_to_content_dict(sections: list[SectionSchema]) -> dict:
    """Convert sections schema to content JSONB dict.
    
    Args:
        sections: List of sections
        
    Returns:
        Content dict with sections array
    """
    # Use exclude_none to avoid storing keys with null values in JSONB
    return {
        "sections": [
            section.model_dump(by_alias=True, exclude_none=True)
            for section in sections
        ]
    }


def content_dict_to_sections(content: dict) -> list[SectionSchema]:
    """Convert content JSONB dict to sections schema.
    
    Args:
        content: Content dict from database
        
    Returns:
        List of sections
    """
    sections_data = content.get("sections", [])
    return [SectionSchema(**section) for section in sections_data]


def extract_image_paths_from_content(content: dict) -> list[str]:
    """Extract all image paths from blog content.
    
    Args:
        content: Content dict from database
        
    Returns:
        List of image file paths (relative paths from storage base)
    """
    image_paths = []
    sections_data = content.get("sections", [])
    
    for section in sections_data:
        blocks = section.get("blocks", [])
        for block in blocks:
            if block.get("type") == "image" and block.get("src"):
                src = block["src"]
                # Only extract paths that are not base64 (already saved images)
                if not is_base64_image(src):
                    # Remove leading slash if present
                    image_path = src.lstrip("/")
                    image_paths.append(image_path)
    
    return image_paths


def extract_image_path_from_field(image_value: Optional[str]) -> Optional[str]:
    """Extract image path from authorImg or blogImage field.
    
    Args:
        image_value: Image URL or None
        
    Returns:
        Image path (relative to storage base) if it's a saved image, None otherwise
    """
    if not image_value:
        return None
    
    # Only extract paths that are not base64 (already saved images)
    if not is_base64_image(image_value):
        # Remove leading slash if present
        return image_value.lstrip("/")
    
    return None


async def delete_old_images(image_paths: list[str], storage_base_path: str) -> None:
    """Delete old image files from storage.
    
    Args:
        image_paths: List of image file paths (relative to storage_base_path)
        storage_base_path: Base path for file storage
    """
    logger = logging.getLogger(__name__)
    for image_path in image_paths:
        try:
            full_path = Path(storage_base_path) / image_path
            if full_path.exists() and full_path.is_file():
                full_path.unlink()
                # Try to remove parent directory if empty (blog slug directory)
                try:
                    parent_dir = full_path.parent
                    if parent_dir.exists() and not any(parent_dir.iterdir()):
                        parent_dir.rmdir()
                except OSError as e:
                    # Directory not empty or other error, log for monitoring
                    logger.warning(
                        f"Failed to remove empty directory {parent_dir} after deleting image {image_path}: {e}"
                    )
        except Exception as e:
            # Log errors when deleting files for monitoring and debugging
            logger.warning(
                f"Failed to delete image {image_path} from storage: {e}",
                exc_info=True
            )


async def process_base64_images_in_sections(
    sections: list[SectionSchema],
    blog_slug: str,
    storage_base_path: str = None
) -> list[SectionSchema]:
    """
    Process base64 images in blog sections.
    
    Detects image blocks with base64 src, decodes them, saves to storage using UUID,
    and replaces src with generated URLs. The URL path is stored in JSON for easy
    file identification during retrieval.
    
    Args:
        sections: List of sections with potential base64 images
        blog_slug: Blog slug for organizing images
        storage_base_path: Base path for file storage (defaults to settings)
        
    Returns:
        Processed sections with base64 images replaced by URLs (paths stored in JSON)
    """
    if storage_base_path is None:
        storage_base_path = settings.storage_base_path
    
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
                    
                except ValueError as e:
                    # Raise validation error for invalid base64/image issues
                    raise BlogValidationError(
                        f"Failed to process image in block '{block.id}': {str(e)}",
                        details=[{"field": f"sections[].blocks[].src", "issue": str(e)}]
                    )
                except Exception as e:
                    # Raise validation error for other issues (file write, etc.)
                    raise BlogValidationError(
                        f"Failed to save image in block '{block.id}': {str(e)}",
                        details=[{"field": f"sections[].blocks[].src", "issue": f"Storage error: {str(e)}"}]
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


async def process_base64_image_field(
    image_value: Optional[str],
    blog_slug: str,
    field_name: str,
    storage_base_path: str = None
) -> Optional[str]:
    """Process a base64 image field (authorImg or blogImage).
    
    If the value contains base64 data (has ';base64,' marker), it will be decoded,
    saved to storage, and the URL path will be returned. If it's just a path (no base64),
    it's returned as-is.
    
    Handles both standard format (data:image/png;base64,...) and custom format
    (data:/path/to/image;base64,...).
    
    Args:
        image_value: Image value (base64 data URL or regular URL/path)
        blog_slug: Blog slug for organizing images
        field_name: Field name for error messages (e.g., "authorImg", "blogImage")
        storage_base_path: Base path for file storage (defaults to settings)
        
    Returns:
        URL path if base64 was processed, original value if path only
        
    Raises:
        BlogValidationError: If base64 image processing fails
    """
    if not image_value:
        return image_value
    
    # If it doesn't contain base64 data, return as-is (path only - keep existing)
    if not contains_base64_data(image_value):
        return image_value
    
    # Process base64 image (handles both standard and custom formats)
    try:
        # Extract base64 data from custom format (data:/path;base64,...) or standard format
        if image_value.startswith("data:"):
            # Find the base64 marker
            base64_marker = ";base64,"
            base64_index = image_value.find(base64_marker)
            if base64_index != -1:
                base64_data = image_value[base64_index + len(base64_marker):]
                
                # Try to determine image type from the data URL or default to png
                image_type = "png"  # Default
                # Check if it's standard format: data:image/png;base64,...
                if image_value.startswith("data:image/"):
                    type_match = re.match(r'^data:image/(\w+);base64,', image_value)
                    if type_match:
                        image_type = type_match.group(1).lower()
                
                # Validate image type
                if image_type not in ALLOWED_IMAGE_TYPES:
                    raise ValueError(f"Image type '{image_type}' not allowed. Allowed: {ALLOWED_IMAGE_TYPES}")
                
                # Decode base64 data
                try:
                    binary_data = base64.b64decode(base64_data)
                except Exception as e:
                    raise ValueError(f"Failed to decode base64 data: {str(e)}")
                
                # Validate size
                if len(binary_data) > MAX_IMAGE_SIZE:
                    raise ValueError(f"Image size exceeds maximum allowed size of {MAX_IMAGE_SIZE / 1024 / 1024}MB")
        
        # Save image with UUID filename
        image_url = await save_image(
            binary_data=binary_data,
            blog_slug=blog_slug,
            image_id=None,  # Generate UUID automatically
            image_type=image_type,
            storage_base_path=storage_base_path or settings.storage_base_path
        )
        
        return image_url
            else:
                # Has 'data:' but no ';base64,' - treat as path
                return image_value
        else:
            # Shouldn't reach here if contains_base64_data returned True, but handle gracefully
            return image_value
        
    except ValueError as e:
        # Raise validation error for invalid base64/image issues
        raise BlogValidationError(
            f"Failed to process {field_name}: {str(e)}",
            details=[{"field": field_name, "issue": str(e)}]
        )
    except Exception as e:
        # Raise validation error for other issues (file write, etc.)
        raise BlogValidationError(
            f"Failed to save {field_name}: {str(e)}",
            details=[{"field": field_name, "issue": f"Storage error: {str(e)}"}]
        )


class BlogService:
    """Service for blog-related business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = BlogRepository(session)
    
    async def create_blog(
        self,
        data: BlogCreate,
        ctx: AuthContext,
        request: Optional[Request] = None,
    ) -> BlogCreateResponse:
        """Create a new blog post.
        
        Args:
            data: Blog creation data
            
        Returns:
            BlogRead with created blog details
            
        Raises:
            BlogSlugExists: If slug already exists
            BlogValidationError: If content structure is invalid
        """
        # Check if slug already exists
        existing_blog = await self.repository.get_by_slug_for_update(data.slug)
        if existing_blog:
            raise BlogSlugExists(data.slug)
        
        # Track saved image paths for cleanup on failure
        saved_image_paths = []
        
        try:
            # Process base64 images in authorImg and blogImage fields
            processed_author_img = await process_base64_image_field(
                image_value=data.author_img,
                blog_slug=data.slug,
                field_name="authorImg",
                storage_base_path=settings.storage_base_path
            )
            # Track saved image if it was processed (not base64 anymore)
            if processed_author_img and not is_base64_image(processed_author_img):
                author_img_path = extract_image_path_from_field(processed_author_img)
                if author_img_path:
                    saved_image_paths.append(author_img_path)
            
            processed_blog_image = await process_base64_image_field(
                image_value=data.blog_image,
                blog_slug=data.slug,
                field_name="blogImage",
                storage_base_path=settings.storage_base_path
            )
            # Track saved image if it was processed (not base64 anymore)
            if processed_blog_image and not is_base64_image(processed_blog_image):
                blog_image_path = extract_image_path_from_field(processed_blog_image)
                if blog_image_path:
                    saved_image_paths.append(blog_image_path)
            
            # Process base64 images in sections (replace with URLs)
            # This must happen before validation so that src fields contain URLs
            processed_sections = await process_base64_images_in_sections(
                sections=data.sections,
                blog_slug=data.slug,
                storage_base_path=settings.storage_base_path
            )
            
            # Extract image paths from processed sections
            content_dict_temp = sections_to_content_dict(processed_sections)
            section_image_paths = extract_image_paths_from_content(content_dict_temp)
            saved_image_paths.extend(section_image_paths)
            
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
                author_img=processed_author_img,
                published_at=data.published_date,
                reading_time=data.reading_time,
                hero_quote=data.hero_quote,
                blog_image=processed_blog_image,
                meta_description=data.meta_description,
                keywords=data.keywords,
                status=data.status or STATUS_DRAFT,
                content=content_dict,
            )
            
            # Save blog
            blog = await self.repository.create(blog)
        except Exception:
            # Clean up saved images on any failure
            if saved_image_paths:
                await delete_old_images(saved_image_paths, settings.storage_base_path)
            raise
        
        # Create audit log (flush only, no commit)
        try:
            await create_audit_log(
                session=self.session,
                user_id=ctx.user_id,
                action="create",
                entity_type="blog",
                entity_id=blog.id,
                old_values=None,
                new_values={
                    "id": str(blog.id),
                    "slug": blog.slug,
                    "title": blog.title,
                    "author": blog.author,
                    "status": blog.status,
                },
                description=f"Blog '{blog.slug}' created",
                request=request,
            )
        except Exception as e:
            # Log error but don't fail the blog creation
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for blog creation: {str(e)}", exc_info=True)
            # Don't rollback here - will rollback in main commit if needed
        
        # Single commit for both blog creation and audit log
        try:
            await self.session.commit()
            await self.session.refresh(blog)
        except IntegrityError as e:
            await self.session.rollback()
            # Check if error is related to slug uniqueness constraint
            if "slug" in str(e.orig).lower() or "unique constraint" in str(e.orig).lower():
                raise BlogSlugExists(data.slug)
            raise
        except Exception:
            await self.session.rollback()
            raise
        
        # Build response (minimal fields per API spec)
        result = BlogCreateResponse.model_validate(blog)
        # Attach ETag
        result._etag = generate_etag(blog.updated_at or blog.created_at)
        result._last_modified = blog.updated_at or blog.created_at
        
        # Call blog revalidation webhook
        try:
            await call_blog_revalidation_webhook(blog.slug)
        except Exception as e:
            # Log error but don't fail the blog creation
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to call blog revalidation webhook: {str(e)}", exc_info=True)
        
        return result
    
    async def get_blog_by_slug(
        self,
        slug: str,
        if_none_match: Optional[str] = None,
        ctx: Optional[AuthContext] = None,
    ) -> BlogRead | FastAPIResponse:
        """Get blog details by slug.
        
        Args:
            slug: Blog slug
            if_none_match: ETag from If-None-Match header
            
        Returns:
            BlogRead with blog details, or FastAPIResponse (304) if unchanged
            
        Raises:
            BlogNotFound: If blog not found
        """
        # Get blog
        blog = await self.repository.get_by_slug(slug)
        if not blog:
            raise BlogNotFound(slug)
        
        # Generate ETag
        updated_at = blog.updated_at or blog.created_at
        etag = generate_etag(updated_at)
        
        # Check If-None-Match header
        if if_none_match and if_none_match == etag:
            response = FastAPIResponse(status_code=status.HTTP_304_NOT_MODIFIED)
            return set_304_response_headers(None, response, etag, updated_at)
        
        # Build response
        blog_dict = {
            **blog.__dict__,
            "content": content_dict_to_sections(blog.content),
        }
        result = BlogRead.model_validate(blog_dict)
        # Add sections from content
        result.content = content_dict_to_sections(blog.content)
        # Attach ETag
        result._etag = etag
        result._last_modified = updated_at
        return result
    
    async def list_blogs(
        self,
        query: BlogListQuery,
        if_none_match: Optional[str] = None,
        ctx: Optional[AuthContext] = None,
    ) -> BlogPaginatedResponse | FastAPIResponse:
        """List blogs with pagination, filtering, search, and sorting.
        
        Args:
            query: Query parameters for filtering and pagination
            if_none_match: ETag from If-None-Match header
            
        Returns:
            BlogPaginatedResponse with blogs list, or FastAPIResponse (304) if unchanged
        """
        # Get blogs from repository
        blogs, total = await self.repository.list_with_pagination(
            page=query.page,
            limit=query.limit,
            sort=query.sort,
            order=query.order,
            author=query.author,
            search=query.search,
            status=query.status,
        )
        
        # Generate collection ETag from latest blog updated_at
        latest_updated_at = None
        if blogs:
            latest_updated_at = max(
                (blog.updated_at or blog.created_at for blog in blogs),
                default=None
            )
            if latest_updated_at:
                etag = generate_etag(latest_updated_at)

                # Check If-None-Match header
                if if_none_match and if_none_match == etag:
                    response = FastAPIResponse(status_code=status.HTTP_304_NOT_MODIFIED)
                    return set_304_response_headers(None, response, etag, latest_updated_at)
        else:
            etag = None
        
        # Build response items (metadata only, no sections)
        blog_items = [BlogListItem.model_validate(blog) for blog in blogs]
        
        # Calculate pagination metadata (matching API spec format)
        total_pages = (total + query.limit - 1) // query.limit if total > 0 else 0
        has_next = query.page < total_pages
        has_prev = query.page > 1
        
        # Build pagination info
        pagination_info = BlogPaginationInfo(
            page=query.page,
            limit=query.limit,
            total=total,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )
        
        # Build response
        result = BlogPaginatedResponse(
            blogs=blog_items,
            pagination=pagination_info,
        )
        
        # Attach ETag for router to set header
        if etag and latest_updated_at:
            result._etag = etag
            result._last_modified = latest_updated_at
        
        return result
    
    async def update_blog(
        self,
        slug: str,
        data: BlogUpdate,
        ctx: AuthContext,
        request: Optional[Request] = None,
    ) -> BlogUpdateResponse:
        """Update blog post (full update).
        
        For PUT requests, this replaces ALL data completely:
        - Extracts and deletes all old images from the blog
        - Replaces all fields with data from payload
        - Processes and saves new images from payload
        
        Args:
            slug: Blog slug to update
            data: Blog update data (must contain all fields for full update)
            
        Returns:
            BlogUpdateResponse with updated blog details (minimal fields per API spec)
            
        Raises:
            BlogNotFound: If blog not found
            BlogSlugExists: If new slug already exists
            BlogValidationError: If content structure is invalid or sections missing
        """
        # Get current blog
        blog = await self.repository.get_by_slug(slug)
        if not blog:
            raise BlogNotFound(slug)
        
        # Capture old values for audit log
        old_slug = blog.slug
        old_title = blog.title
        old_status = blog.status
        
        # For full update (PUT), essential fields and sections are required
        if data.slug is None:
            raise BlogValidationError(
                "Slug is required for full update",
                details=[{"field": "slug", "issue": "Slug must be provided for PUT request"}],
            )
        if data.title is None:
            raise BlogValidationError(
                "Title is required for full update",
                details=[{"field": "title", "issue": "Title must be provided for PUT request"}],
            )
        if data.author is None:
            raise BlogValidationError(
                "Author is required for full update",
                details=[{"field": "author", "issue": "Author must be provided for PUT request"}],
            )
        if data.sections is None:
            raise BlogValidationError(
                "Sections are required for full update",
                details=[{"field": "sections", "issue": "Sections must be provided for PUT request"}],
            )
        
        # Check if slug is being changed and new slug exists
        if data.slug != slug:
            existing_blog = await self.repository.get_by_slug_for_update(data.slug)
            if existing_blog:
                raise BlogSlugExists(data.slug)
        
        # Extract old image paths from current blog content and image fields
        old_image_paths = extract_image_paths_from_content(blog.content)
        
        # Extract old image paths from authorImg and blogImage fields
        old_author_img_path = extract_image_path_from_field(blog.author_img)
        if old_author_img_path:
            old_image_paths.append(old_author_img_path)
        
        old_blog_image_path = extract_image_path_from_field(blog.blog_image)
        if old_blog_image_path:
            old_image_paths.append(old_blog_image_path)
        
        # Track saved new image paths for cleanup on failure
        saved_new_image_paths = []
        
        try:
            # Process base64 images in authorImg and blogImage fields
            processed_author_img = await process_base64_image_field(
                image_value=data.author_img,
                blog_slug=data.slug,
                field_name="authorImg",
                storage_base_path=settings.storage_base_path
            )
            # Track saved image if it was processed (not base64 anymore)
            if processed_author_img and not is_base64_image(processed_author_img):
                author_img_path = extract_image_path_from_field(processed_author_img)
                if author_img_path:
                    saved_new_image_paths.append(author_img_path)
            
            processed_blog_image = await process_base64_image_field(
                image_value=data.blog_image,
                blog_slug=data.slug,
                field_name="blogImage",
                storage_base_path=settings.storage_base_path
            )
            # Track saved image if it was processed (not base64 anymore)
            if processed_blog_image and not is_base64_image(processed_blog_image):
                blog_image_path = extract_image_path_from_field(processed_blog_image)
                if blog_image_path:
                    saved_new_image_paths.append(blog_image_path)
            
            # Process base64 images in sections (replace with URLs)
            processed_sections = await process_base64_images_in_sections(
                sections=data.sections,
                blog_slug=data.slug,  # Use new slug
                storage_base_path=settings.storage_base_path
            )
            
            # Extract image paths from processed sections
            content_dict_temp = sections_to_content_dict(processed_sections)
            section_image_paths = extract_image_paths_from_content(content_dict_temp)
            saved_new_image_paths.extend(section_image_paths)
            
            # Validate content structure (after image processing)
            validate_content_structure(processed_sections)
            
            # Replace ALL fields completely with payload data (full update)
            # None values in payload mean set to None (not keep old values)
            blog.slug = data.slug
            blog.title = data.title
            blog.subtitle = data.subtitle  # Can be None
            blog.description = data.description  # Can be None
            blog.author = data.author
            blog.author_img = processed_author_img  # Processed (base64 converted to URL or kept as-is)
            blog.published_at = data.published_date  # Can be None
            blog.reading_time = data.reading_time  # Can be None
            blog.hero_quote = data.hero_quote  # Can be None
            blog.blog_image = processed_blog_image  # Processed (base64 converted to URL or kept as-is)
            blog.meta_description = data.meta_description  # Can be None
            blog.keywords = data.keywords  # Can be None
            # Status is not updated here - use separate status update endpoint
            # Replace content completely with new sections
            blog.content = sections_to_content_dict(processed_sections)
            
            # Save blog
            blog = await self.repository.update(blog)
        except Exception:
            # Clean up saved new images on any failure
            if saved_new_image_paths:
                await delete_old_images(saved_new_image_paths, settings.storage_base_path)
            raise
        
        # Create audit log (flush only, no commit)
        try:
            old_values = {
                "slug": old_slug,
                "title": old_title,
                "status": old_status,
            }
            new_values = {
                "slug": blog.slug,
                "title": blog.title,
                "status": blog.status,
            }
            # Add slug change note if slug changed
            description = f"Blog '{blog.slug}' updated"
            if old_slug != blog.slug:
                description = f"Blog updated: slug changed from '{old_slug}' to '{blog.slug}'"
            
            await create_audit_log(
                session=self.session,
                user_id=ctx.user_id,
                action="update",
                entity_type="blog",
                entity_id=blog.id,
                old_values=old_values,
                new_values=new_values,
                description=description,
                request=request,
            )
        except Exception as e:
            # Log error but don't fail the blog update
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for blog update: {str(e)}", exc_info=True)
            # Don't rollback here - will rollback in main commit if needed
        
        # Single commit for both blog update and audit log
        try:
            await self.session.commit()
            await self.session.refresh(blog)
        except IntegrityError as e:
            await self.session.rollback()
            # Check if error is related to slug uniqueness constraint
            if "slug" in str(e.orig).lower() or "unique constraint" in str(e.orig).lower():
                raise BlogSlugExists(data.slug)
            raise
        except Exception:
            await self.session.rollback()
            raise
        
        # Only delete old images after successful commit
        await delete_old_images(old_image_paths, settings.storage_base_path)
        
        # Build response (minimal fields per API spec)
        result = BlogUpdateResponse.model_validate(blog)
        # Attach ETag
        updated_at = blog.updated_at or blog.created_at
        result._etag = generate_etag(updated_at)
        result._last_modified = updated_at
        
        # Call blog revalidation webhook
        try:
            await call_blog_revalidation_webhook(blog.slug)
        except Exception as e:
            # Log error but don't fail the blog update
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to call blog revalidation webhook: {str(e)}", exc_info=True)
        
        return result
    
    async def delete_blog(
        self,
        slug: str,
        ctx: AuthContext,
        request: Optional[Request] = None,
    ) -> BlogDeleteResponse:
        """Delete blog post (soft delete).
        
        Args:
            slug: Blog slug to delete
            
        Returns:
            BlogDeleteResponse with deletion details
            
        Raises:
            BlogNotFound: If blog not found
        """
        # Get blog
        blog = await self.repository.get_by_slug(slug)
        if not blog:
            raise BlogNotFound(slug)
        
        # Capture old values for audit log
        old_status = blog.status
        
        # Soft delete
        await self.repository.soft_delete(blog)
        
        # Create audit log (flush only, no commit)
        try:
            await create_audit_log(
                session=self.session,
                user_id=ctx.user_id,
                action="delete",
                entity_type="blog",
                entity_id=blog.id,
                old_values={
                    "slug": blog.slug,
                    "title": blog.title,
                    "status": old_status,
                },
                new_values=None,
                description=f"Blog '{blog.slug}' deleted",
                request=request,
            )
        except Exception as e:
            # Log error but don't fail the blog deletion
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for blog deletion: {str(e)}", exc_info=True)
            # Don't rollback here - will rollback in main commit if needed
        
        # Single commit for both blog deletion and audit log
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        
        # Build response
        return BlogDeleteResponse(
            slug=blog.slug,
            deleted_at=blog.deleted_at or datetime.now(timezone.utc),
        )

    async def update_blog_status(
        self,
        slug: str,
        status: str,
        ctx: AuthContext,
        request: Optional[Request] = None,
    ) -> BlogUpdateResponse:
        """Update blog status.
        
        Args:
            slug: Blog slug to update
            status: New status (draft or published)
            ctx: Authentication context
            request: FastAPI Request object for audit logs
            
        Returns:
            BlogUpdateResponse with updated blog details
            
        Raises:
            BlogNotFound: If blog not found
        """
        # Get current blog
        blog = await self.repository.get_by_slug(slug)
        if not blog:
            raise BlogNotFound(slug)
        
        # Capture old values for audit log
        old_status = blog.status
        
        # Update status
        blog.status = status
        
        # Save blog
        blog = await self.repository.update(blog)
        
        # Create audit log (flush only, no commit)
        try:
            await create_audit_log(
                session=self.session,
                user_id=ctx.user_id,
                action="update_status",
                entity_type="blog",
                entity_id=blog.id,
                old_values={
                    "status": old_status,
                },
                new_values={
                    "status": blog.status,
                },
                description=f"Blog '{blog.slug}' status changed from '{old_status}' to '{blog.status}'",
                request=request,
            )
        except Exception as e:
            # Log error but don't fail the status update
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for blog status update: {str(e)}", exc_info=True)
            # Don't rollback here - will rollback in main commit if needed
        
        # Single commit for both blog update and audit log
        try:
            await self.session.commit()
            await self.session.refresh(blog)
        except Exception:
            await self.session.rollback()
            raise
        
        # Build response
        return BlogUpdateResponse(
            id=blog.id,
            slug=blog.slug,
            updated_at=blog.updated_at or datetime.now(timezone.utc),
        )
    
    async def patch_blog(
        self,
        slug: str,
        data: BlogPatchUpdate,
        ctx: AuthContext,
        request: Optional[Request] = None,
    ) -> BlogUpdateResponse:
        """Partially update blog post (PATCH).
        
        Updates only the fields provided in the payload:
        - Omitted fields: Keep existing values
        - null values: Keep existing values
        - Empty string "": Remove field (for images, set to None)
        - Valid values: Update field
        
        Args:
            slug: Blog slug to update
            data: Partial blog update data (only provided fields will be updated)
            ctx: Authentication context
            request: FastAPI Request object for audit logs
            
        Returns:
            BlogUpdateResponse with updated blog details
            
        Raises:
            BlogNotFound: If blog not found
            BlogSlugExists: If new slug already exists
            BlogValidationError: If content structure is invalid
        """
        # Get current blog
        blog = await self.repository.get_by_slug(slug)
        if not blog:
            raise BlogNotFound(slug)
        
        # Capture old values for audit log (only for fields being updated)
        old_values = {}
        new_values = {}
        changed_fields = []
        
        # Capture old status for audit log (will be updated to published)
        old_status = blog.status
        
        # Track old image paths for cleanup
        old_image_paths = []
        saved_new_image_paths = []
        
        try:
            # Update slug if provided
            if data.slug is not None:
                if data.slug != slug:
                    # Check if new slug exists
                    existing_blog = await self.repository.get_by_slug_for_update(data.slug)
                    if existing_blog:
                        raise BlogSlugExists(data.slug)
                    old_values["slug"] = blog.slug
                    new_values["slug"] = data.slug
                    blog.slug = data.slug
                    changed_fields.append("slug")
            
            # Update title if provided
            if data.title is not None:
                old_values["title"] = blog.title
                new_values["title"] = data.title
                blog.title = data.title
                changed_fields.append("title")
            
            # Update subtitle if provided
            if data.subtitle is not None:
                old_values["subtitle"] = blog.subtitle
                new_values["subtitle"] = data.subtitle if data.subtitle != "" else None
                blog.subtitle = new_values["subtitle"]
                changed_fields.append("subtitle")
            
            # Update description if provided
            if data.description is not None:
                old_values["description"] = blog.description
                new_values["description"] = data.description if data.description != "" else None
                blog.description = new_values["description"]
                changed_fields.append("description")
            
            # Update author if provided
            if data.author is not None:
                old_values["author"] = blog.author
                new_values["author"] = data.author
                blog.author = data.author
                changed_fields.append("author")
            
            # Handle author_img update
            if data.author_img is not None:
                old_author_img = blog.author_img
                
                if data.author_img == "":
                    # Remove image
                    old_values["author_img"] = old_author_img
                    blog.author_img = None
                    new_values["author_img"] = None
                    # Extract and track old image path for deletion
                    old_img_path = extract_image_path_from_field(old_author_img)
                    if old_img_path:
                        old_image_paths.append(old_img_path)
                    changed_fields.append("author_img")
                elif contains_base64_data(data.author_img):
                    # Update image (contains base64 data)
                    old_values["author_img"] = old_author_img
                    processed_author_img = await process_base64_image_field(
                        image_value=data.author_img,
                        blog_slug=blog.slug,
                        field_name="authorImg",
                        storage_base_path=settings.storage_base_path
                    )
                    # Extract old image path for deletion
                    if old_author_img:
                        old_img_path = extract_image_path_from_field(old_author_img)
                        if old_img_path:
                            old_image_paths.append(old_img_path)
                    # Track new image path
                    if processed_author_img:
                        new_img_path = extract_image_path_from_field(processed_author_img)
                        if new_img_path:
                            saved_new_image_paths.append(new_img_path)
                    
                    blog.author_img = processed_author_img
                    new_values["author_img"] = processed_author_img
                    changed_fields.append("author_img")
                else:
                    # Path only - keep existing (no change, no deletion)
                    # Don't update blog.author_img, don't delete old file
                    pass
            
            # Handle blog_image update
            if data.blog_image is not None:
                old_blog_image = blog.blog_image
                
                if data.blog_image == "":
                    # Remove image
                    old_values["blog_image"] = old_blog_image
                    blog.blog_image = None
                    new_values["blog_image"] = None
                    # Extract and track old image path for deletion
                    old_img_path = extract_image_path_from_field(old_blog_image)
                    if old_img_path:
                        old_image_paths.append(old_img_path)
                    changed_fields.append("blog_image")
                elif contains_base64_data(data.blog_image):
                    # Update image (contains base64 data)
                    old_values["blog_image"] = old_blog_image
                    processed_blog_image = await process_base64_image_field(
                        image_value=data.blog_image,
                        blog_slug=blog.slug,
                        field_name="blogImage",
                        storage_base_path=settings.storage_base_path
                    )
                    # Extract old image path for deletion
                    if old_blog_image:
                        old_img_path = extract_image_path_from_field(old_blog_image)
                        if old_img_path:
                            old_image_paths.append(old_img_path)
                    # Track new image path
                    if processed_blog_image:
                        new_img_path = extract_image_path_from_field(processed_blog_image)
                        if new_img_path:
                            saved_new_image_paths.append(new_img_path)
                    
                    blog.blog_image = processed_blog_image
                    new_values["blog_image"] = processed_blog_image
                    changed_fields.append("blog_image")
                else:
                    # Path only - keep existing (no change, no deletion)
                    # Don't update blog.blog_image, don't delete old file
                    pass
            
            # Update published_date if provided
            if data.published_date is not None:
                old_values["published_date"] = blog.published_at.isoformat() if blog.published_at else None
                new_values["published_date"] = data.published_date.isoformat() if data.published_date else None
                blog.published_at = data.published_date
                changed_fields.append("published_date")
            
            # Update reading_time if provided
            if data.reading_time is not None:
                old_values["reading_time"] = blog.reading_time
                new_values["reading_time"] = data.reading_time if data.reading_time != "" else None
                blog.reading_time = new_values["reading_time"]
                changed_fields.append("reading_time")
            
            # Update hero_quote if provided
            if data.hero_quote is not None:
                old_values["hero_quote"] = blog.hero_quote
                new_values["hero_quote"] = data.hero_quote if data.hero_quote != "" else None
                blog.hero_quote = new_values["hero_quote"]
                changed_fields.append("hero_quote")
            
            # Update meta_description if provided
            if data.meta_description is not None:
                old_values["meta_description"] = blog.meta_description
                new_values["meta_description"] = data.meta_description if data.meta_description != "" else None
                blog.meta_description = new_values["meta_description"]
                changed_fields.append("meta_description")
            
            # Update keywords if provided
            if data.keywords is not None:
                old_values["keywords"] = blog.keywords
                new_values["keywords"] = data.keywords if data.keywords != [] else None
                blog.keywords = new_values["keywords"]
                changed_fields.append("keywords")
            
            # Handle sections update (if provided, replace all sections)
            if data.sections is not None:
                # Extract old image paths from current content
                old_content_image_paths = extract_image_paths_from_content(blog.content)
                
                # Process base64 images in new sections
                processed_sections = await process_base64_images_in_sections(
                    sections=data.sections,
                    blog_slug=blog.slug,
                    storage_base_path=settings.storage_base_path
                )
                
                # Extract image paths from processed sections
                content_dict_temp = sections_to_content_dict(processed_sections)
                new_content_image_paths = extract_image_paths_from_content(content_dict_temp)
                saved_new_image_paths.extend(new_content_image_paths)
                
                # Only delete old images that are NOT present in new sections
                # This preserves images that are still being used
                # Normalize new paths for comparison (extract_image_paths_from_content already removes leading slash)
                normalized_new_paths = {path.lstrip("/") for path in new_content_image_paths}
                
                for old_path in old_content_image_paths:
                    # Normalize old path for comparison (extract_image_paths_from_content already removes leading slash)
                    normalized_old = old_path.lstrip("/")
                    # Check if this old image path exists in new sections
                    if normalized_old not in normalized_new_paths:
                        # Image is not in new sections - mark for deletion
                        # Path format should be without leading slash for delete_old_images function
                        old_image_paths.append(normalized_old)
                
                # Validate content structure
                validate_content_structure(processed_sections)
                
                # Replace content
                old_values["content"] = "sections_updated"
                new_values["content"] = "sections_updated"
                blog.content = sections_to_content_dict(processed_sections)
                changed_fields.append("sections")
            
            # Always update status to published when using PATCH endpoint
            # Track in audit log only if status actually changed
            if blog.status != STATUS_PUBLISHED:
                old_values["status"] = old_status
                new_values["status"] = STATUS_PUBLISHED
                changed_fields.append("status")
            blog.status = STATUS_PUBLISHED
            
            # Save blog
            blog = await self.repository.update(blog)
        except Exception:
            # Clean up saved new images on any failure
            if saved_new_image_paths:
                await delete_old_images(saved_new_image_paths, settings.storage_base_path)
            raise
        
        # Create audit log (flush only, no commit)
        try:
            description = f"Blog '{blog.slug}' partially updated: {', '.join(changed_fields)}"
            await create_audit_log(
                session=self.session,
                user_id=ctx.user_id,
                action="patch",
                entity_type="blog",
                entity_id=blog.id,
                old_values=old_values if old_values else None,
                new_values=new_values if new_values else None,
                description=description,
                request=request,
            )
        except Exception as e:
            # Log error but don't fail the blog update
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for blog patch: {str(e)}", exc_info=True)
            # Don't rollback here - will rollback in main commit if needed
        
        # Single commit for both blog update and audit log
        try:
            await self.session.commit()
            await self.session.refresh(blog)
        except IntegrityError as e:
            await self.session.rollback()
            # Check if error is related to slug uniqueness constraint
            if "slug" in str(e.orig).lower() or "unique constraint" in str(e.orig).lower():
                raise BlogSlugExists(data.slug if data.slug else slug)
            raise
        except Exception:
            await self.session.rollback()
            raise
        
        # Only delete old images after successful commit
        if old_image_paths:
            await delete_old_images(old_image_paths, settings.storage_base_path)
        
        # Build response
        result = BlogUpdateResponse.model_validate(blog)
        # Attach ETag
        updated_at = blog.updated_at or blog.created_at
        result._etag = generate_etag(updated_at)
        result._last_modified = updated_at
        
        return result