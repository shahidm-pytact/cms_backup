"""Audit Log service for business logic."""
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from fastapi import status
from fastapi.responses import Response as FastAPIResponse

from src.audit_logs.repository import AuditLogRepository
from src.audit_logs.schemas import (
    AuditLogListQuery,
    AuditLogRead,
    AuditLogListItem,
    AuditLogPaginatedResponse,
)
from src.audit_logs.exceptions import AuditLogNotFound
from src.audit_logs.constants import ERROR_INVALID_DATE_FORMAT
from src.exceptions import ValidationError
from src.utils import generate_etag


class AuditLogService:
    """Service for audit log-related business logic."""
    
    def __init__(self, session):
        self.repository = AuditLogRepository(session)
        self.session = session
    
    def _parse_iso8601_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO 8601 date string to datetime object.
        
        Args:
            date_str: ISO 8601 date string (e.g., '2024-01-01T00:00:00Z')
            
        Returns:
            datetime object in UTC timezone, or None if date_str is None
            
        Raises:
            ValidationError: If date format is invalid
        """
        if date_str is None:
            return None
        
        try:
            # Handle 'Z' suffix (UTC timezone)
            if date_str.endswith('Z'):
                date_str = date_str[:-1] + '+00:00'
            
            # Parse ISO 8601 format
            dt = datetime.fromisoformat(date_str)
            
            # Ensure timezone-aware (UTC)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            
            return dt
        except (ValueError, TypeError) as e:
            raise ValidationError(
                message=ERROR_INVALID_DATE_FORMAT,
                error_code="VALIDATION_ERROR",
                details=[{"field": "date", "issue": ERROR_INVALID_DATE_FORMAT}],
            )
    
    async def get_audit_log_by_id(
        self,
        audit_log_id: UUID,
        if_none_match: Optional[str] = None,
    ) -> AuditLogRead | FastAPIResponse:
        """Get audit log by ID with ETag support.
        
        Args:
            audit_log_id: Audit log UUID
            if_none_match: ETag from If-None-Match header
            
        Returns:
            AuditLogRead with audit log details, or FastAPIResponse (304) if unchanged
            
        Raises:
            AuditLogNotFound: If audit log not found
        """
        # Get audit log from repository
        audit_log = await self.repository.get_by_id(audit_log_id)
        if not audit_log:
            raise AuditLogNotFound(str(audit_log_id))
        
        # Generate ETag from created_at (audit logs are immutable, so ETag is based on creation time)
        etag = generate_etag(audit_log.created_at)
        
        # Check If-None-Match header
        if if_none_match and if_none_match == etag:
            response = FastAPIResponse(status_code=status.HTTP_304_NOT_MODIFIED)
            response.headers["ETag"] = etag
            response.headers["Last-Modified"] = audit_log.created_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
            return response
        
        # Build response
        result = AuditLogRead.model_validate(audit_log)
        result._etag = etag
        result._last_modified = audit_log.created_at
        return result
    
    async def list_audit_logs(
        self,
        query: AuditLogListQuery,
        if_none_match: Optional[str] = None,
    ) -> AuditLogPaginatedResponse | FastAPIResponse:
        """List audit logs with pagination, filtering, and sorting.
        
        Permission validation already done in router via require_permission("audit_logs.audit_log", "read_all").
        Only SuperAdmin can access audit logs.
        
        Args:
            query: Query parameters for filtering and pagination
            if_none_match: ETag from If-None-Match header
            
        Returns:
            AuditLogPaginatedResponse with audit logs list, or FastAPIResponse (304) if unchanged
        """
        # Parse date filters
        date_from = self._parse_iso8601_date(query.date_from)
        date_to = self._parse_iso8601_date(query.date_to)
        
        # Get audit logs from repository
        audit_logs, total = await self.repository.list_with_pagination(
            page=query.page,
            page_size=query.page_size,
            user_id=query.user_id,
            entity_type=query.entity_type,
            action=query.action,
            date_from=date_from,
            date_to=date_to,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        )
        
        # Generate collection ETag from latest audit log created_at
        latest_created_at = None
        if audit_logs:
            latest_created_at = max(audit_log.created_at for audit_log in audit_logs)
            etag = generate_etag(latest_created_at)
            
            # Check If-None-Match header
            if if_none_match and if_none_match == etag:
                response = FastAPIResponse(status_code=status.HTTP_304_NOT_MODIFIED)
                response.headers["ETag"] = etag
                if latest_created_at:
                    response.headers["Last-Modified"] = latest_created_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
                return response
        else:
            etag = None
        
        # Build response items
        items = [AuditLogListItem.model_validate(audit_log) for audit_log in audit_logs]
        
        # Calculate pagination metadata
        total_pages = (total + query.page_size - 1) // query.page_size if total > 0 else 0
        
        # Build next_page URL with all query parameters
        next_page = None
        if query.page < total_pages:
            next_page = f"/v1/audit-logs?page={query.page + 1}&page_size={query.page_size}&sort_by={query.sort_by}&sort_order={query.sort_order}"
            if query.user_id:
                next_page += f"&user_id={query.user_id}"
            if query.entity_type:
                next_page += f"&entity_type={query.entity_type}"
            if query.action:
                next_page += f"&action={query.action}"
            if query.date_from:
                next_page += f"&date_from={query.date_from}"
            if query.date_to:
                next_page += f"&date_to={query.date_to}"
        
        # Build prev_page URL with all query parameters
        prev_page = None
        if query.page > 1:
            prev_page = f"/v1/audit-logs?page={query.page - 1}&page_size={query.page_size}&sort_by={query.sort_by}&sort_order={query.sort_order}"
            if query.user_id:
                prev_page += f"&user_id={query.user_id}"
            if query.entity_type:
                prev_page += f"&entity_type={query.entity_type}"
            if query.action:
                prev_page += f"&action={query.action}"
            if query.date_from:
                prev_page += f"&date_from={query.date_from}"
            if query.date_to:
                prev_page += f"&date_to={query.date_to}"
        
        # Build response
        result = AuditLogPaginatedResponse(
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
            if latest_created_at:
                result._last_modified = latest_created_at
        
        return result
