"""Authentication router with all auth endpoints."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Form, Header, HTTPException, Request, Response, status
from fastapi.responses import Response as FastAPIResponse

from src.schemas import StandardResponse, AuthContext
from src.auth.dependencies import get_auth_context_from_token, AuthApiDep
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
    GoogleAuthRequest
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
from src.auth.google_auth import verify_google_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# Endpoints
@router.get("/test")
async def auth_test():
    """Deployment check: confirms latest backend is deployed. No auth required."""
    return {"status": "ok", "message": "auth deployed", "path": "/auth/test"}


@router.post("/google")
async def google_login(
    payload: GoogleAuthRequest,
    api: AuthApiDep = Depends(AuthApiDep),
    request: Request = None,  # FastAPI injects Request automatically
):
    """Authenticate user with Google token."""
    # Verify Google token
    idinfo = verify_google_token(payload.token)
    
    email = idinfo.get("email")
    google_id = idinfo.get("sub")
    
    if not email or not google_id:
        raise HTTPException(status_code=400, detail="Invalid Google token")
    
    # Restrict login to @pytact.com emails only
    if not email.endswith("@pytact.com"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only @pytact.com email addresses are allowed."
        )
    
    # Handle Google authentication (business logic in service)
    tokens = await api.google_login(email, google_id, request)
    
    return tokens

@router.post(
    "/token",
    status_code=status.HTTP_200_OK,
    summary=AuthApiDocs.token["summary"],
    description=AuthApiDocs.token["description"],
)
async def token(
    username: str = Form(...),  # OAuth2 uses 'username' but we treat it as email
    password: str = Form(...),
    api: AuthApiDep = Depends(AuthApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
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
    
    Note: All exception handling and logging is done in the service layer.
    Router only formats HTTP responses (OAuth2 compliance).
    """
    try:
        # Generate OAuth2 token (business logic and error handling in service)
        tokens = await api.generate_oauth2_token(username, password, request)
        
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
        # All exceptions are already logged in service layer
        # Router only formats HTTP response for OAuth2 compliance
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        # All exceptions are already logged in service layer
        # Router only formats HTTP response for OAuth2 compliance
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
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
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
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[dict]:
    """Logout and invalidate user session/token."""
    # TODO: Implement token blacklist or JWT ID revocation if needed
    # For now, just return success (stateless JWT tokens)
    
    # Handle logout (business logic in service)
    await api.logout(ctx.user_id, request)
    
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
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
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
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
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
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
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
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
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
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
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
