"""Role router for API endpoints."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, Response, Request, status
from fastapi.responses import Response as FastAPIResponse

from src.schemas import StandardResponse, AuthContext
from src.auth.dependencies import require_permission
from src.roles.dependencies import RoleApiDep
from src.roles.documentations.roles_api_doc import RoleApiDocs
from src.roles.schemas import (
    RoleCreate,
    RoleUpdate,
    RoleListQuery,
    RoleRead,
    RolePaginatedResponse,
)
from src.roles.constants import (
    SUCCESS_ROLE_CREATED,
    SUCCESS_ROLE_RETRIEVED,
    SUCCESS_ROLES_RETRIEVED,
    SUCCESS_ROLE_UPDATED,
)
from src.utils import set_etag_headers_and_return, set_request_id_header

router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


@router.get(
    "",
    response_model=StandardResponse[RolePaginatedResponse],
    status_code=status.HTTP_200_OK,
    summary=RoleApiDocs.list["summary"],
    description=RoleApiDocs.list["description"],
)
async def list_roles(
    query: RoleListQuery = Depends(RoleListQuery),
    ctx: AuthContext = Depends(require_permission("roles.role", "read_all")),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    api: RoleApiDep = Depends(RoleApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[RolePaginatedResponse] | FastAPIResponse:
    """List roles with pagination, filtering, search, and sorting."""
    result = await api.list_roles(query, ctx, if_none_match)
    
    # Handle 304 response
    if isinstance(result, FastAPIResponse):
        set_request_id_header(request, result)
        return result
    
    return set_etag_headers_and_return(response, result, SUCCESS_ROLES_RETRIEVED, request)


@router.post(
    "",
    response_model=StandardResponse[RoleRead],
    status_code=status.HTTP_201_CREATED,
    summary=RoleApiDocs.create["summary"],
    description=RoleApiDocs.create["description"],
)
async def create_role(
    data: RoleCreate,
    ctx: AuthContext = Depends(require_permission("roles.role", "create")),
    api: RoleApiDep = Depends(RoleApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[RoleRead]:
    """Create a new custom role with permissions assignment."""
    result = await api.create_role(data, ctx)
    
    return set_etag_headers_and_return(response, result, SUCCESS_ROLE_CREATED, request)


@router.get(
    "/{role_id}",
    response_model=StandardResponse[RoleRead],
    status_code=status.HTTP_200_OK,
    summary=RoleApiDocs.get["summary"],
    description=RoleApiDocs.get["description"],
)
async def get_role(
    role_id: UUID,
    ctx: AuthContext = Depends(require_permission("roles.role", "read")),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    api: RoleApiDep = Depends(RoleApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[RoleRead] | FastAPIResponse:
    """Get specific role details with permissions."""
    result = await api.get_role_by_id(str(role_id), ctx, if_none_match)
    
    # Handle 304 response
    if isinstance(result, FastAPIResponse):
        set_request_id_header(request, result)
        return result
    
    return set_etag_headers_and_return(response, result, SUCCESS_ROLE_RETRIEVED, request)


@router.patch(
    "/{role_id}",
    response_model=StandardResponse[RoleRead],
    status_code=status.HTTP_200_OK,
    summary=RoleApiDocs.update["summary"],
    description=RoleApiDocs.update["description"],
)
async def update_role(
    role_id: UUID,
    data: RoleUpdate,
    ctx: AuthContext = Depends(require_permission("roles.role", "update")),
    if_match: Optional[str] = Header(None, alias="If-Match"),
    api: RoleApiDep = Depends(RoleApiDep),
    request: Request = None,  # FastAPI injects Request automatically
    response: Response = None,  # FastAPI injects Response automatically
) -> StandardResponse[RoleRead]:
    """Update role information (name, permissions_json, status)."""
    result = await api.update_role(str(role_id), data, ctx, if_match)
    
    return set_etag_headers_and_return(response, result, SUCCESS_ROLE_UPDATED, request)
