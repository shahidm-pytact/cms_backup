"""Blog router for API endpoints."""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Header, Response, Request, status
from fastapi.responses import Response as FastAPIResponse

from src.schemas import StandardResponse, AuthContext
from src.auth.dependencies import require_permission, require_permission_or_next_secret
from src.cms.dependencies import BlogApiDep
from src.utils import trigger_blog_webhook
from src.cms.documentations.blogs_api_doc import BlogApiDocs
from src.cms.schemas import (
    BlogCreate,
    BlogUpdate,
    BlogPatchUpdate,
    BlogStatusUpdate,
    BlogListQuery,
    BlogRead,
    BlogPaginatedResponse,
    BlogCreateResponse,
    BlogUpdateResponse,
    BlogDeleteResponse,
)
from src.cms.constants import (
    SUCCESS_BLOG_CREATED,
    SUCCESS_BLOG_RETRIEVED,
    SUCCESS_BLOGS_RETRIEVED,
    SUCCESS_BLOG_UPDATED,
    SUCCESS_BLOG_PATCHED,
    SUCCESS_BLOG_STATUS_UPDATED,
    SUCCESS_BLOG_DELETED,
)
from src.utils import set_etag_headers_and_return, set_request_id_header

router = APIRouter(
    prefix="/blogs",
    tags=["Blogs"],
)


