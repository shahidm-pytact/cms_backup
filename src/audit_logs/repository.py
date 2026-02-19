"""Audit Log repository for database operations."""
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_logs.models import AuditLog


class AuditLogRepository:
    """Repository for audit log-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, audit_log_id: UUID) -> Optional[AuditLog]:
        """Get audit log by ID with eager loading of relationships.
        
        Args:
            audit_log_id: Audit log UUID
            
        Returns:
            AuditLog model if found, None otherwise
        """
        result = await self.session.execute(
            select(AuditLog)
            .options(
                selectinload(AuditLog.user),  # Eager load user relationship
            )
            .where(
                AuditLog.id == audit_log_id,
                # Note: audit_logs table does NOT have deleted_at (immutable audit trail)
            )
        )
        return result.scalar_one_or_none()
    
    async def list_with_pagination(
        self,
        page: int,
        page_size: int,
        user_id: Optional[UUID] = None,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[AuditLog], int]:
        """List audit logs with pagination, filtering, and sorting.
        
        Args:
            page: Page number (≥ 1)
            page_size: Page size (1-100)
            user_id: Filter by user ID (actor who performed the action)
            entity_type: Filter by entity type (e.g., 'user', 'role')
            action: Filter by action (e.g., 'create', 'update', 'delete')
            date_from: Filter from date (inclusive, UTC datetime)
            date_to: Filter to date (inclusive, UTC datetime)
            sort_by: Sort field (created_at, user_id, entity_type, action)
            sort_order: Sort order (asc or desc)
            
        Returns:
            Tuple of (list of audit logs, total count)
        """
        # Build base query
        query = select(AuditLog).options(
            selectinload(AuditLog.user),  # Eager load user relationship
        )
        # Note: audit_logs table does NOT have deleted_at (immutable audit trail)
        
        # Apply user_id filter
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        
        # Apply entity_type filter
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        
        # Apply action filter
        if action:
            query = query.where(AuditLog.action == action)
        
        # Apply date range filter (inclusive boundaries)
        date_filters = []
        if date_from:
            date_filters.append(AuditLog.created_at >= date_from)
        if date_to:
            date_filters.append(AuditLog.created_at <= date_to)
        if date_filters:
            query = query.where(and_(*date_filters))
        
        # Count total (before pagination)
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Apply sorting
        sort_column = getattr(AuditLog, sort_by, AuditLog.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.session.execute(query)
        audit_logs = result.scalars().all()
        
        return list(audit_logs), total
