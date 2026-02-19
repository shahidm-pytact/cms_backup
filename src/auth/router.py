"""Authentication router with all auth endpoints."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Form, Header, HTTPException, Request, Response, status
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import StandardResponse, AuthContext
from src.database import get_session
from src.auth.dependencies import get_auth_context_from_token
from src.auth.service import AuthService
from src.auth.schemas import (
    LoginRequest,
    SetPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    LoginResponse,
    InvitationAcceptResponse,
    SetPasswordResponse,
    ResetPasswordResponse,
    UserContextResponse,
)
from src.auth.constants import (
    SUCCESS_TOKEN_GENERATED,
    SUCCESS_LOGIN,
    SUCCESS_LOGOUT,
    SUCCESS_INVITATION_ACCEPTED,
    SUCCESS_PASSWORD_SET,
    SUCCESS_PASSWORD_RESET_REQUESTED,
    SUCCESS_PASSWORD_RESET,
    SUCCESS_USER_CONTEXT_RETRIEVED,
)
from src.auth.exceptions import (
    InvalidRequestError,
    InvalidCredentialsError,
    InactiveUserError,
    InactiveRoleError,
)
from src.utils import set_etag_headers_and_return, set_request_id_header, set_304_response_headers
from src.auth.documentations.auth_api_doc import AuthApiDocs

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# API Dependency Class
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


# Endpoints

@router.post(
    "/token",
    status_code=status.HTTP_200_OK,
    summary=AuthApiDocs.token["summary"],
    description=AuthApiDocs.token["description"],
)
async def token(
    username: str = Form(...),  # OAuth2 uses 'username' but we treat it as email
    password: str = Form(...),
    session: AsyncSession = Depends(get_session),
    request: Request = None,
    response: Response = None,
) -> dict:
    """OAuth2-compatible token endpoint for Swagger UI authorization.
    
    This endpoint accepts form data (username/password) and returns OAuth2-compatible
    response format for Swagger UI integration. Returns plain dict (not StandardResponse)
    for OAuth2 compatibility.
    
    CRITICAL: This endpoint uses Form(...) parameters (not JSON) for OAuth2 compatibility.
    Requires python-multipart package to be installed.
    
    Following OAuth2 rules from auth_setup.md and error_prevention.md:
    - Accepts Form(...) parameters (username, password)
    - Returns OAuth2-compatible response (access_token, token_type, expires_in)
    - Handles all authentication errors with OAuth2-compatible format
    - Sets WWW-Authenticate header on errors
    - Sets X-Request-ID header on all responses
    """
    try:
        # Use service directly for authentication
        service = AuthService(session)
        user = await service.authenticate_user(username, password)
        tokens = await service.create_tokens(user)
        
        # Return OAuth2-compatible response (plain dict, not StandardResponse)
        # OAuth2 requires: access_token, token_type
        # OAuth2 optional: expires_in (recommended for better compliance)
        response_data = {
            "access_token": tokens["access_token"],
            "token_type": tokens["token_type"],
        }
        
        # Include expires_in if available (OAuth2 optional field, but recommended)
        if "expires_in" in tokens:
            response_data["expires_in"] = tokens["expires_in"]
        
        # Set X-Request-ID header explicitly (middleware also handles it, but this ensures it's set)
        set_request_id_header(request, response)
        
        return response_data
        
    except (InvalidCredentialsError, InactiveUserError, InactiveRoleError):
        # CRITICAL: Return OAuth2-compatible error for Swagger UI
        # Use generic message to avoid information leakage
        # All authentication errors return same message for security
        # HTTPException will be handled by http_exception_handler which sets X-Request-ID
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # CRITICAL: Catch any unexpected exceptions and return OAuth2-compatible error
        # This prevents exposing internal errors and maintains OAuth2 compliance
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/login",
    response_model=StandardResponse[LoginResponse],
    status_code=status.HTTP_200_OK,
    summary=AuthApiDocs.login["summary"],
    description=AuthApiDocs.login["description"],
)
async def login(
    login_data: LoginRequest,
    api: AuthApiDep = Depends(AuthApiDep),
    request: Request = None,
    response: Response = None,
) -> StandardResponse[LoginResponse]:
    """Authenticate user with email and password."""
    result = await api.login(login_data)
    return set_etag_headers_and_return(response, result, SUCCESS_LOGIN, request)


@router.post(
    "/logout",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary=AuthApiDocs.logout["summary"],
    description=AuthApiDocs.logout["description"],
)
async def logout(
    ctx: AuthContext = Depends(get_auth_context_from_token),
    api: AuthApiDep = Depends(AuthApiDep),
    request: Request = None,
    response: Response = None,
) -> StandardResponse[dict]:
    """Logout and invalidate user session/token."""
    # TODO: Implement token blacklist or JWT ID revocation if needed
    # For now, just return success (stateless JWT tokens)
    return set_etag_headers_and_return(response, None, SUCCESS_LOGOUT, request)


@router.post(
    "/invitations/{token}/accept",
    response_model=StandardResponse[InvitationAcceptResponse],
    status_code=status.HTTP_200_OK,
    summary=AuthApiDocs.accept_invitation["summary"],
    description=AuthApiDocs.accept_invitation["description"],
)
async def accept_invitation(
    token: str,
    api: AuthApiDep = Depends(AuthApiDep),
    request: Request = None,
    response: Response = None,
) -> StandardResponse[InvitationAcceptResponse]:
    """Accept invitation (validate token and mark invitation as accepted)."""
    result = await api.accept_invitation(token)
    return set_etag_headers_and_return(response, result, SUCCESS_INVITATION_ACCEPTED, request)


@router.post(
    "/invitations/{token}/set-password",
    response_model=StandardResponse[SetPasswordResponse],
    status_code=status.HTTP_200_OK,
    summary=AuthApiDocs.set_password["summary"],
    description=AuthApiDocs.set_password["description"],
)
async def set_password(
    token: str,
    password_data: SetPasswordRequest,
    api: AuthApiDep = Depends(AuthApiDep),
    request: Request = None,
    response: Response = None,
) -> StandardResponse[SetPasswordResponse]:
    """Set initial password after accepting invitation."""
    result = await api.set_password_from_invitation(token, password_data)
    return set_etag_headers_and_return(response, result, SUCCESS_PASSWORD_SET, request)


@router.post(
    "/reset-password",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary=AuthApiDocs.request_password_reset["summary"],
    description=AuthApiDocs.request_password_reset["description"],
)
async def request_password_reset(
    reset_data: ResetPasswordRequest,
    api: AuthApiDep = Depends(AuthApiDep),
    request: Request = None,
    response: Response = None,
) -> StandardResponse[dict]:
    """Request password reset (generates reset token and sends email)."""
    await api.request_password_reset(reset_data)
    return set_etag_headers_and_return(
        response, None, SUCCESS_PASSWORD_RESET_REQUESTED, request
    )


@router.post(
    "/reset-password/{token}",
    response_model=StandardResponse[ResetPasswordResponse],
    status_code=status.HTTP_200_OK,
    summary=AuthApiDocs.reset_password["summary"],
    description=AuthApiDocs.reset_password["description"],
)
async def reset_password(
    token: str,
    password_data: SetPasswordRequest,
    api: AuthApiDep = Depends(AuthApiDep),
    request: Request = None,
    response: Response = None,
) -> StandardResponse[ResetPasswordResponse]:
    """Reset user password using reset token."""
    result = await api.reset_password(token, password_data)
    return set_etag_headers_and_return(response, result, SUCCESS_PASSWORD_RESET, request)


@router.get(
    "/me",
    response_model=StandardResponse[UserContextResponse],
    status_code=status.HTTP_200_OK,
    summary=AuthApiDocs.get_me["summary"],
    description=AuthApiDocs.get_me["description"],
)
async def get_me(
    ctx: AuthContext = Depends(get_auth_context_from_token),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    api: AuthApiDep = Depends(AuthApiDep),
    request: Request = None,
    response: Response = None,
) -> StandardResponse[UserContextResponse] | FastAPIResponse:
    """Retrieve current user's details and context."""
    result = await api.get_user_context(ctx.user_id)
    
    # Handle conditional GET (304 Not Modified)
    if if_none_match and hasattr(result, "_etag") and if_none_match == result._etag:
        not_modified_response = FastAPIResponse(status_code=status.HTTP_304_NOT_MODIFIED)
        return set_304_response_headers(
            request, not_modified_response, result._etag, result._last_modified
        )
    
    return set_etag_headers_and_return(
        response, result, SUCCESS_USER_CONTEXT_RETRIEVED, request
    )
