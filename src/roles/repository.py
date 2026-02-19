"""Role repository for database operations."""
from typing import Optional
from uuid import UUID
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.roles.models import Role


class RoleRepository:
    """Repository for role-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, role_id: UUID) -> Optional[Role]:
        """Get role by ID.
        
        Args:
            role_id: Role UUID
            
        Returns:
            Role model if found, None otherwise
        """
        result = await self.session.execute(
            select(Role).where(
                Role.id == role_id,
                Role.deleted_at.is_(None),  # Filter soft-deleted roles
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_slug(self, slug: str) -> Optional[Role]:
        """Get role by slug (case-insensitive).
        
        Args:
            slug: Role slug (case-insensitive)
            
        Returns:
            Role model if found, None otherwise
        """
        result = await self.session.execute(
            select(Role).where(
                func.lower(Role.slug) == func.lower(slug),  # Case-insensitive slug match
                Role.deleted_at.is_(None),  # Filter soft-deleted roles
            )
        )
        return result.scalar_one_or_none()
    
    async def list_with_pagination(
        self,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        status: Optional[str] = None,
        role_type: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Role], int]:
        """List roles with pagination, filtering, search, and sorting.
        
        Args:
            page: Page number (≥ 1)
            page_size: Page size (1-100)
            search: Search by role name or slug (case-insensitive partial match)
            status: Filter by status (active, inactive)
            role_type: Filter by role type (system, custom)
            sort_by: Sort field (created_at, updated_at, name, slug, status)
            sort_order: Sort order (asc or desc)
            
        Returns:
            Tuple of (list of roles, total count)
        """
        # Build base query
        query = select(Role).where(
            Role.deleted_at.is_(None)  # Filter soft-deleted roles
        )
        
        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Role.name.ilike(search_pattern),
                    Role.slug.ilike(search_pattern),
                )
            )
        
        # Apply status filter
        if status:
            query = query.where(Role.status == status)
        
        # Apply role_type filter
        if role_type:
            query = query.where(Role.role_type == role_type)
        
        # Count total (before pagination)
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Apply sorting
        sort_column = getattr(Role, sort_by, Role.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.session.execute(query)
        roles = result.scalars().all()
        
        return list(roles), total
    
    async def create(self, role: Role) -> Role:
        """Create role in database.
        
        Args:
            role: Role model to create
            
        Returns:
            Created Role model
        """
        self.session.add(role)
        await self.session.flush()
        await self.session.refresh(role)
        return role
    
    async def update(self, role: Role) -> Role:
        """Update role in database.
        
        Args:
            role: Role model with updated fields
            
        Returns:
            Updated Role model
        """
        self.session.add(role)
        await self.session.flush()
        await self.session.refresh(role)
        return role
