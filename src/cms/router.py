"""Blog router for API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, Header, Response, Request, status
from fastapi.responses import Response as FastAPIResponse

from src.schemas import StandardResponse, AuthContext
from src.auth.dependencies import require_permission
from src.cms.dependencies import BlogApiDep
from src.cms.documentations.blogs_api_doc import BlogApiDocs
from src.cms.schemas import (
    BlogCreate,
    BlogUpdate,
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
    ctx: AuthContext = Depends(require_permission("blogs.blog", "read_all")),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    api: BlogApiDep = Depends(BlogApiDep),
    request: Request = None,
    response: Response = None,
) -> StandardResponse[BlogPaginatedResponse] | FastAPIResponse:
    """List all blogs with pagination, filtering, and sorting."""
    result = await api.list_blogs(query, ctx, if_none_match)
    
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
    request: Request = None,
    response: Response = None,
) -> StandardResponse[BlogCreateResponse]:
    """Create a new blog post."""
    result = await api.create_blog(data, ctx, request)
    
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
    ctx: AuthContext = Depends(require_permission("blogs.blog", "read")),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    api: BlogApiDep = Depends(BlogApiDep),
    request: Request = None,
    response: Response = None,
) -> StandardResponse[BlogRead] | FastAPIResponse:
    """Get specific blog with full details."""
    result = await api.get_blog_by_slug(slug, ctx, if_none_match)
    
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
    request: Request = None,
    response: Response = None,
) -> StandardResponse[BlogUpdateResponse]:
    """Update blog post (full update)."""
    result = await api.update_blog(slug, data, ctx, request)
    
    return set_etag_headers_and_return(response, result, SUCCESS_BLOG_UPDATED, request)


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
    request: Request = None,
    response: Response = None,
) -> StandardResponse[BlogDeleteResponse]:
    """Delete blog post."""
    result = await api.delete_blog(slug, ctx, request)
    
    return set_etag_headers_and_return(response, result, SUCCESS_BLOG_DELETED, request)
