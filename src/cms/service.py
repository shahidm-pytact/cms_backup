"""Blog service for business logic."""
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from pathlib import Path
from fastapi.responses import Response as FastAPIResponse
from fastapi import status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.cms.repository import BlogRepository
from src.cms.models import Blog
from src.audit_logs.utils import create_audit_log
from src.schemas import AuthContext
import logging
from src.cms.schemas import (
    BlogCreate,
    BlogUpdate,
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
    decode_base64_image,
    save_image,
)
from src.config import settings
from src.utils import generate_etag, format_last_modified, set_304_response_headers


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
                except OSError:
                    # Directory not empty or other error, ignore
                    pass
        except Exception:
            # Ignore errors when deleting files (file might not exist, etc.)
            pass


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
    
    If the value is a base64 data URL, it will be decoded, saved to storage,
    and the URL path will be returned. If it's already a URL or None, it's returned as-is.
    
    Args:
        image_value: Image value (base64 data URL or regular URL)
        blog_slug: Blog slug for organizing images
        field_name: Field name for error messages (e.g., "authorImg", "blogImage")
        storage_base_path: Base path for file storage (defaults to settings)
        
    Returns:
        URL path if base64 was processed, original value otherwise
        
    Raises:
        BlogValidationError: If base64 image processing fails
    """
    if not image_value:
        return image_value
    
    # If it's not a base64 image, return as-is
    if not is_base64_image(image_value):
        return image_value
    
    # Process base64 image
    try:
        # Decode base64 image
        binary_data, image_type = decode_base64_image(image_value)
        
        # Save image with UUID filename
        image_url = await save_image(
            binary_data=binary_data,
            blog_slug=blog_slug,
            image_id=None,  # Generate UUID automatically
            image_type=image_type,
            storage_base_path=storage_base_path or settings.storage_base_path
        )
        
        return image_url
        
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
        
        # Process base64 images in authorImg and blogImage fields
        processed_author_img = await process_base64_image_field(
            image_value=data.author_img,
            blog_slug=data.slug,
            field_name="authorImg",
            storage_base_path=settings.storage_base_path
        )
        
        processed_blog_image = await process_base64_image_field(
            image_value=data.blog_image,
            blog_slug=data.slug,
            field_name="blogImage",
            storage_base_path=settings.storage_base_path
        )
        
        # Process base64 images in sections (replace with URLs)
        # This must happen before validation so that src fields contain URLs
        processed_sections = await process_base64_images_in_sections(
            sections=data.sections,
            blog_slug=data.slug,
            storage_base_path=settings.storage_base_path
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
        
        # Commit transaction
        await self.session.commit()
        await self.session.refresh(blog)
        
        # Create audit log
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
            await self.session.commit()
        except Exception as e:
            # Log error but don't fail the blog creation
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for blog creation: {str(e)}", exc_info=True)
        
        # Build response (minimal fields per API spec)
        result = BlogCreateResponse.model_validate(blog)
        # Attach ETag
        result._etag = generate_etag(blog.updated_at or blog.created_at)
        result._last_modified = blog.updated_at or blog.created_at
        return result
    
    async def get_blog_by_slug(
        self,
        slug: str,
        if_none_match: Optional[str] = None,
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
        
        # Delete old images before processing new ones
        await delete_old_images(old_image_paths, settings.storage_base_path)
        
        # Process base64 images in authorImg and blogImage fields
        processed_author_img = await process_base64_image_field(
            image_value=data.author_img,
            blog_slug=data.slug,
            field_name="authorImg",
            storage_base_path=settings.storage_base_path
        )
        
        processed_blog_image = await process_base64_image_field(
            image_value=data.blog_image,
            blog_slug=data.slug,
            field_name="blogImage",
            storage_base_path=settings.storage_base_path
        )
        
        # Process base64 images in sections (replace with URLs)
        processed_sections = await process_base64_images_in_sections(
            sections=data.sections,
            blog_slug=data.slug,  # Use new slug
            storage_base_path=settings.storage_base_path
        )
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
        blog.status = data.status or STATUS_DRAFT  # Default to draft if not provided
        # Replace content completely with new sections
        blog.content = sections_to_content_dict(processed_sections)
        
        # Save blog
        blog = await self.repository.update(blog)
        
        # Commit transaction
        await self.session.commit()
        await self.session.refresh(blog)
        
        # Create audit log
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
            await self.session.commit()
        except Exception as e:
            # Log error but don't fail the blog update
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for blog update: {str(e)}", exc_info=True)
        
        # Build response (minimal fields per API spec)
        result = BlogUpdateResponse.model_validate(blog)
        # Attach ETag
        updated_at = blog.updated_at or blog.created_at
        result._etag = generate_etag(updated_at)
        result._last_modified = updated_at
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
        
        # Commit transaction
        await self.session.commit()
        
        # Create audit log
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
            await self.session.commit()
        except Exception as e:
            # Log error but don't fail the blog deletion
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for blog deletion: {str(e)}", exc_info=True)
        
        # Build response
        return BlogDeleteResponse(
            slug=blog.slug,
            deleted_at=blog.deleted_at or datetime.now(timezone.utc),
        )
