"""Audit Log Pydantic schemas."""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

from src.pagination import PaginatedResponse
from src.audit_logs.constants import ERROR_INVALID_SORT_FIELD, ERROR_INVALID_SORT_ORDER


class AuditLogListQuery(BaseModel):
    """Query schema for listing audit logs with pagination and filtering."""
    
    page: int = Field(1, ge=1, description="Page number (≥ 1)")
    page_size: int = Field(20, ge=1, le=100, description="Page size (1-100)")
    user_id: Optional[UUID] = Field(None, description="Filter by user ID (actor)")
    entity_type: Optional[str] = Field(None, description="Filter by entity type (e.g., 'user', 'role')")
    action: Optional[str] = Field(None, description="Filter by action (e.g., 'create', 'update', 'delete')")
    date_from: Optional[str] = Field(None, description="Filter from date (ISO 8601 format, UTC, e.g., '2024-01-01T00:00:00Z')")
    date_to: Optional[str] = Field(None, description="Filter to date (ISO 8601 format, UTC, e.g., '2024-01-31T23:59:59Z')")
    sort_by: str = Field("created_at", description="Sort field: created_at, user_id, entity_type, action")
    sort_order: str = Field("desc", description="Sort order: asc or desc")
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """Validate sort_by field."""
        allowed_fields = ["created_at", "user_id", "entity_type", "action"]
        if v not in allowed_fields:
            raise ValueError(ERROR_INVALID_SORT_FIELD)
        return v
    
    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate sort_order field."""
        allowed_orders = ["asc", "desc"]
        if v not in allowed_orders:
            raise ValueError(ERROR_INVALID_SORT_ORDER)
        return v


class AuditLogRead(BaseModel):
    """Response schema for audit log details."""
    
    id: UUID
    user_id: Optional[UUID] = None
    action: str
    entity_type: str
    entity_id: UUID
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogListItem(BaseModel):
    """Response schema for audit log list item (without old_values/new_values)."""
    
    id: UUID
    user_id: Optional[UUID] = None
    action: str
    entity_type: str
    entity_id: UUID
    description: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogPaginatedResponse(PaginatedResponse[AuditLogListItem]):
    """Paginated response for audit log list."""
    pass
