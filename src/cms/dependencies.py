"""Blog CMS module dependencies."""
from typing import Optional
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas import AuthContext
from src.cms.service import BlogService
from src.cms.schemas import (
    BlogCreate,
    BlogUpdate,
    BlogListQuery,
)


class BlogApiDep:
    """API dependency for blog operations."""
    
    def __init__(
        self,
        session: AsyncSession = Depends(get_session),
    ):
        self.service = BlogService(session)
        self.session = session
    
    async def create_blog(
        self,
        data: BlogCreate,
        ctx: AuthContext,
        request: Optional[Request] = None,
    ):
        """Create a new blog."""
        return await self.service.create_blog(data, ctx, request)
    
    async def get_blog_by_slug(
        self,
        slug: str,
        ctx: AuthContext,
        if_none_match: Optional[str] = None,
    ):
        """Get blog by slug."""
        return await self.service.get_blog_by_slug(
            slug,
            if_none_match,
        )
    
    async def list_blogs(
        self,
        query: BlogListQuery,
        ctx: AuthContext,
        if_none_match: Optional[str] = None,
    ):
        """List blogs with pagination."""
        return await self.service.list_blogs(
            query,
            if_none_match,
        )
    
    async def update_blog(
        self,
        slug: str,
        data: BlogUpdate,
        ctx: AuthContext,
        request: Optional[Request] = None,
    ):
        """Update blog (full update)."""
        return await self.service.update_blog(
            slug,
            data,
            ctx,
            request,
        )
    
    async def delete_blog(
        self,
        slug: str,
        ctx: AuthContext,
        request: Optional[Request] = None,
    ):
        """Delete blog."""
        return await self.service.delete_blog(slug, ctx, request)
