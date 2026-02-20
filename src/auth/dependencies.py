"""Authentication dependencies for FastAPI routes."""
from uuid import UUID
from typing import Optional, Callable, Awaitable
from fastapi import Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas import AuthContext
from src.auth.utils import decode_token
from src.auth.service import AuthService
from src.auth.schemas import (
    LoginRequest,
    SetPasswordRequest,
    ResetPasswordRequest,
    LoginResponse,
    InvitationAcceptResponse,
    SetPasswordResponse,
    ResetPasswordResponse,
    UserContextResponse,
)
from src.auth.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    InactiveUserError,
    InactiveRoleError,
)
from src.auth.repository import AuthRepository
from src.auth.constants import STATUS_ACTIVE
from src.exceptions import ForbiddenError
from src.config import settings

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


def require_permission(module: str, action: str) -> Callable[..., Awaitable[AuthContext]]:
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


async def optional_auth_with_next_secret(
    verification_secret: Optional[str] = Query(None, alias="verification_secret"),
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> Optional[AuthContext]:
    """Optional authentication that allows access with verification_secret.
    
    If verification_secret query parameter is provided and matches the configured secret,
    returns None (no authentication context needed).
    Otherwise, requires valid JWT token and returns AuthContext.
    
    Args:
        verification_secret: Secret from verification_secret query parameter
        token: JWT token from Authorization header
        session: Database session
        
    Returns:
        AuthContext if JWT token is valid, None if secret is valid
        
    Raises:
        InvalidTokenError: If token is invalid and no valid secret is provided
        TokenExpiredError: If token has expired
        InactiveUserError: If user is not active
        InactiveRoleError: If user's role is not active
    """
    # Check if either secret is provided and valid
    secret_to_check = verification_secret
    if secret_to_check and secret_to_check == settings.next_api_secret:
        return None
    
    # If no valid secret, require JWT token
    return await get_auth_context_from_token(token, session)


def require_permission_or_next_secret(module: str, action: str) -> Callable[..., Awaitable[Optional[AuthContext]]]:
    """Permission dependency that allows access with verification_secret.
    
    If verification_secret query parameter is provided and matches the configured secret,
    allows access without permission checking.
    Otherwise, requires valid JWT token and checks permissions.
    
    Args:
        module: Permission module and resource (e.g., "blogs.blog", "users.user")
        action: Permission action (e.g., "read", "read_all", "create", "update")
    
    Returns:
        Dependency function that validates permission or verification_secret
    """
    
    async def permission_or_secret_checker(
        ctx: Optional[AuthContext] = Depends(optional_auth_with_next_secret),
    ) -> Optional[AuthContext]:
        """Check permission or allow access with verification_secret.
        
        If ctx is None, it means verification_secret was valid, so allow access.
        Otherwise, check permissions normally.
        """
        # If ctx is None, verification_secret was valid, allow access
        if ctx is None:
            return ctx
        
        # Check permissions normally
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
        
        # Check if specific action is granted
        has_permission = resource_perms.get(action, False)
        
        if not has_permission:
            raise ForbiddenError(
                message="Insufficient permissions",
                error_code="INSUFFICIENT_PERMISSIONS",
                details=[{"field": "permission", "issue": f"Permission denied: {module}.{action}"}],
            )
        
        # Permission granted
        return ctx
    
    return permission_or_secret_checker


class AuthApiDep:
    """API dependency for auth operations."""
    
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.service = AuthService(session)
        self.session = session
    
    async def login(self, login_data: LoginRequest) -> LoginResponse:
        """Login user."""
        return await self.service.login(login_data)
    
    async def accept_invitation(self, token: str) -> InvitationAcceptResponse:
        """Accept invitation."""
        return await self.service.accept_invitation(token)
    
    async def set_password_from_invitation(
        self, token: str, password_data: SetPasswordRequest
    ) -> SetPasswordResponse:
        """Set password from invitation."""
        return await self.service.set_password_from_invitation(token, password_data)
    
    async def request_password_reset(self, reset_data: ResetPasswordRequest) -> None:
        """Request password reset."""
        return await self.service.request_password_reset(reset_data)
    
    async def reset_password(
        self, token: str, password_data: SetPasswordRequest
    ) -> ResetPasswordResponse:
        """Reset password."""
        return await self.service.reset_password(token, password_data)
    
    async def get_user_context(self, user_id: UUID) -> UserContextResponse:
        """Get user context."""
        return await self.service.get_user_context(user_id)
    
    async def google_login(
        self,
        email: str,
        google_id: str,
        request: Optional[Request] = None,
    ) -> dict:
        """Handle Google authentication."""
        return await self.service.google_login(email, google_id, request)
    
    async def generate_oauth2_token(
        self,
        username: str,
        password: str,
        request: Optional[Request] = None,
    ) -> dict:
        """Generate OAuth2-compatible token."""
        return await self.service.generate_oauth2_token(username, password, request)
    
    async def logout(
        self,
        user_id: UUID,
        request: Optional[Request] = None,
    ) -> None:
        """Handle user logout."""
        return await self.service.logout(user_id, request)