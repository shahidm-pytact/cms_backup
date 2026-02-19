"""User repository for database operations."""
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.models import User
from src.roles.models import Role


class UserRepository:
    """Repository for user-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID with eager loading of relationships.
        
        Args:
            user_id: User UUID
            
        Returns:
            User model if found, None otherwise
        """
        result = await self.session.execute(
            select(User)
            .options(
                selectinload(User.role),  # Eager load role
                selectinload(User.invited_by_user),  # Eager load invited_by_user
            )
            .where(
                User.id == user_id,
                User.deleted_at.is_(None),  # Filter soft-deleted users
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address (case-insensitive).
        
        Args:
            email: User email address (case-insensitive)
            
        Returns:
            User model if found, None otherwise
        """
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.role))  # Eager load role
            .where(
                User.email.ilike(email),  # Case-insensitive email match
                User.deleted_at.is_(None),  # Filter soft-deleted users
            )
        )
        return result.scalar_one_or_none()
    
    async def list_with_pagination(
        self,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        status: Optional[str] = None,
        role_id: Optional[UUID] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        user_id_filter: Optional[UUID] = None,  # For Operator: only their own user
    ) -> tuple[list[User], int]:
        """List users with pagination, filtering, search, and sorting.
        
        Args:
            page: Page number (≥ 1)
            page_size: Page size (1-100)
            search: Search by user email or name (case-insensitive partial match)
            status: Filter by user status
            role_id: Filter by role ID
            sort_by: Sort field (created_at, updated_at, email, name, status)
            sort_order: Sort order (asc or desc)
            user_id_filter: If provided, only return this user (for Operator role)
            
        Returns:
            Tuple of (list of users, total count)
        """
        # Build base query
        query = select(User).options(
            selectinload(User.role)  # Eager load role
        ).where(
            User.deleted_at.is_(None)  # Filter soft-deleted users
        )
        
        # Apply user_id filter (for Operator: only their own user)
        if user_id_filter:
            query = query.where(User.id == user_id_filter)
        
        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    User.email.ilike(search_pattern),
                    User.name.ilike(search_pattern),
                )
            )
        
        # Apply status filter
        if status:
            query = query.where(User.status == status)
        
        # Apply role_id filter
        if role_id:
            query = query.where(User.role_id == role_id)
        
        # Count total (before pagination)
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Apply sorting
        sort_column = getattr(User, sort_by, User.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.session.execute(query)
        users = result.scalars().all()
        
        return list(users), total
    
    async def create(self, user: User) -> User:
        """Create user in database.
        
        Args:
            user: User model to create
            
        Returns:
            Created User model
        """
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user, ["role"])  # Refresh with role relationship
        return user
    
    async def update(self, user: User) -> User:
        """Update user in database.
        
        Args:
            user: User model with updated fields
            
        Returns:
            Updated User model
        """
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user, ["role"])  # Refresh with role relationship
        return user
    
    async def get_role_by_id(self, role_id: UUID) -> Optional[Role]:
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
