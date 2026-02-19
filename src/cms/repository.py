"""Blog repository for database operations."""
from typing import Optional
from uuid import UUID
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from src.cms.models import Blog


class BlogRepository:
    """Repository for blog-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, blog_id: UUID) -> Optional[Blog]:
        """Get blog by ID.
        
        Args:
            blog_id: Blog UUID
            
        Returns:
            Blog model if found, None otherwise
        """
        result = await self.session.execute(
            select(Blog).where(
                Blog.id == blog_id,
                Blog.deleted_at.is_(None),  # Filter soft-deleted blogs
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_slug(self, slug: str) -> Optional[Blog]:
        """Get blog by slug.
        
        Args:
            slug: Blog slug
            
        Returns:
            Blog model if found, None otherwise
        """
        result = await self.session.execute(
            select(Blog).where(
                Blog.slug == slug,
                Blog.deleted_at.is_(None),  # Filter soft-deleted blogs
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_slug_for_update(self, slug: str) -> Optional[Blog]:
        """Get blog by slug for update (checks uniqueness).
        
        Args:
            slug: Blog slug
            
        Returns:
            Blog model if found, None otherwise
        """
        result = await self.session.execute(
            select(Blog).where(
                Blog.slug == slug,
                Blog.deleted_at.is_(None),  # Filter soft-deleted blogs
            )
        )
        return result.scalar_one_or_none()
    
    async def list_with_pagination(
        self,
        page: int,
        limit: int,
        sort: str = "publishedDate",
        order: str = "desc",
        author: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[list[Blog], int]:
        """List blogs with pagination, filtering, search, and sorting.
        
        Args:
            page: Page number (≥ 1)
            limit: Page size (1-100)
            sort: Sort field (publishedDate, title, author, createdAt, updatedAt)
            order: Sort order (asc or desc)
            author: Filter by author name (case-insensitive partial match)
            search: Search in title, subtitle, or description (case-insensitive)
            
        Returns:
            Tuple of (list of blogs, total count)
        """
        # Build base query
        query = select(Blog).where(
            Blog.deleted_at.is_(None)  # Filter soft-deleted blogs
        )
        
        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Blog.title.ilike(search_pattern),
                    Blog.subtitle.ilike(search_pattern),
                    Blog.description.ilike(search_pattern),
                )
            )
        
        # Apply author filter
        if author:
            author_pattern = f"%{author}%"
            query = query.where(
                Blog.author.ilike(author_pattern)
            )
        
        # Count total (before pagination)
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Map API sort field names to model column names
        sort_field_map = {
            "publishedDate": Blog.published_at,
            "title": Blog.title,
            "author": Blog.author,
            "createdAt": Blog.created_at,
            "updatedAt": Blog.updated_at,
        }
        
        # Apply sorting
        sort_column = sort_field_map.get(sort, Blog.published_at)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc().nulls_last())
        else:
            query = query.order_by(sort_column.asc().nulls_last())
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        blogs = result.scalars().all()
        
        return list(blogs), total
    
    async def create(self, blog: Blog) -> Blog:
        """Create blog in database.
        
        Args:
            blog: Blog model to create
            
        Returns:
            Created Blog model
        """
        self.session.add(blog)
        await self.session.flush()
        await self.session.refresh(blog)
        return blog
    
    async def update(self, blog: Blog) -> Blog:
        """Update blog in database.
        
        Args:
            blog: Blog model with updated fields
            
        Returns:
            Updated Blog model
        """
        self.session.add(blog)
        await self.session.flush()
        await self.session.refresh(blog)
        return blog
    
    async def soft_delete(self, blog: Blog) -> None:
        """Soft delete blog by setting deleted_at timestamp.
        
        Args:
            blog: Blog model to soft delete
        """
        blog.deleted_at = datetime.now(timezone.utc)
        blog.updated_at = datetime.now(timezone.utc)
        self.session.add(blog)
        await self.session.flush()
