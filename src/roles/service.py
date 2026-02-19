"""Role service for business logic."""
from typing import Optional, Any
from uuid import UUID
from datetime import datetime, timezone
from fastapi.responses import Response as FastAPIResponse
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from src.roles.repository import RoleRepository
from src.roles.models import Role
from src.roles.schemas import (
    RoleCreate,
    RoleUpdate,
    RoleListQuery,
    RoleRead,
    RoleListItem,
    RolePaginatedResponse,
)
from src.roles.exceptions import (
    RoleNotFound,
    DuplicateRoleSlug,
    InvalidPermissionsStructure,
    InvalidStateTransition,
    PreconditionRequired,
    PreconditionFailed,
    EmptyRequestBody,
)
from src.roles.constants import (
    STATUS_ACTIVE,
    STATUS_INACTIVE,
    ROLE_TYPE_CUSTOM,
    ROLE_TYPE_SYSTEM,
    ERROR_INVALID_PERMISSIONS_STRUCTURE,
)
from src.exceptions import ValidationError
from src.utils import generate_etag, format_last_modified, set_304_response_headers
from src.schemas import AuthContext


def validate_permissions_structure(permissions_json: dict[str, Any]) -> None:
    """Validate permissions_json structure.
    
    Args:
        permissions_json: Permissions dictionary to validate
        
    Raises:
        InvalidPermissionsStructure: If structure is invalid
    """
    if not isinstance(permissions_json, dict):
        raise InvalidPermissionsStructure("permissions_json must be a dictionary")
    
    # Must have 'modules' object
    if "modules" not in permissions_json:
        raise InvalidPermissionsStructure(
            "permissions_json must have 'modules' object"
        )
    
    if not isinstance(permissions_json.get("modules"), dict):
        raise InvalidPermissionsStructure("permissions_json.modules must be a dictionary")
    
    # Must have 'system' object
    if "system" not in permissions_json:
        raise InvalidPermissionsStructure(
            "permissions_json must have 'system' object"
        )
    
    if not isinstance(permissions_json.get("system"), dict):
        raise InvalidPermissionsStructure("permissions_json.system must be a dictionary")
    
    # System must contain 'super_admin' field
    if "super_admin" not in permissions_json["system"]:
        raise InvalidPermissionsStructure(
            "permissions_json.system must contain 'super_admin' field"
        )
    
    if not isinstance(permissions_json["system"]["super_admin"], bool):
        raise InvalidPermissionsStructure(
            "permissions_json.system.super_admin must be a boolean"
        )
    
    # Validate modules structure: each module should have boolean values
    for module_name, module_permissions in permissions_json["modules"].items():
        if not isinstance(module_permissions, dict):
            raise InvalidPermissionsStructure(
                f"permissions_json.modules.{module_name} must be a dictionary"
            )
        
        for action, value in module_permissions.items():
            if not isinstance(value, bool):
                raise InvalidPermissionsStructure(
                    f"permissions_json.modules.{module_name}.{action} must be a boolean"
                )


