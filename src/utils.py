"""Centralized utilities for ETag and X-Request-ID header handling."""
from typing import Optional, TypeVar
from datetime import datetime
from fastapi import Response, Request
from fastapi.responses import Response as FastAPIResponse
import httpx
import logging

from src.schemas import StandardResponse
from src.config import settings

T = TypeVar("T")


def generate_etag(updated_at: datetime) -> str:
    """Generate ETag from updated_at timestamp.
    
    Centralized ETag generation function for use across all modules.
    Uses ISO 8601 format with timestamp.
    
    Args:
        updated_at: The datetime when the resource was last updated
        
    Returns:
        ETag string in format: YYYYMMDDTHHMMSSZ
    """
    return updated_at.strftime("%Y%m%dT%H%M%SZ")


def format_last_modified(updated_at: datetime) -> str:
    """Format datetime for Last-Modified header (RFC 7231 format).
    
    Centralized function for formatting Last-Modified HTTP header.
    Uses RFC 7231 format as required by HTTP specification.
    
    Args:
        updated_at: The datetime when the resource was last updated
        
    Returns:
        Formatted datetime string in RFC 7231 format
    """
    return updated_at.strftime("%a, %d %b %Y %H:%M:%S GMT")


def set_request_id_header(
    request: Optional[Request],
    response: Response | FastAPIResponse | None,
) -> None:
    """Set X-Request-ID header on response from request state.
    
    Centralized function for setting X-Request-ID header on responses.
    This ensures the header is set consistently across all endpoints,
    even when middleware might not handle edge cases (e.g., 304 responses).
    
    Args:
        request: FastAPI Request object (can be None)
        response: FastAPI Response or FastAPIResponse object (can be None)
    """
    if request and response:
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            response.headers["X-Request-ID"] = request_id


def set_etag_headers_and_return(
    response: Response | None,
    result: T,
    message: str,
    request: Optional[Request] = None,
) -> StandardResponse[T]:
    """Set ETag, Last-Modified, and X-Request-ID headers and return StandardResponse.
    
    This helper function extracts the header setting logic from routers
    to keep them thin and clean. This is the centralized implementation for
    use across all modules.
    
    Args:
        response: FastAPI Response object (can be None)
        result: The result data from service layer (should have _etag and optionally _last_modified attributes)
        message: Success message for StandardResponse
        request: FastAPI Request object (optional, used to set X-Request-ID header)
        
    Returns:
        StandardResponse with data and message, with headers set if applicable
    """
    if response:
        response.headers["Cache-Control"] = "private, no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        # Set ETag and Last-Modified headers
        if response and hasattr(result, "_etag"):
            response.headers["ETag"] = result._etag
            if hasattr(result, "_last_modified"):
                response.headers["Last-Modified"] = format_last_modified(result._last_modified)
        
    # Set X-Request-ID header
    set_request_id_header(request, response)
    
    return StandardResponse(
        data=result,
        message=message,
    )


def set_304_response_headers(
    request: Optional[Request],
    response: FastAPIResponse,
    etag: str,
    last_modified: Optional[datetime] = None,
) -> FastAPIResponse:
    """Set headers for 304 Not Modified response.
    
    Centralized function for setting headers on 304 responses.
    Sets ETag, Last-Modified (if provided), and X-Request-ID headers.
    
    Args:
        request: FastAPI Request object (can be None)
        response: FastAPIResponse object (304 response)
        etag: ETag value to set
        last_modified: Optional datetime for Last-Modified header
        
    Returns:
        FastAPIResponse with headers set
    """
    response.headers["ETag"] = etag
    if last_modified:
        response.headers["Last-Modified"] = format_last_modified(last_modified)
    set_request_id_header(request, response)
    return response


async def call_blog_revalidation_webhook(blog_slug: str, event_type: str) -> bool:
    """Call the blog revalidation webhook after blog operations.
    
    Args:
        blog_slug: The slug of the blog that was created/updated/deleted
        event_type: The type of event ("created", "updated", "deleted")
        
    Returns:
        True if webhook call was successful, False otherwise
    """
    if not settings.blog_revalidation_webhook_secret:
        logger = logging.getLogger(__name__)
        logger.warning("Blog revalidation webhook secret not configured, skipping webhook call")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            # Use different headers based on event type
            headers = {
                "Content-Type": "application/json"
            }
            
            if event_type == "updated":
                headers["x-webhook-secret"] = settings.blog_revalidation_webhook_secret
            else:
                headers["Authorization"] = f"Bearer {settings.blog_revalidation_webhook_secret}"
            
            response = await client.post(
                settings.blog_revalidation_webhook_url,
                headers=headers,
                json={"slug": blog_slug, "event_type": event_type},
                timeout=10.0
            )
            
            if response.status_code == 200:
                logger = logging.getLogger(__name__)
                logger.info(f"Blog revalidation webhook called successfully for slug: {blog_slug}, event: {event_type}")
                return True
            else:
                logger = logging.getLogger(__name__)
                logger.error(f"Blog revalidation webhook failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to call blog revalidation webhook for slug {blog_slug}, event {event_type}: {str(e)}")
        return False


async def trigger_blog_webhook(result, slug: str, event_type: str) -> None:
    """Centralized function to trigger webhook for blog operations.
    
    Args:
        result: API response object
        slug: Blog slug
        event_type: Event type ("created", "updated", "deleted")
    """
    if result and hasattr(result, 'data') and result.data:
        try:
            await call_blog_revalidation_webhook(slug, event_type)
        except Exception as e:
            # Log webhook error but don't fail response
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to call blog revalidation webhook: {str(e)}", exc_info=True)
