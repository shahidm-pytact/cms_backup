"""Role SQLAlchemy models."""
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import CheckConstraint

from src.database import Base


class Role(Base):
    """Role model representing access profiles with permissions."""

    __tablename__ = "roles"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    # Business Fields
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Status and Type
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
    )
    role_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="custom",
    )

    # Permissions
    permissions_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
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
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="role",
        primaryjoin="Role.id == User.role_id",
    )
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
    )
    updated_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[updated_by],
    )

    # Table Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_roles_status"
        ),
        CheckConstraint(
            "role_type IN ('superadmin', 'operator')",
            name="ck_roles_role_type"
        ),
    )
