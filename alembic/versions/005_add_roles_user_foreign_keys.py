"""Add roles user foreign keys

Revision ID: 005_add_roles_user_fks
Revises: 004_add_audit_logs
Create Date: 2025-01-21 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_add_roles_user_fks'
down_revision: Union[str, None] = '004_add_audit_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add foreign key constraints to roles table for created_by and updated_by."""
    # Add foreign key constraint for created_by
    op.create_foreign_key(
        'fk_roles_created_by_users',
        'roles', 'users',
        ['created_by'], ['id'],
        ondelete='SET NULL', onupdate='CASCADE'
    )
    # Add foreign key constraint for updated_by
    op.create_foreign_key(
        'fk_roles_updated_by_users',
        'roles', 'users',
        ['updated_by'], ['id'],
        ondelete='SET NULL', onupdate='CASCADE'
    )


def downgrade() -> None:
    """Remove foreign key constraints from roles table."""
    op.drop_constraint('fk_roles_updated_by_users', 'roles', type_='foreignkey')
    op.drop_constraint('fk_roles_created_by_users', 'roles', type_='foreignkey')
