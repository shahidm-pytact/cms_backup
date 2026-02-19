"""Audit Log router for API endpoints."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, Response, Request, status
from fastapi.responses import Response as FastAPIResponse

from src.schemas import StandardResponse, AuthContext
from src.auth.dependencies import require_permission
from src.audit_logs.dependencies import AuditLogApiDep
from src.audit_logs.documentations.audit_logs_api_doc import AuditLogsApiDocs
from src.audit_logs.schemas import (
    AuditLogListQuery,
    AuditLogRead,
    AuditLogPaginatedResponse,
)
from src.audit_logs.constants import (
    SUCCESS_AUDIT_LOG_RETRIEVED,
    SUCCESS_AUDIT_LOGS_RETRIEVED,
)
from src.utils import set_etag_headers_and_return, set_request_id_header

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get(
    "",
    response_model=StandardResponse[AuditLogPaginatedResponse],
    status_code=status.HTTP_200_OK,
    summary=AuditLogsApiDocs.list["summary"],
    description=AuditLogsApiDocs.list["description"],
)
async def list_audit_logs(
    query: AuditLogListQuery = Depends(AuditLogListQuery),
    ctx: AuthContext = Depends(require_permission("audit_logs.audit_log", "read_all")),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    api: AuditLogApiDep = Depends(AuditLogApiDep),
    request: Request = None,
    response: Response = None,
) -> StandardResponse[AuditLogPaginatedResponse] | FastAPIResponse:
    """List audit logs with pagination, filtering, search, and sorting."""
    result = await api.list_audit_logs(query, ctx, if_none_match)
    
    # Handle 304 response
    if isinstance(result, FastAPIResponse):
        set_request_id_header(request, result)
        return result
    
    return set_etag_headers_and_return(response, result, SUCCESS_AUDIT_LOGS_RETRIEVED, request)


@router.get(
    "/{audit_log_id}",
    response_model=StandardResponse[AuditLogRead],
    status_code=status.HTTP_200_OK,
    summary=AuditLogsApiDocs.get["summary"],
    description=AuditLogsApiDocs.get["description"],
)
async def get_audit_log(
    audit_log_id: UUID,
    ctx: AuthContext = Depends(require_permission("audit_logs.audit_log", "read")),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    api: AuditLogApiDep = Depends(AuditLogApiDep),
    request: Request = None,
    response: Response = None,
) -> StandardResponse[AuditLogRead] | FastAPIResponse:
    """Get audit log details including old_values and new_values."""
    result = await api.get_audit_log_by_id(audit_log_id, ctx, if_none_match)
    
    # Handle 304 response
    if isinstance(result, FastAPIResponse):
        set_request_id_header(request, result)
        return result
    
    return set_etag_headers_and_return(response, result, SUCCESS_AUDIT_LOG_RETRIEVED, request)
