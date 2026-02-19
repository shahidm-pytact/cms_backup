"""Role module Pydantic schemas."""
from typing import Optional, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

from src.pagination import PaginatedResponse


# Request Schemas

class RoleCreate(BaseModel):
    """Request schema for creating a new role."""
    
    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique role identifier (lowercase alphanumeric and hyphens only)"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Role display name"
    )
    permissions_json: dict[str, Any] = Field(
        ...,
        description="Assigned permissions structure: { 'modules': {...}, 'system': {...} }"
    )
    status: Optional[str] = Field(
        "active",
        description="Role activation status: active, inactive"
    )
    
    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format: lowercase alphanumeric and hyphens only."""
        v_lower = v.lower()
        # Check if contains only lowercase alphanumeric and hyphens
        if not all(c.isalnum() or c == "-" for c in v_lower):
            raise ValueError("Slug must contain only lowercase alphanumeric characters and hyphens")
        return v_lower
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize status value."""
        if v is None:
            return "active"
        v_lower = v.lower()
        if v_lower not in ("active", "inactive"):
            raise ValueError("Status must be 'active' or 'inactive'")
        return v_lower
    
    model_config = ConfigDict(from_attributes=True)


class RoleUpdate(BaseModel):
    """Request schema for updating role information (partial update)."""
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Role display name"
    )
    permissions_json: Optional[dict[str, Any]] = Field(
        None,
        description="Assigned permissions structure: { 'modules': {...}, 'system': {...} }"
    )
    status: Optional[str] = Field(
        None,
        description="Role activation status: active, inactive (case-insensitive)"
    )
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize status value."""
        if v is None:
            return None
        v_lower = v.lower()
        if v_lower not in ("active", "inactive"):
            raise ValueError("Status must be 'active' or 'inactive'")
        return v_lower
    
    model_config = ConfigDict(from_attributes=True)


class RoleListQuery(BaseModel):
    """Query schema for listing roles with pagination and filtering."""
    
    page: int = Field(1, ge=1, description="Page number (≥ 1)")
    page_size: int = Field(20, ge=1, le=100, description="Page size (1-100)")
    search: Optional[str] = Field(None, description="Search by role name or slug (case-insensitive partial match)")
    status: Optional[str] = Field(None, description="Filter by status: active, inactive")
    role_type: Optional[str] = Field(None, description="Filter by role type: system, custom")
    sort_by: str = Field("created_at", description="Sort field: created_at, updated_at, name, slug, status")
    sort_order: str = Field("desc", description="Sort order: asc or desc")
    
    model_config = ConfigDict(from_attributes=True)


# Response Schemas

class RoleRead(BaseModel):
    """Response schema for role details."""
    
    id: UUID
    slug: str
    name: str
    status: str
    role_type: str
    permissions_json: dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class RoleListItem(BaseModel):
    """Response schema for role in list (simplified)."""
    
    id: UUID
    slug: str
    name: str
    status: str
    role_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class RolePaginatedResponse(PaginatedResponse[RoleListItem]):
    """Paginated response for role list."""
    pass
