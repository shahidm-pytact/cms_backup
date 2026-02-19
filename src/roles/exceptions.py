"""Role module exceptions."""
from src.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    PreconditionFailedError,
    PreconditionRequiredError,
    BadRequestError,
)
from src.roles.constants import (
    ERROR_CODE_ROLE_NOT_FOUND,
    ERROR_CODE_DUPLICATE_ROLE_SLUG,
    ERROR_CODE_INVALID_PERMISSIONS_STRUCTURE,
    ERROR_CODE_INVALID_STATE_TRANSITION,
    ERROR_CODE_VALIDATION_ERROR,
    ERROR_ROLE_NOT_FOUND,
    ERROR_DUPLICATE_ROLE_SLUG,
    ERROR_INVALID_PERMISSIONS_STRUCTURE,
    ERROR_INVALID_STATE_TRANSITION,
    ERROR_EMPTY_REQUEST_BODY,
)


class RoleNotFound(NotFoundError):
    """Role not found exception."""
    
    def __init__(self, role_id: str):
        super().__init__(
            resource="Role",
            resource_id=role_id,
            error_code=ERROR_CODE_ROLE_NOT_FOUND,
        )


class DuplicateRoleSlug(ConflictError):
    """Duplicate role slug exception."""
    
    def __init__(self, slug: str):
        super().__init__(
            message=ERROR_DUPLICATE_ROLE_SLUG,
            error_code=ERROR_CODE_DUPLICATE_ROLE_SLUG,
            details=[{"field": "slug", "issue": ERROR_DUPLICATE_ROLE_SLUG}],
        )


class InvalidPermissionsStructure(ValidationError):
    """Invalid permissions_json structure exception."""
    
    def __init__(self, message: str = None):
        super().__init__(
            message=message or ERROR_INVALID_PERMISSIONS_STRUCTURE,
            error_code=ERROR_CODE_INVALID_PERMISSIONS_STRUCTURE,
            details=[{"field": "permissions_json", "issue": message or ERROR_INVALID_PERMISSIONS_STRUCTURE}],
        )


class InvalidStateTransition(ValidationError):
    """Invalid status transition exception."""
    
    def __init__(self, message: str = None):
        super().__init__(
            message=message or ERROR_INVALID_STATE_TRANSITION,
            error_code=ERROR_CODE_INVALID_STATE_TRANSITION,
            details=[{"field": "status", "issue": message or ERROR_INVALID_STATE_TRANSITION}],
        )


class PreconditionRequired(PreconditionRequiredError):
    """If-Match header required exception."""
    
    def __init__(self):
        super().__init__(
            message="If-Match header required for update operations",
            details=[{"field": "If-Match", "issue": "If-Match header is required for update operations"}],
        )


class PreconditionFailed(PreconditionFailedError):
    """ETag mismatch exception."""
    
    def __init__(self, message: str = None):
        super().__init__(
            message=message or "Resource version mismatch. Please refresh and try again.",
            details=[{"field": "If-Match", "issue": message or "ETag mismatch"}],
        )


class EmptyRequestBody(BadRequestError):
    """Empty request body exception."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_EMPTY_REQUEST_BODY,
            error_code=ERROR_CODE_VALIDATION_ERROR,
            details=[{"field": "request_body", "issue": "At least one field must be provided for update"}],
        )
