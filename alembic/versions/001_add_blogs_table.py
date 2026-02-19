"""Add blogs table

Revision ID: 001_add_blogs
Revises: 
Create Date: 2025-01-21 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_add_blogs'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create blogs table."""
    op.create_table(
        'blogs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('subtitle', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=False),
        sa.Column('author_img', sa.String(length=500), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reading_time', sa.String(length=50), nullable=True),
        sa.Column('hero_quote', sa.Text(), nullable=True),
        sa.Column('blog_image', sa.String(length=500), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('draft', 'published')", name='ck_blogs_status')
    )
    op.create_index(op.f('ix_blogs_id'), 'blogs', ['id'], unique=False)
    op.create_index(op.f('ix_blogs_slug'), 'blogs', ['slug'], unique=True)
    op.create_index(op.f('ix_blogs_published_at'), 'blogs', ['published_at'], unique=False)
    op.create_index(op.f('ix_blogs_status'), 'blogs', ['status'], unique=False)
    op.create_index(op.f('ix_blogs_updated_at'), 'blogs', ['updated_at'], unique=False)
    op.create_index(op.f('ix_blogs_deleted_at'), 'blogs', ['deleted_at'], unique=False)


def downgrade() -> None:
    """Drop blogs table."""
    op.drop_index(op.f('ix_blogs_deleted_at'), table_name='blogs')
    op.drop_index(op.f('ix_blogs_updated_at'), table_name='blogs')
    op.drop_index(op.f('ix_blogs_status'), table_name='blogs')
    op.drop_index(op.f('ix_blogs_published_at'), table_name='blogs')
    op.drop_index(op.f('ix_blogs_slug'), table_name='blogs')
    op.drop_index(op.f('ix_blogs_id'), table_name='blogs')
    op.drop_table('blogs')
