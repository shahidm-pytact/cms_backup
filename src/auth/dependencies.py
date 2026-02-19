"""Authentication dependencies for FastAPI routes."""
from uuid import UUID
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas import AuthContext
from src.auth.utils import decode_token
from src.auth.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    InactiveUserError,
    InactiveRoleError,
)
from src.auth.repository import AuthRepository
from src.auth.constants import STATUS_ACTIVE
from src.exceptions import ForbiddenError

# OAuth2PasswordBearer for Swagger UI integration
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/v1/auth/token",
    auto_error=False,  # Don't auto-raise if token missing
)


async def get_auth_context_from_token(
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> AuthContext:
    """Extract authentication context from JWT token.
    
    This dependency validates the JWT token and extracts user context.
    Used for endpoints that require authentication.
    
    Args:
        token: JWT token from Authorization header
        session: Database session
        
    Returns:
        AuthContext with user_id, role_id, role, and permissions_json
        
    Raises:
        InvalidTokenError: If token is missing or invalid
        TokenExpiredError: If token has expired
        InactiveUserError: If user is not active
        InactiveRoleError: If user's role is not active
    """
    # CRITICAL: Check if token is provided
    if not token:
        raise InvalidTokenError()
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise TokenExpiredError()
    
    # Extract required claims
    user_id_str = payload.get("sub")
    role_id_str = payload.get("role_id")
    
    if not user_id_str or not role_id_str:
        raise InvalidTokenError()
    
    try:
        user_id = UUID(user_id_str)
        role_id = UUID(role_id_str)
    except (ValueError, TypeError):
        raise InvalidTokenError()
    
    # Get user from database
    repository = AuthRepository(session)
    user = await repository.get_user_by_id(user_id)
    
    if not user:
        raise InvalidTokenError()
    
    # Check user status
    if user.status != STATUS_ACTIVE:
        raise InactiveUserError()
    
    # Check role status (eager loaded)
    if not user.role or user.role.status != STATUS_ACTIVE:
        raise InactiveRoleError()
    
    # Build AuthContext
    return AuthContext(
        user_id=user_id,
        role_id=role_id,
        role=user.role.slug if user.role else None,
        permissions_json=user.role.permissions_json if user.role else None,
    )


async def get_current_user_model(
    ctx: AuthContext = Depends(get_auth_context_from_token),
    session: AsyncSession = Depends(get_session),
):
    """Get current user model from AuthContext.
    
    This dependency fetches the full User model when needed (e.g., for audit logs).
    Use AuthContext when possible to avoid database lookups.
    
    Args:
        ctx: AuthContext from JWT token
        session: Database session
        
    Returns:
        User model with role relationship loaded
    """
    repository = AuthRepository(session)
    user = await repository.get_user_by_id(ctx.user_id)
    
    if not user:
        raise InvalidTokenError()
    
    return user


def require_permission(module: str, action: str):
    """FastAPI dependency factory for permission checking.
    
    Checks if the user's role has the required permission by examining
    the role's permissions_json structure.
    
    Permission format: "module.resource" (e.g., "blogs.blog", "users.user")
    Action: Permission action (e.g., "read", "read_all", "create", "update", "delete")
    
    Permissions are checked in the structure:
        permissions_json["modules"][module_name][resource_name][action]
    
    All users must have explicit permission granted - no special privileges.
    
    Usage:
        @router.get("/users/{user_id}")
        async def get_user(
            user_id: UUID,
            ctx: AuthContext = Depends(require_permission("users.user", "read")),
        ):
            # User has permission, proceed with ctx
            pass
    
    Args:
        module: Permission module and resource (e.g., "blogs.blog", "users.user")
        action: Permission action (e.g., "read", "read_all", "create", "update")
    
    Returns:
        Dependency function that validates permission and returns AuthContext
        
    Raises:
        ForbiddenError: If user doesn't have the required permission
    """
    
    async def permission_checker(
        ctx: AuthContext = Depends(get_auth_context_from_token),
    ) -> AuthContext:
        """Check permission based on role's permissions_json.
        
        Checks if the role has the required permission by examining:
        Module permission: modules[module_name][resource_name][action]
        
        All users, regardless of role, must have explicit permission granted.
        """
        # Check if permissions_json is available
        if not ctx.permissions_json:
            raise ForbiddenError(
                message="Insufficient permissions",
                error_code="INSUFFICIENT_PERMISSIONS",
                details=[{"field": "permission", "issue": "No permissions found for role"}],
            )
        
        permissions_json = ctx.permissions_json
        
        # Parse module string (e.g., "blogs.blog" -> module_name="blogs", resource_name="blog")
        module_parts = module.split(".")
        module_name, resource_name = module_parts
        
        # Check module permission
        modules = permissions_json.get("modules", {})
        module_perms = modules.get(module_name, {})
        
        if not isinstance(module_perms, dict):
            raise ForbiddenError(
                message="Insufficient permissions",
                error_code="INSUFFICIENT_PERMISSIONS",
                details=[{"field": "permission", "issue": f"Permission denied: {module}.{action}"}],
            )
        
        resource_perms = module_perms.get(resource_name, {})
        
        if not isinstance(resource_perms, dict):
            raise ForbiddenError(
                message="Insufficient permissions",
                error_code="INSUFFICIENT_PERMISSIONS",
                details=[{"field": "permission", "issue": f"Permission denied: {module}.{action}"}],
            )
        
        # Check if the specific action is granted
        has_permission = resource_perms.get(action, False)
        
        if not has_permission:
            raise ForbiddenError(
                message="Insufficient permissions",
                error_code="INSUFFICIENT_PERMISSIONS",
                details=[{"field": "permission", "issue": f"Permission denied: {module}.{action}"}],
            )
        
        # Permission granted
        return ctx
    
    return permission_checker
