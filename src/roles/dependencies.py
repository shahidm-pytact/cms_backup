"""Role module dependencies."""
from uuid import UUID
from typing import Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas import AuthContext
from src.roles.service import RoleService
from src.roles.schemas import (
    RoleCreate,
    RoleUpdate,
    RoleListQuery,
)


class RoleApiDep:
    """API dependency for role operations."""
    
    def __init__(
        self,
        session: AsyncSession = Depends(get_session),
    ):
        self.service = RoleService(session)
        self.session = session
    
    async def create_role(
        self,
        data: RoleCreate,
        ctx: AuthContext,
    ):
        """Create a new role."""
        return await self.service.create_role(data, ctx)
    
    async def get_role_by_id(
        self,
        role_id: str,
        ctx: AuthContext,
        if_none_match: Optional[str] = None,
    ):
        """Get role by ID."""
        return await self.service.get_role_by_id(
            UUID(role_id),
            if_none_match,
        )
    
    async def list_roles(
        self,
        query: RoleListQuery,
        ctx: AuthContext,
        if_none_match: Optional[str] = None,
    ):
        """List roles with pagination."""
        return await self.service.list_roles(
            query,
            if_none_match,
        )
    
    async def update_role(
        self,
        role_id: str,
        data: RoleUpdate,
        ctx: AuthContext,
        if_match: Optional[str] = None,
    ):
        """Update role."""
        return await self.service.update_role(
            UUID(role_id),
            data,
            ctx,
            if_match,
        )