@router.get(
    "",
    response_model=StandardResponse[BlogPaginatedResponse],
    status_code=status.HTTP_200_OK,
    summary=BlogApiDocs.list["summary"],
    description=BlogApiDocs.list["description"],
    response_model_exclude_none=True,
)
async def list_blogs(
    query: BlogListQuery = Depends(BlogListQuery),
    ctx: Optional[AuthContext] = Depends(require_permission_or_next_secret("blogs.blog", "read_all")),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    api: BlogApiDep = Depends(BlogApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[BlogPaginatedResponse] | FastAPIResponse:
    """List all blogs with pagination, filtering, and sorting."""
    result = await api.list_blogs(query, if_none_match, ctx)
    
    # Handle 304 response
    if isinstance(result, FastAPIResponse):
        set_request_id_header(request, result)
        return result
    
    return set_etag_headers_and_return(response, result, SUCCESS_BLOGS_RETRIEVED, request)


@router.post(
    "",
    response_model=StandardResponse[BlogCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary=BlogApiDocs.create["summary"],
    description=BlogApiDocs.create["description"],
)
async def create_blog(
    data: BlogCreate,
    ctx: AuthContext = Depends(require_permission("blogs.blog", "create")),
    api: BlogApiDep = Depends(BlogApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[BlogCreateResponse]:
    """Create a new blog post."""
    result = await api.create_blog(data, ctx, request)
    
    # Call blog revalidation webhook after successful blog creation
    if result and hasattr(result, 'data') and result.data:
        try:
            await trigger_blog_webhook(result, result.data.slug, "created")
        except Exception as e:
            # Log webhook error but don't fail response
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to call blog revalidation webhook: {str(e)}", exc_info=True)
    
    return set_etag_headers_and_return(response, result, SUCCESS_BLOG_CREATED, request)


@router.get(
    "/{slug}",
    response_model=StandardResponse[BlogRead],
    status_code=status.HTTP_200_OK,
    summary=BlogApiDocs.get["summary"],
    description=BlogApiDocs.get["description"],
    response_model_exclude_none=True,
)
async def get_blog(
    slug: str,
    ctx: Optional[AuthContext] = Depends(require_permission_or_next_secret("blogs.blog", "read")),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    api: BlogApiDep = Depends(BlogApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[BlogRead] | FastAPIResponse:
    """Get specific blog with full details."""
    result = await api.get_blog_by_slug(slug, if_none_match, ctx)
    
    # Handle 304 response
    if isinstance(result, FastAPIResponse):
        set_request_id_header(request, result)
        return result
    
    return set_etag_headers_and_return(response, result, SUCCESS_BLOG_RETRIEVED, request)


@router.put(
    "/{slug}",
    response_model=StandardResponse[BlogUpdateResponse],
    status_code=status.HTTP_200_OK,
    summary=BlogApiDocs.update["summary"],
    description=BlogApiDocs.update["description"],
)
async def update_blog_put(
    slug: str,
    data: BlogUpdate,
    ctx: AuthContext = Depends(require_permission("blogs.blog", "update")),
    api: BlogApiDep = Depends(BlogApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[BlogUpdateResponse]:
    """Update blog post (full update)."""
    result = await api.update_blog(slug, data, ctx, request)
    
    # Call blog revalidation webhook after successful blog update
    if result and hasattr(result, 'data') and result.data:
        try:
            await trigger_blog_webhook(result, slug, "updated")
        except Exception as e:
            # Log webhook error but don't fail response
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to call blog revalidation webhook: {str(e)}", exc_info=True)
    
    return set_etag_headers_and_return(response, result, SUCCESS_BLOG_UPDATED, request)


@router.patch(
    "/{slug}",
    response_model=StandardResponse[BlogUpdateResponse],
    status_code=status.HTTP_200_OK,
    summary="Partially update blog",
    description="Update specific fields of a blog post without affecting others. Omitted fields are preserved. Use empty string to remove optional fields.",
)
async def patch_blog(
    slug: str,
    data: BlogPatchUpdate,
    ctx: AuthContext = Depends(require_permission("blogs.blog", "update")),
    api: BlogApiDep = Depends(BlogApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[BlogUpdateResponse]:
    """Partially update blog post (PATCH).
    
    Updates only the fields provided in the payload:
    - Omitted fields: Keep existing values
    - null values: Keep existing values
    - Empty string "": Remove field (for images, set to None)
    - Valid values: Update field
    
    **Image Handling Examples:**
    
    1. **Keep existing image** (omit field or use null):
       ```json
       {
         "title": "Updated Title"
         // authorImg and blogImage not included - existing images preserved
       }
       ```
       OR
       ```json
       {
         "title": "Updated Title",
         "authorImg": null  // Existing image kept
       }
       ```
    
    2. **Remove image** (use empty string ""):
       ```json
       {
         "title": "Updated Title",
         "authorImg": "",  // Removes author image (sets to None)
         "blogImage": ""   // Removes blog image (sets to None)
       }
       ```
    
    3. **Replace image** (use base64 data URL or existing URL):
       ```json
       {
         "title": "Updated Title",
         "authorImg": "data:image/png;base64,iVBORw0KGgoAAAANS..."  // Replaces author image
       }
       ```
       OR
       ```json
       {
         "blogImage": "/static/blogs/my-blog/image-123.png"  // Replaces with existing URL
       }
       ```
    
    **Note:** When replacing an image, the old image file is automatically deleted.
    """
    result = await api.patch_blog(slug, data, ctx, request)
    
    # Call blog revalidation webhook after successful blog patch
    if result and hasattr(result, 'data') and result.data:
        try:
            await trigger_blog_webhook(result, slug, "updated")
        except Exception as e:
            # Log webhook error but don't fail response
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to call blog revalidation webhook: {str(e)}", exc_info=True)
    
    return set_etag_headers_and_return(response, result, SUCCESS_BLOG_PATCHED, request)


@router.patch(
    "/{slug}/status",
    response_model=StandardResponse[BlogUpdateResponse],
    status_code=status.HTTP_200_OK,
    summary="Update blog status",
    description="Update the status of a blog post (draft or published)",
)
async def update_blog_status(
    slug: str,
    data: BlogStatusUpdate,
    ctx: AuthContext = Depends(require_permission("blogs.blog", "update")),
    api: BlogApiDep = Depends(BlogApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[BlogUpdateResponse]:
    """Update blog post status."""
    result = await api.update_blog_status(slug, data, ctx, request)
    
    return set_etag_headers_and_return(response, result, SUCCESS_BLOG_STATUS_UPDATED, request)


@router.delete(
    "/{slug}",
    response_model=StandardResponse[BlogDeleteResponse],
    status_code=status.HTTP_200_OK,
    summary=BlogApiDocs.delete["summary"],
    description=BlogApiDocs.delete["description"],
)
async def delete_blog(
    slug: str,
    ctx: AuthContext = Depends(require_permission("blogs.blog", "delete")),
    api: BlogApiDep = Depends(BlogApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[BlogDeleteResponse]:
    """Delete blog post."""
    result = await api.delete_blog(slug, ctx, request)
    
    # Call blog revalidation webhook after successful blog deletion
    if result and hasattr(result, 'data') and result.data:
        try:
            await trigger_blog_webhook(result, slug, "deleted")
        except Exception as e:
            # Log webhook error but don't fail response
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to call blog revalidation webhook: {str(e)}", exc_info=True)
    
    return set_etag_headers_and_return(response, result, SUCCESS_BLOG_DELETED, request)
