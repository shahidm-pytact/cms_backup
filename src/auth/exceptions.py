"""Authentication-specific exceptions."""
from src.exceptions import (
    UnauthenticatedError,
    ConflictError,
    ValidationError,
    NotFoundError,
    BadRequestError,
)
from src.auth.constants import (
    ERROR_CODE_INVALID_CREDENTIALS,
    ERROR_CODE_INACTIVE_USER,
    ERROR_CODE_INACTIVE_ROLE,
    ERROR_CODE_TOKEN_EXPIRED,
    ERROR_CODE_INVALID_TOKEN,
    ERROR_CODE_INVITATION_NOT_FOUND,
    ERROR_CODE_INVITATION_EXPIRED,
    ERROR_CODE_INVITATION_ALREADY_ACCEPTED,
    ERROR_CODE_INVITATION_NOT_ACCEPTED,
    ERROR_CODE_PASSWORD_ALREADY_SET,
    ERROR_CODE_RESET_TOKEN_NOT_FOUND,
    ERROR_CODE_RESET_TOKEN_EXPIRED,
    ERROR_CODE_VALIDATION_ERROR,
    ERROR_CODE_INVALID_REQUEST,
    ERROR_INVALID_CREDENTIALS,
    ERROR_INACTIVE_USER,
    ERROR_INACTIVE_ROLE,
    ERROR_TOKEN_EXPIRED,
    ERROR_INVITATION_NOT_FOUND,
    ERROR_INVITATION_EXPIRED,
    ERROR_INVITATION_ALREADY_ACCEPTED,
    ERROR_INVITATION_NOT_ACCEPTED,
    ERROR_PASSWORD_ALREADY_SET,
    ERROR_RESET_TOKEN_NOT_FOUND,
    ERROR_RESET_TOKEN_EXPIRED,
    ERROR_PASSWORD_VALIDATION_FAILED,
)


class InvalidCredentialsError(UnauthenticatedError):
    """Invalid email or password."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_INVALID_CREDENTIALS,
            error_code=ERROR_CODE_INVALID_CREDENTIALS,
            details=[{"field": "credentials", "issue": ERROR_INVALID_CREDENTIALS}],
        )


class InactiveUserError(UnauthenticatedError):
    """User account is not active."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_INACTIVE_USER,
            error_code=ERROR_CODE_INACTIVE_USER,
            details=[{"field": "user", "issue": ERROR_INACTIVE_USER}],
        )


class InactiveRoleError(UnauthenticatedError):
    """User's role is not active."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_INACTIVE_ROLE,
            error_code=ERROR_CODE_INACTIVE_ROLE,
            details=[{"field": "role", "issue": ERROR_INACTIVE_ROLE}],
        )


class TokenExpiredError(UnauthenticatedError):
    """JWT token has expired."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_TOKEN_EXPIRED,
            error_code=ERROR_CODE_TOKEN_EXPIRED,
            details=[{"field": "token", "issue": ERROR_TOKEN_EXPIRED}],
        )


class InvalidTokenError(UnauthenticatedError):
    """Invalid JWT token."""
    
    def __init__(self):
        super().__init__(
            message="Invalid token",
            error_code=ERROR_CODE_INVALID_TOKEN,
            details=[{"field": "token", "issue": "Invalid token"}],
        )


class InvitationNotFoundError(NotFoundError):
    """Invitation token not found."""
    
    def __init__(self, token: str):
        super().__init__(
            resource="Invitation",
            resource_id=token,
            error_code=ERROR_CODE_INVITATION_NOT_FOUND,
            details=[{"field": "token", "issue": ERROR_INVITATION_NOT_FOUND}],
        )


class InvitationExpiredError(ConflictError):
    """Invitation token has expired."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_INVITATION_EXPIRED,
            error_code=ERROR_CODE_INVITATION_EXPIRED,
            details=[{"field": "token", "issue": ERROR_INVITATION_EXPIRED}],
        )


class InvitationAlreadyAcceptedError(ConflictError):
    """Invitation has already been accepted."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_INVITATION_ALREADY_ACCEPTED,
            error_code=ERROR_CODE_INVITATION_ALREADY_ACCEPTED,
            details=[{"field": "invitation", "issue": ERROR_INVITATION_ALREADY_ACCEPTED}],
        )


class InvitationNotAcceptedError(ConflictError):
    """Invitation has not been accepted yet."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_INVITATION_NOT_ACCEPTED,
            error_code=ERROR_CODE_INVITATION_NOT_ACCEPTED,
            details=[{"field": "invitation", "issue": ERROR_INVITATION_NOT_ACCEPTED}],
        )


class PasswordAlreadySetError(ConflictError):
    """Password has already been set."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_PASSWORD_ALREADY_SET,
            error_code=ERROR_CODE_PASSWORD_ALREADY_SET,
            details=[{"field": "password", "issue": ERROR_PASSWORD_ALREADY_SET}],
        )


class ResetTokenNotFoundError(NotFoundError):
    """Password reset token not found."""
    
    def __init__(self, token: str):
        super().__init__(
            resource="Reset token",
            resource_id=token,
            error_code=ERROR_CODE_RESET_TOKEN_NOT_FOUND,
            details=[{"field": "token", "issue": ERROR_RESET_TOKEN_NOT_FOUND}],
        )


class ResetTokenExpiredError(ConflictError):
    """Password reset token has expired."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_RESET_TOKEN_EXPIRED,
            error_code=ERROR_CODE_RESET_TOKEN_EXPIRED,
            details=[{"field": "token", "issue": ERROR_RESET_TOKEN_EXPIRED}],
        )


class PasswordValidationError(ValidationError):
    """Password validation failed."""
    
    def __init__(self, details: list[dict[str, str]]):
        super().__init__(
            message=ERROR_PASSWORD_VALIDATION_FAILED,
            error_code=ERROR_CODE_VALIDATION_ERROR,
            details=details,
        )


class InvalidRequestError(BadRequestError):
    """Invalid request format."""
    
    def __init__(self, message: str = "Invalid request", details: list[dict[str, str]] | None = None):
        super().__init__(
            message=message,
            error_code=ERROR_CODE_INVALID_REQUEST,
            details=details or [{"field": "request", "issue": message}],
        )
