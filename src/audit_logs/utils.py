"""Audit log utility functions."""
from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_logs.models import AuditLog


async def create_audit_log(
    session: AsyncSession,
    user_id: Optional[UUID],
    action: str,
    entity_type: str,
    entity_id: UUID,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    """Create an audit log entry.
    
    Args:
        session: Database session
        user_id: ID of the user performing the action (actor)
        action: Action type (e.g., 'create', 'update', 'delete', 'invite')
        entity_type: Type of entity (e.g., 'user', 'role', 'blog')
        entity_id: ID of the affected entity
        old_values: Previous state (for updates)
        new_values: New state (for creates/updates)
        description: Human-readable description
        request: FastAPI Request object (for IP/user agent)
        
    Returns:
        Created AuditLog instance
    """
    # Extract IP address and user agent from request
    ip_address = None
    user_agent = None
    
    if request:
        # Get IP address (handle proxies)
        ip_address = request.client.host if request.client else None
        # Check for X-Forwarded-For header (if behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        
        # Get user agent
        user_agent = request.headers.get("user-agent")
    
    # Create audit log
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent,
        description=description,
    )
    
    # Add to session (will be committed with the main transaction)
    session.add(audit_log)
    await session.flush()  # Flush to get ID, but don't commit yet
    
    return audit_log


def mask_sensitive_value(value: Optional[str]) -> Optional[str]:
    """Mask sensitive values in audit logs (e.g., tokens).
    
    Args:
        value: Value to mask
        
    Returns:
        Masked value (e.g., "***masked***") or None
    """
    if value is None:
        return None
    return "***masked***"
