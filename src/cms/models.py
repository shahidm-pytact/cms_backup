"""Blog CMS SQLAlchemy models."""
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import String, DateTime, func, Text, ARRAY, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Blog(Base):
    """Blog model representing blog posts with metadata and JSON content."""

    __tablename__ = "blogs"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    # Unique Identifier
    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # Metadata Fields
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    subtitle: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    author: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    author_img: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    reading_time: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    hero_quote: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    blog_image: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    meta_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    keywords: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        index=True,
    )

    # Content (JSONB)
    content: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {"sections": []},
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
        index=True,
    )

    # Soft Delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Table Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published')",
            name="ck_blogs_status"
        ),
    )
