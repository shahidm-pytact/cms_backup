"""User module Pydantic schemas."""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict

from src.pagination import PaginatedResponse


# Request Schemas

class UserInvite(BaseModel):
    """Request schema for inviting a new user."""
    
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., min_length=1, max_length=255, description="User full name")
    role_id: UUID = Field(..., description="Assigned role ID")
    
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Request schema for updating user information (partial update)."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="User full name")
    email: Optional[EmailStr] = Field(None, description="User email address")
    role_id: Optional[UUID] = Field(None, description="Assigned role ID")
    
    model_config = ConfigDict(from_attributes=True)


class UserStatusUpdate(BaseModel):
    """Request schema for updating user status."""
    
    status: str = Field(
        ...,
        description="User status: activate or deactivate"
    )
    
    model_config = ConfigDict(from_attributes=True)


class UserListQuery(BaseModel):
    """Query schema for listing users with pagination and filtering."""
    
    page: int = Field(1, ge=1, description="Page number (≥ 1)")
    page_size: int = Field(20, ge=1, le=100, description="Page size (1-100)")
    search: Optional[str] = Field(None, description="Search by user email or name (case-insensitive partial match)")
    status: Optional[str] = Field(None, description="Filter by user status: invited, active, inactive, expired, cancelled")
    role_id: Optional[UUID] = Field(None, description="Filter by role ID")
    sort_by: str = Field("created_at", description="Sort field: created_at, updated_at, email, name, status")
    sort_order: str = Field("desc", description="Sort order: asc or desc")
    
    model_config = ConfigDict(from_attributes=True)


# Response Schemas

class RoleInfo(BaseModel):
    """Role information in user response."""
    
    id: UUID
    name: str
    
    model_config = ConfigDict(from_attributes=True)


class InvitationStatus(BaseModel):
    """Invitation status information."""
    
    invited_at: Optional[datetime] = None
    invite_expires_at: Optional[datetime] = None
    invite_accepted_at: Optional[datetime] = None
    is_expired: bool
    can_resend: bool
    
    model_config = ConfigDict(from_attributes=True)


class UserRead(BaseModel):
    """Response schema for user details."""
    
    id: UUID
    email: str
    name: str
    status: str
    role_id: UUID
    role: Optional[RoleInfo] = None
    invitation_status: Optional[InvitationStatus] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserListItem(BaseModel):
    """Response schema for user in list (simplified)."""
    
    id: UUID
    email: str
    name: str
    status: str
    role_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserPaginatedResponse(PaginatedResponse[UserListItem]):
    """Paginated response for user list."""
    pass


class UserInviteResponse(BaseModel):
    """Response schema for user invitation."""
    
    id: UUID
    email: str
    name: str
    status: str
    role_id: UUID
    invited_at: datetime
    invite_expires_at: datetime
    invited_by: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class InvitationStatusResponse(BaseModel):
    """Response schema for invitation status."""
    
    user_id: UUID
    email: str
    status: str
    invited_at: datetime
    invite_expires_at: datetime
    invite_accepted_at: Optional[datetime] = None
    is_expired: bool
    can_resend: bool
    invited_by: UUID
    
    model_config = ConfigDict(from_attributes=True)


class ResendInviteResponse(BaseModel):
    """Response schema for resend invitation."""
    
    user_id: UUID
    email: str
    status: str
    invited_at: datetime
    invite_expires_at: datetime
    invited_by: UUID
    
    model_config = ConfigDict(from_attributes=True)


class PasswordResetRequestResponse(BaseModel):
    """Response schema for password reset request."""
    
    user_id: UUID
    email: str
    password_reset_token_expires_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
