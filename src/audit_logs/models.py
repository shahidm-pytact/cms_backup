"""Audit Log SQLAlchemy models."""
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Text, JSON, Index, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class AuditLog(Base):
    """Audit Log model representing immutable audit trail for administrative actions."""

    __tablename__ = "audit_logs"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    # Actor
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )

    # Action Details
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )

    # State Changes
    old_values: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    new_values: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Timestamp (Immutable)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Description
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs",
    )

    # Composite Index for Traceability
    __table_args__ = (
        # Composite index for entity traceability queries
        Index("idx_audit_logs_entity", "entity_type", "entity_id"),
        # User activity queries (partial index)
        Index("idx_audit_logs_user_created", "user_id", "created_at", postgresql_where=text("user_id IS NOT NULL")),
        # Entity action queries
        Index("idx_audit_logs_entity_action", "entity_type", "action"),
        # Default sort for audit log listing
        Index("idx_audit_logs_created_at_desc", "created_at"),
    )
