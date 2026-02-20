"""Authentication request and response schemas."""
from typing import Optional, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator


#Google Login
class GoogleAuthRequest(BaseModel):
    token: str

# Login 
class LoginRequest(BaseModel):
    """Login request schema."""
    
    email: EmailStr = Field(..., max_length=254, description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    
    model_config = ConfigDict(from_attributes=True)

# Set Password
class SetPasswordRequest(BaseModel):
    """Set password request schema (for invitation and password reset)."""
    
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (must contain uppercase, lowercase, number, and special character)",
    )
    confirm_password: str = Field(..., description="Password confirmation")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 128:
            raise ValueError("Password must be at most 128 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v
    
    @model_validator(mode="after")
    def validate_passwords_match(self):
        """Validate that passwords match."""
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self
    
    model_config = ConfigDict(from_attributes=True)


class ResetPasswordRequest(BaseModel):
    """Request password reset schema."""
    
    email: EmailStr = Field(..., max_length=254, description="User email address")
    
    model_config = ConfigDict(from_attributes=True)


# Response Schemas

class UserInfo(BaseModel):
    """User information in response."""
    
    id: UUID
    email: str
    name: str
    role_id: UUID
    role: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class RoleInfo(BaseModel):
    """Role information in response."""
    
    id: UUID
    slug: str
    name: str
    status: str
    
    model_config = ConfigDict(from_attributes=True)


class PermissionsResponse(BaseModel):
    """Permissions structure in response."""
    
    modules: dict[str, dict[str, bool]]
    system: dict[str, bool]
    flat_list: list[str]
    
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """OAuth2 token response schema."""
    
    access_token: str
    token_type: str
    expires_in: int
    scope: str = ""
    
    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """Login response schema."""
    
    access_token: str
    token_type: str
    expires_in: int
    user: UserInfo
    
    model_config = ConfigDict(from_attributes=True)


class InvitationValidateResponse(BaseModel):
    """Invitation validation response schema."""
    
    valid: bool
    user_id: UUID
    email: str
    status: str
    invite_expires_at: datetime
    is_expired: bool
    
    model_config = ConfigDict(from_attributes=True)


class InvitationAcceptResponse(BaseModel):
    """Invitation accept response schema."""
    
    user_id: UUID
    email: str
    status: str
    invite_accepted_at: datetime
    can_set_password: bool
    
    model_config = ConfigDict(from_attributes=True)


class SetPasswordResponse(BaseModel):
    """Set password response schema."""
    
    user_id: UUID
    email: str
    status: str
    password_set_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ResetPasswordResponse(BaseModel):
    """Password reset response schema."""
    
    user_id: UUID
    email: str
    password_reset_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserContextResponse(BaseModel):
    """User context response schema for /auth/me endpoint."""
    
    user: UserInfo
    role: RoleInfo
    
    model_config = ConfigDict(from_attributes=True)
    
    # ETag support
    _etag: Optional[str] = None
    _last_modified: Optional[datetime] = None