class RoleService:
    """Service for role-related business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = RoleRepository(session)
    
    async def create_role(
        self,
        data: RoleCreate,
        ctx: AuthContext,
    ) -> RoleRead:
        """Create a new custom role with permissions assignment.
        
        Args:
            data: Role creation data
            ctx: AuthContext with user information
            
        Returns:
            RoleRead with created role details
            
        Raises:
            DuplicateRoleSlug: If slug already exists (case-insensitive)
            InvalidPermissionsStructure: If permissions_json structure is invalid
        """
        # Check if slug already exists (case-insensitive)
        existing_role = await self.repository.get_by_slug(data.slug)
        if existing_role:
            raise DuplicateRoleSlug(data.slug)
        
        # Validate permissions_json structure
        validate_permissions_structure(data.permissions_json)
        
        # Create role
        role = Role(
            slug=data.slug.lower(),  # Store slug in lowercase
            name=data.name,
            status=data.status or STATUS_ACTIVE,
            role_type=ROLE_TYPE_CUSTOM,  # Default is custom
            permissions_json=data.permissions_json,
            created_by=ctx.user_id,
            updated_by=ctx.user_id,
        )
        
        # Save role
        role = await self.repository.create(role)
        
        # Commit transaction
        await self.session.commit()
        await self.session.refresh(role)
        
        # Return response
        result = RoleRead.model_validate(role)
        result._etag = generate_etag(role.updated_at)
        result._last_modified = role.updated_at
        return result
    
    async def get_role_by_id(
        self,
        role_id: UUID,
        if_none_match: Optional[str] = None,
    ) -> RoleRead | FastAPIResponse:
        """Get role details with permissions.
        
        Args:
            role_id: Role ID to retrieve
            if_none_match: ETag from If-None-Match header
            
        Returns:
            RoleRead with role details, or FastAPIResponse (304) if unchanged
            
        Raises:
            RoleNotFound: If role not found
        """
        # Get role
        role = await self.repository.get_by_id(role_id)
        if not role:
            raise RoleNotFound(str(role_id))
        
        # Generate ETag
        etag = generate_etag(role.updated_at)
        
        # Check If-None-Match header
        if if_none_match and if_none_match == etag:
            response = FastAPIResponse(status_code=status.HTTP_304_NOT_MODIFIED)
            return set_304_response_headers(None, response, etag, role.updated_at)
        
        # Build response
        result = RoleRead.model_validate(role)
        result._etag = etag
        result._last_modified = role.updated_at
        return result
    
    async def list_roles(
        self,
        query: RoleListQuery,
        if_none_match: Optional[str] = None,
    ) -> RolePaginatedResponse | FastAPIResponse:
        """List roles with pagination, filtering, search, and sorting.
        
        Args:
            query: Query parameters for filtering and pagination
            if_none_match: ETag from If-None-Match header
            
        Returns:
            RolePaginatedResponse with roles list, or FastAPIResponse (304) if unchanged
        """
        # Get roles from repository
        roles, total = await self.repository.list_with_pagination(
            page=query.page,
            page_size=query.page_size,
            search=query.search,
            status=query.status,
            role_type=query.role_type,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        )
        
        # Generate collection ETag from latest role updated_at
        latest_updated_at = None
        if roles:
            latest_updated_at = max(role.updated_at for role in roles)
            etag = generate_etag(latest_updated_at)
            
            # Check If-None-Match header
            if if_none_match and if_none_match == etag:
                response = FastAPIResponse(status_code=status.HTTP_304_NOT_MODIFIED)
                return set_304_response_headers(None, response, etag, latest_updated_at)
        else:
            etag = None
        
        # Build response items
        items = [RoleListItem.model_validate(role) for role in roles]
        
        # Calculate pagination metadata
        total_pages = (total + query.page_size - 1) // query.page_size if total > 0 else 0
        next_page = f"?page={query.page + 1}" if query.page < total_pages else None
        prev_page = f"?page={query.page - 1}" if query.page > 1 else None
        
        # Build response
        result = RolePaginatedResponse(
            items=items,
            total=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages,
            next_page=next_page,
            prev_page=prev_page,
        )
        
        # Attach ETag for router to set header
        if etag:
            result._etag = etag
            if latest_updated_at:
                result._last_modified = latest_updated_at
        
        return result
    
    async def update_role(
        self,
        role_id: UUID,
        data: RoleUpdate,
        ctx: AuthContext,
        if_match: Optional[str] = None,
    ) -> RoleRead:
        """Update role information (name, permissions_json, status).
        
        Args:
            role_id: Role ID to update
            data: Role update data (partial update)
            ctx: AuthContext with user information
            if_match: ETag from If-Match header (required for update)
            
        Returns:
            RoleRead with updated role details
            
        Raises:
            RoleNotFound: If role not found
            PreconditionRequired: If If-Match header is missing
            PreconditionFailed: If ETag mismatch
            EmptyRequestBody: If request body is empty
            ValidationError: If system role tries to update name or permissions_json
            InvalidPermissionsStructure: If permissions_json structure is invalid
            InvalidStateTransition: If status transition is invalid
        """
        # Check if request body is empty
        if not any([data.name is not None, data.permissions_json is not None, data.status is not None]):
            raise EmptyRequestBody()
        
        # Check If-Match header (required for update)
        if not if_match:
            raise PreconditionRequired()
        
        # Get current role
        role = await self.repository.get_by_id(role_id)
        if not role:
            raise RoleNotFound(str(role_id))
        
        # Validate ETag
        current_etag = generate_etag(role.updated_at)
        if if_match != current_etag:
            raise PreconditionFailed("Resource version mismatch. Please refresh and try again.")
        
        # Check if role is system role - can only update status
        if role.role_type == ROLE_TYPE_SYSTEM:
            if data.name is not None:
                raise ValidationError(
                    message="System roles cannot update name field. Only status can be updated.",
                    error_code="VALIDATION_ERROR",
                    details=[{"field": "name", "issue": "System roles cannot update name field"}],
                )
            if data.permissions_json is not None:
                raise ValidationError(
                    message="System roles cannot update permissions_json field. Only status can be updated.",
                    error_code="VALIDATION_ERROR",
                    details=[{"field": "permissions_json", "issue": "System roles cannot update permissions_json field"}],
                )
        
        # Validate status transition (if status is being updated)
        if data.status is not None:
            if data.status == role.status:
                raise InvalidStateTransition(f"Role is already {data.status}")
        
        # Update fields (only provided fields)
        if data.name is not None:
            role.name = data.name
        
        if data.permissions_json is not None:
            # Validate permissions_json structure
            validate_permissions_structure(data.permissions_json)
            role.permissions_json = data.permissions_json
        
        if data.status is not None:
            role.status = data.status
        
        # Update audit fields
        role.updated_by = ctx.user_id
        role.updated_at = datetime.now(timezone.utc)
        
        # Save role
        role = await self.repository.update(role)
        
        # Commit transaction
        await self.session.commit()
        await self.session.refresh(role)
        
        # Return response
        result = RoleRead.model_validate(role)
        result._etag = generate_etag(role.updated_at)
        result._last_modified = role.updated_at
        return result
