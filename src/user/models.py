"""User SQLAlchemy models."""
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class User(Base):
    """User model representing authenticated system participants."""

    __tablename__ = "users"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    # Business Fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Foreign Keys
    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status and Lifecycle
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="invited",
    )

    # Authentication
    password: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Invitation Tokens
    invite_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    invite_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Password Reset Tokens
    password_reset_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    password_reset_token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Invitation Timeline
    invited_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    invited_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    invite_accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )
    updated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )

    # Soft Delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Relationships
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="users",
        foreign_keys=[role_id],
    )
    invited_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side=[id],
        foreign_keys=[invited_by],
        back_populates="invited_users",
    )
    invited_users: Mapped[list["User"]] = relationship(
        "User",
        foreign_keys=[invited_by],
        back_populates="invited_by_user",
    )
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side=[id],
        foreign_keys=[created_by],
        back_populates="created_users",
    )
    created_users: Mapped[list["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_by_user",
    )
    updated_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side=[id],
        foreign_keys=[updated_by],
        back_populates="updated_users",
    )
    updated_users: Mapped[list["User"]] = relationship(
        "User",
        foreign_keys=[updated_by],
        back_populates="updated_by_user",
    )

    # Audit Logs
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
    )

    # Table Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('invited', 'active', 'inactive', 'expired', 'cancelled')",
            name="ck_users_status"
        ),
    )
