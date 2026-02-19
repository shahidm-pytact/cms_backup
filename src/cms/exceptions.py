"""Blog CMS module exceptions."""
from src.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    BadRequestError,
)
from src.cms.constants import (
    ERROR_CODE_BLOG_NOT_FOUND,
    ERROR_CODE_DUPLICATE_BLOG_SLUG,
    ERROR_CODE_VALIDATION_ERROR,
    ERROR_BLOG_NOT_FOUND,
    ERROR_DUPLICATE_BLOG_SLUG,
    ERROR_BLOG_VALIDATION_ERROR,
    ERROR_EMPTY_REQUEST_BODY,
    ERROR_INVALID_SECTION_STRUCTURE,
    ERROR_INVALID_BLOCK_STRUCTURE,
    ERROR_DUPLICATE_SECTION_ID,
    ERROR_DUPLICATE_BLOCK_ID,
)


class BlogNotFound(NotFoundError):
    """Blog not found exception."""
    
    def __init__(self, slug: str):
        super().__init__(
            resource="Blog",
            resource_id=slug,
            error_code=ERROR_CODE_BLOG_NOT_FOUND,
        )


class BlogSlugExists(ConflictError):
    """Duplicate blog slug exception."""
    
    def __init__(self, slug: str):
        super().__init__(
            message=ERROR_DUPLICATE_BLOG_SLUG,
            error_code=ERROR_CODE_DUPLICATE_BLOG_SLUG,
            details=[{"field": "slug", "issue": f"Blog with slug '{slug}' already exists"}],
        )


class BlogValidationError(ValidationError):
    """Blog validation error exception."""
    
    def __init__(self, message: str, details: list[dict[str, str]] = None):
        super().__init__(
            message=message or ERROR_BLOG_VALIDATION_ERROR,
            error_code=ERROR_CODE_VALIDATION_ERROR,
            details=details or [{"field": "validation", "issue": message or ERROR_BLOG_VALIDATION_ERROR}],
        )


class EmptyRequestBody(BadRequestError):
    """Empty request body exception."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_EMPTY_REQUEST_BODY,
            error_code=ERROR_CODE_VALIDATION_ERROR,
            details=[{"field": "request_body", "issue": "At least one field must be provided for update"}],
        )
