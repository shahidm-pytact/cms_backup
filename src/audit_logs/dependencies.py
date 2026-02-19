"""Audit Log module dependencies."""
from typing import Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas import AuthContext
from src.audit_logs.service import AuditLogService
from src.audit_logs.schemas import AuditLogListQuery


class AuditLogApiDep:
    """API dependency for audit log operations."""
    
    def __init__(
        self,
        session: AsyncSession = Depends(get_session),
    ):
        self.service = AuditLogService(session)
        self.session = session
    
    async def get_audit_log_by_id(
        self,
        audit_log_id: UUID,
        ctx: AuthContext,
        if_none_match: Optional[str] = None,
    ):
        """Get audit log by ID.
        
        Permission validation already done in router via require_permission("audit_logs.audit_log", "read").
        Only SuperAdmin can access audit logs.
        """
        return await self.service.get_audit_log_by_id(
            audit_log_id,
            if_none_match,
        )
    
    async def list_audit_logs(
        self,
        query: AuditLogListQuery,
        ctx: AuthContext,
        if_none_match: Optional[str] = None,
    ):
        """List audit logs with pagination.
        
        Permission validation already done in router via require_permission("audit_logs.audit_log", "read_all").
        Only SuperAdmin can access audit logs.
        """
        return await self.service.list_audit_logs(
            query,
            if_none_match,
        )
