"""Base exception classes and global exception handlers."""
from typing import Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, DatabaseError
from pydantic import ValidationError

from src.schemas import StandardResponse, ErrorInfo, ErrorResponse
from src.utils import set_request_id_header


class AppException(Exception):
    """Base exception class for all application exceptions."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[list[dict[str, str]]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or []
        super().__init__(self.message)


class BadRequestError(AppException):
    """400 Bad Request - Invalid input or request format."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "INVALID_REQUEST",
        details: Optional[list[dict[str, str]]] = None,
    ):
        super().__init__(message, error_code, status.HTTP_400_BAD_REQUEST, details)


class UnauthenticatedError(AppException):
    """401 Unauthorized - Missing or invalid authentication token."""
    
    def __init__(
        self,
        message: str = "Authentication required",
        error_code: str = "UNAUTHENTICATED",
        details: Optional[list[dict[str, str]]] = None,
    ):
        super().__init__(message, error_code, status.HTTP_401_UNAUTHORIZED, details)


class ForbiddenError(AppException):
    """403 Forbidden - Valid token but insufficient permissions."""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        error_code: str = "INSUFFICIENT_PERMISSIONS",
        details: Optional[list[dict[str, str]]] = None,
    ):
        super().__init__(message, error_code, status.HTTP_403_FORBIDDEN, details)


class NotFoundError(AppException):
    """404 Not Found - Resource not found."""
    
    def __init__(
        self,
        resource: str,
        resource_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[list[dict[str, str]]] = None,
    ):
        if error_code is None:
            error_code = f"{resource.upper().replace(' ', '_')}_NOT_FOUND"
        
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with ID {resource_id} not found"
        
        if details is None:
            details = [{"field": "id", "issue": message}]
        
        super().__init__(message, error_code, status.HTTP_404_NOT_FOUND, details)


class ConflictError(AppException):
    """409 Conflict - Resource conflict or duplicate."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "CONFLICT",
        details: Optional[list[dict[str, str]]] = None,
    ):
        super().__init__(message, error_code, status.HTTP_409_CONFLICT, details)


class ValidationError(AppException):
    """422 Unprocessable Entity - Validation error."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        error_code: str = "VALIDATION_ERROR",
        details: Optional[list[dict[str, str]]] = None,
    ):
        super().__init__(message, error_code, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class PreconditionFailedError(AppException):
    """412 Precondition Failed - ETag mismatch."""
    
    def __init__(
        self,
        message: str = "Resource version mismatch",
        error_code: str = "PRECONDITION_FAILED",
        details: Optional[list[dict[str, str]]] = None,
    ):
        super().__init__(message, error_code, status.HTTP_412_PRECONDITION_FAILED, details)


class PreconditionRequiredError(AppException):
    """428 Precondition Required - If-Match header missing."""
    
    def __init__(
        self,
        message: str = "If-Match header required",
        error_code: str = "PRECONDITION_REQUIRED",
        details: Optional[list[dict[str, str]]] = None,
    ):
        super().__init__(message, error_code, status.HTTP_428_PRECONDITION_REQUIRED, details)


class InternalServerError(AppException):
    """500 Internal Server Error - Unexpected server error."""
    
    def __init__(
        self,
        message: str = "Internal server error",
        error_code: str = "INTERNAL_ERROR",
        details: Optional[list[dict[str, str]]] = None,
    ):
        super().__init__(message, error_code, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


# Exception Handlers

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions."""
    error_info = ErrorInfo(
        code=exc.error_code,
        details=exc.details,
    )
    
    response = JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=error_info,
            message=exc.message,
        ).model_dump(),
    )
    
    # Add WWW-Authenticate header for 401 errors (OAuth2 compatibility)
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        response.headers["WWW-Authenticate"] = "Bearer"
    
    # Set X-Request-ID header
    set_request_id_header(request, response)
    
    return response


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        issue = error["msg"]
        details.append({"field": field, "issue": issue})
    
    error_info = ErrorInfo(
        code="VALIDATION_ERROR",
        details=details,
    )
    
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error=error_info,
            message="Validation failed. Please check your input.",
        ).model_dump(),
    )
    
    # Set X-Request-ID header
    set_request_id_header(request, response)
    
    return response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    error_info = ErrorInfo(
        code="HTTP_ERROR",
        details=[{"field": "request", "issue": exc.detail}],
    )
    
    response = JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=error_info,
            message=exc.detail,
        ).model_dump(),
    )
    
    # Set X-Request-ID header
    set_request_id_header(request, response)
    
    return response


async def database_exception_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Handle database exceptions."""
    error_info = ErrorInfo(
        code="DATABASE_ERROR",
        details=[{"field": "database", "issue": "A database error occurred"}],
    )
    
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=error_info,
            message="A database error occurred. Please try again later.",
        ).model_dump(),
    )
    
    # Set X-Request-ID header
    set_request_id_header(request, response)
    
    return response


async def catch_all_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler for unexpected errors."""
    error_info = ErrorInfo(
        code="INTERNAL_ERROR",
        details=[{"field": "server", "issue": "An unexpected error occurred"}],
    )
    
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=error_info,
            message="An unexpected error occurred. Please try again later.",
        ).model_dump(),
    )
    
    # Set X-Request-ID header
    set_request_id_header(request, response)
    
    return response
