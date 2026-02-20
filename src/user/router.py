"""User router for API endpoints."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, Response, Request, status
from fastapi.responses import Response as FastAPIResponse

from src.schemas import StandardResponse, AuthContext
from src.auth.dependencies import require_permission
from src.user.dependencies import UserApiDep
from src.user.documentations.user_api_doc import UserApiDocs
from src.user.schemas import (
    UserInvite,
    UserUpdate,
    UserStatusUpdate,
    UserListQuery,
    UserRead,
    UserPaginatedResponse,
    UserInviteResponse,
    InvitationStatusResponse,
    ResendInviteResponse,
    PasswordResetRequestResponse,
)
from src.user.constants import (
    SUCCESS_USER_INVITED,
    SUCCESS_USER_RETRIEVED,
    SUCCESS_USERS_RETRIEVED,
SUCCESS_USER_UPDATED,
SUCCESS_USER_STATUS_UPDATED,
SUCCESS_INVITATION_RESENT,
SUCCESS_PASSWORD_RESET_EMAIL_SENT,
SUCCESS_INVITATION_STATUS_RETRIEVED,
)
from src.utils import set_etag_headers_and_return, set_request_id_header

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "",
    response_model=StandardResponse[UserPaginatedResponse],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.list["summary"],
    description=UserApiDocs.list["description"],
)
async def list_users(
    query: UserListQuery = Depends(UserListQuery),
    ctx: AuthContext = Depends(require_permission("users.user", "read_all")),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    api: UserApiDep = Depends(UserApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[UserPaginatedResponse] | FastAPIResponse:
    """List users with pagination, filtering, search, and sorting."""
    result = await api.list_users(query, ctx, if_none_match)
    
    # Handle 304 response
    if isinstance(result, FastAPIResponse):
        set_request_id_header(request, result)
        return result
    
    return set_etag_headers_and_return(response, result, SUCCESS_USERS_RETRIEVED, request)


@router.post(
    "/invite",
    response_model=StandardResponse[UserInviteResponse],
    status_code=status.HTTP_201_CREATED,
    summary=UserApiDocs.invite["summary"],
    description=UserApiDocs.invite["description"],
)
async def invite_user(
    data: UserInvite,
    ctx: AuthContext = Depends(require_permission("users.user", "invite")),
    api: UserApiDep = Depends(UserApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[UserInviteResponse]:
    """Invite a new user with role assignment."""
    result = await api.invite_user(data, ctx, request)
    return set_etag_headers_and_return(response, result, SUCCESS_USER_INVITED, request)


@router.get(
    "/{user_id}",
    response_model=StandardResponse[UserRead],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.get["summary"],
    description=UserApiDocs.get["description"],
)
async def get_user(
    user_id: UUID,
    ctx: AuthContext = Depends(require_permission("users.user", "read")),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    api: UserApiDep = Depends(UserApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[UserRead] | FastAPIResponse:
    """Get user details with invitation status and role information."""
    result = await api.get_user(user_id, ctx, if_none_match)
    
    # Handle 304 response
    if isinstance(result, FastAPIResponse):
        set_request_id_header(request, result)
        return result
    
    return set_etag_headers_and_return(response, result, SUCCESS_USER_RETRIEVED, request)


@router.get(
    "/{user_id}/invitation-status",
    response_model=StandardResponse[InvitationStatusResponse],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.get_invitation_status["summary"],
    description=UserApiDocs.get_invitation_status["description"],
)
async def get_invitation_status(
    user_id: UUID,
    ctx: AuthContext = Depends(require_permission("users.user", "read")),
    api: UserApiDep = Depends(UserApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[InvitationStatusResponse]:
    """Get user invitation status including status, expiry date, and re-invite eligibility."""
    result = await api.get_invitation_status(str(user_id))
    return set_etag_headers_and_return(response, result, SUCCESS_INVITATION_STATUS_RETRIEVED, request)


@router.patch(
    "/{user_id}",
    response_model=StandardResponse[UserRead],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.update["summary"],
    description=UserApiDocs.update["description"],
)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    ctx: AuthContext = Depends(require_permission("users.user", "update")),
    if_match: Optional[str] = Header(None, alias="If-Match"),
    api: UserApiDep = Depends(UserApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[UserRead]:
    """Update user information (name, email, role_id)."""
    result = await api.update_user(str(user_id), data, ctx, if_match, request)
    return set_etag_headers_and_return(response, result, SUCCESS_USER_UPDATED, request)


@router.patch(
    "/{user_id}/status",
    response_model=StandardResponse[UserRead],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.update_status["summary"],
    description=UserApiDocs.update_status["description"],
)
async def update_user_status(
    user_id: UUID,
    data: UserStatusUpdate,
    ctx: AuthContext = Depends(require_permission("users.user", "update")),
    if_match: Optional[str] = Header(None, alias="If-Match"),
    api: UserApiDep = Depends(UserApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[UserRead]:
    """Update user status (activate or deactivate)."""
    result = await api.update_user_status(str(user_id), data, ctx, if_match, request)
    return set_etag_headers_and_return(response, result, SUCCESS_USER_STATUS_UPDATED, request)


@router.post(
    "/{user_id}/resend-invite",
    response_model=StandardResponse[ResendInviteResponse],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.resend_invite["summary"],
    description=UserApiDocs.resend_invite["description"],
)
async def resend_invite(
    user_id: UUID,
    ctx: AuthContext = Depends(require_permission("users.user", "invite")),
    api: UserApiDep = Depends(UserApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[ResendInviteResponse]:
    """Resend invitation to user with new token."""
    result = await api.resend_invite(str(user_id), ctx, request)
    return set_etag_headers_and_return(response, result, SUCCESS_INVITATION_RESENT, request)


@router.post(
    "/{user_id}/request-password-reset",
    response_model=StandardResponse[PasswordResetRequestResponse],
    status_code=status.HTTP_200_OK,
    summary=UserApiDocs.request_password_reset["summary"],
    description=UserApiDocs.request_password_reset["description"],
)
async def request_password_reset(
    user_id: UUID,
    ctx: AuthContext = Depends(require_permission("users.user", "update")),
    api: UserApiDep = Depends(UserApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[PasswordResetRequestResponse]:
    """Request password reset for a user (generates reset token and sends email)."""
    result = await api.request_password_reset(str(user_id), ctx, request)
    return set_etag_headers_and_return(response, result, SUCCESS_PASSWORD_RESET_EMAIL_SENT, request)
