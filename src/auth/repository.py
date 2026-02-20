"""Authentication repository for database operations."""
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.models import User
from src.roles.models import Role


class AuthRepository:
    """Repository for authentication-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address.
        
        Args:
            email: User email address (case-insensitive)
            
        Returns:
            User model if found, None otherwise
        """
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.role))  # Eager load role relationship
            .where(
                User.email.ilike(email),  # Case-insensitive email match
                User.deleted_at.is_(None),  # Filter soft-deleted users
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            User model if found, None otherwise
        """
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.role))  # Eager load role relationship
            .where(
                User.id == user_id,
                User.deleted_at.is_(None),  # Filter soft-deleted users
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_invite_token(self, token: str) -> Optional[User]:
        """Get user by invitation token.
        
        Args:
            token: Invitation token
            
        Returns:
            User model if found, None otherwise
        """
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.role))  # Eager load role relationship
            .where(
                User.invite_token == token,
                User.deleted_at.is_(None),  # Filter soft-deleted users
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_reset_token(self, token: str) -> Optional[User]:
        """Get user by password reset token.
        
        Args:
            token: Password reset token
            
        Returns:
            User model if found, None otherwise
        """
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.role))  # Eager load role relationship
            .where(
                User.password_reset_token == token,
                User.deleted_at.is_(None),  # Filter soft-deleted users
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_reset_token_for_update(self, token: str) -> Optional[User]:
        """Get user by password reset token with row lock (FOR UPDATE).
        
        This method locks the row to prevent concurrent token reuse.
        
        Args:
            token: Password reset token
            
        Returns:
            User model if found, None otherwise
        """
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.role))  # Eager load role relationship
            .where(
                User.password_reset_token == token,
                User.deleted_at.is_(None),  # Filter soft-deleted users
            )
            .with_for_update()  # Lock row to prevent concurrent access
        )
        return result.scalar_one_or_none()
    
    async def invalidate_reset_token(self, user: User) -> None:
        """Atomically invalidate password reset token for a user.
        
        This ensures the token is cleared immediately, preventing reuse.
        
        Args:
            user: User model to invalidate token for
        """
        # Clear token fields immediately
        user.password_reset_token = None
        user.password_reset_token_expires_at = None
        # Flush to database immediately (before password update)
        self.session.add(user)
        await self.session.flush()
    
    async def update_user(self, user: User) -> User:
        """Update user in database.
        
        Args:
            user: User model with updated fields
            
        Returns:
            Updated User model
        """
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user
