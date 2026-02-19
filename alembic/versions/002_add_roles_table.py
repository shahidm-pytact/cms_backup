"""Add roles table

Revision ID: 002_add_roles
Revises: 001_add_blogs
Create Date: 2025-01-21 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_add_roles'
down_revision: Union[str, None] = '001_add_blogs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create roles table."""
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('role_type', sa.String(length=20), nullable=False, server_default='custom'),
        sa.Column('permissions_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('active', 'inactive')", name='ck_roles_status'),
        sa.CheckConstraint("role_type IN ('system', 'custom')", name='ck_roles_role_type')
    )
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    op.create_index(op.f('ix_roles_slug'), 'roles', ['slug'], unique=True)
    op.create_index(op.f('ix_roles_created_by'), 'roles', ['created_by'], unique=False)
    op.create_index(op.f('ix_roles_updated_by'), 'roles', ['updated_by'], unique=False)
    # Note: Foreign keys to users.id will be added in migration 005 after users table exists


def downgrade() -> None:
    """Drop roles table."""
    op.drop_index(op.f('ix_roles_updated_by'), table_name='roles')
    op.drop_index(op.f('ix_roles_created_by'), table_name='roles')
    op.drop_index(op.f('ix_roles_slug'), table_name='roles')
    op.drop_index(op.f('ix_roles_id'), table_name='roles')
    op.drop_table('roles')
