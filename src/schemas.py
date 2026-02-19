"""Global schemas for StandardResponse and AuthContext."""
from typing import Generic, TypeVar, Optional, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """Standard API response wrapper for all endpoints.
    
    Success Response:
        {
            "success": true,
            "data": { ... },
            "message": "Operation completed successfully"
        }
    
    Error Response:
        {
            "success": false,
            "error": {
                "code": "ERROR_CODE",
                "details": [{"field": "field_name", "issue": "Error description"}]
            },
            "message": "Human-friendly error message"
        }
    """
    
    success: bool = True
    data: Optional[T] = None
    message: str
    
    model_config = ConfigDict(from_attributes=True)


class ErrorInfo(BaseModel):
    """Error information structure for error responses."""
    
    code: str
    details: list[dict[str, str]]
    
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Error response structure."""
    
    success: bool = False
    error: ErrorInfo
    message: str
    
    model_config = ConfigDict(from_attributes=True)


class AuthContext(BaseModel):
    """Authentication context from JWT token.
    
    Contains user identification and role information extracted from JWT token.
    Used throughout the application for authorization and organization filtering.
    """
    
    user_id: UUID
    role_id: UUID
    role: Optional[str] = None  # Role slug (e.g., "super-admin", "operator")
    permissions_json: Optional[dict[str, Any]] = None  # Full permissions structure from role
    
    model_config = ConfigDict(from_attributes=True)
