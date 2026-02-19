"""User module exceptions."""
from src.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    ForbiddenError,
    BadRequestError,
)
from src.user.constants import (
    ERROR_CODE_USER_NOT_FOUND,
    ERROR_CODE_DUPLICATE_EMAIL,
    ERROR_CODE_ROLE_NOT_FOUND,
    ERROR_CODE_INACTIVE_ROLE,
    ERROR_CODE_INVALID_STATE_TRANSITION,
    ERROR_CODE_USER_NOT_ACTIVE,
    ERROR_CODE_USER_NOT_INVITED,
    ERROR_CODE_INVITATION_NOT_FOUND,
    ERROR_CODE_VALIDATION_ERROR,
    ERROR_USER_NOT_FOUND,
    ERROR_DUPLICATE_EMAIL,
    ERROR_ROLE_NOT_FOUND,
    ERROR_INACTIVE_ROLE,
    ERROR_INVALID_STATE_TRANSITION,
    ERROR_USER_NOT_ACTIVE,
    ERROR_USER_NOT_INVITED,
    ERROR_INVITATION_NOT_FOUND,
    ERROR_EMPTY_REQUEST_BODY,
)


class UserNotFound(NotFoundError):
    """User not found exception."""
    
    def __init__(self, user_id: str):
        super().__init__(
            resource="User",
            resource_id=user_id,
            error_code=ERROR_CODE_USER_NOT_FOUND,
        )


class DuplicateEmail(ConflictError):
    """Duplicate email exception."""
    
    def __init__(self, email: str):
        super().__init__(
            message=ERROR_DUPLICATE_EMAIL,
            error_code=ERROR_CODE_DUPLICATE_EMAIL,
            details=[{"field": "email", "issue": ERROR_DUPLICATE_EMAIL}],
        )


class RoleNotFound(NotFoundError):
    """Role not found exception."""
    
    def __init__(self, role_id: str):
        super().__init__(
            resource="Role",
            resource_id=role_id,
            error_code=ERROR_CODE_ROLE_NOT_FOUND,
        )


class InactiveRole(ValidationError):
    """Inactive role exception."""
    
    def __init__(self, role_id: str):
        super().__init__(
            message=ERROR_INACTIVE_ROLE,
            error_code=ERROR_CODE_INACTIVE_ROLE,
            details=[{"field": "role_id", "issue": ERROR_INACTIVE_ROLE}],
        )


class InvalidStateTransition(ValidationError):
    """Invalid state transition exception."""
    
    def __init__(self, message: str = None):
        super().__init__(
            message=message or ERROR_INVALID_STATE_TRANSITION,
            error_code=ERROR_CODE_INVALID_STATE_TRANSITION,
            details=[{"field": "status", "issue": message or ERROR_INVALID_STATE_TRANSITION}],
        )


class UserNotActive(ValidationError):
    """User not active exception."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_USER_NOT_ACTIVE,
            error_code=ERROR_CODE_USER_NOT_ACTIVE,
            details=[{"field": "status", "issue": ERROR_USER_NOT_ACTIVE}],
        )


class UserNotInvited(ConflictError):
    """User not invited exception."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_USER_NOT_INVITED,
            error_code=ERROR_CODE_USER_NOT_INVITED,
            details=[{"field": "status", "issue": ERROR_USER_NOT_INVITED}],
        )


class InvitationNotFound(NotFoundError):
    """Invitation not found exception."""
    
    def __init__(self, user_id: str):
        super().__init__(
            resource="Invitation",
            resource_id=user_id,
            error_code=ERROR_CODE_INVITATION_NOT_FOUND,
        )


class EmptyRequestBody(BadRequestError):
    """Empty request body exception."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_EMPTY_REQUEST_BODY,
            error_code=ERROR_CODE_VALIDATION_ERROR,
            details=[{"field": "request_body", "issue": "At least one field must be provided for update"}],
        )
