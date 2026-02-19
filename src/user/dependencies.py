"""User module dependencies."""
from typing import Optional
from uuid import UUID
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas import AuthContext
from src.user.service import UserService
from src.user.schemas import (
    UserInvite,
    UserUpdate,
    UserStatusUpdate,
    UserListQuery,
)


class UserApiDep:
    """API dependency for user operations."""
    
    def __init__(
        self,
        session: AsyncSession = Depends(get_session),
    ):
        self.service = UserService(session)
        self.session = session
    
    async def invite_user(
        self,
        data: UserInvite,
        ctx: AuthContext,
        request: Optional[Request] = None,
    ):
        """Invite a new user."""
        return await self.service.invite_user(data, ctx, request)
    
    async def get_user(
        self,
        user_id: str,
        ctx: AuthContext,
        if_none_match: str | None = None,
    ):
        """Get user by ID."""
        return await self.service.get_user(
            UUID(user_id),
            if_none_match,
        )
    
    async def list_users(
        self,
        query: UserListQuery,
        ctx: AuthContext,
        if_none_match: str | None = None,
    ):
        """List users with pagination."""
        return await self.service.list_users(
            query,
            if_none_match,
        )
    
    async def update_user(
        self,
        user_id: str,
        data: UserUpdate,
        ctx: AuthContext,
        if_match: str | None = None,
        request: Optional[Request] = None,
    ):
        """Update user."""
        return await self.service.update_user(
            UUID(user_id),
            data,
            ctx,
            if_match,
            request,
        )
    
    async def update_user_status(
        self,
        user_id: str,
        data: UserStatusUpdate,
        ctx: AuthContext,
        if_match: str | None = None,
        request: Optional[Request] = None,
    ):
        """Update user status."""
        return await self.service.update_user_status(
            UUID(user_id),
            data,
            ctx,
            if_match,
            request,
        )
    
    async def get_invitation_status(
        self,
        user_id: str,
    ):
        """Get invitation status."""
        return await self.service.get_invitation_status(UUID(user_id))
    
    async def resend_invite(
        self,
        user_id: str,
        ctx: AuthContext,
        request: Optional[Request] = None,
    ):
        """Resend invitation."""
        return await self.service.resend_invite(
            UUID(user_id),
            ctx,
            request,
        )
    
    async def request_password_reset(
        self,
        user_id: str,
        ctx: AuthContext,
        request: Optional[Request] = None,
    ):
        """Request password reset."""
        return await self.service.request_password_reset(UUID(user_id), ctx, request)
