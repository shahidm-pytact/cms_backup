"""Update role_type constraint to include superadmin and operator

Revision ID: 006_update_role_type
Revises: 005_add_roles_user_fks
Create Date: 2026-02-17 12:42:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006_update_role_type'
down_revision: Union[str, None] = '005_add_roles_user_fks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update role_type constraint to allow 'superadmin' and 'operator'."""
    # Drop the old constraint
    op.drop_constraint('ck_roles_role_type', 'roles', type_='check')
    # Create the new constraint with updated values
    op.create_check_constraint(
        'ck_roles_role_type',
        'roles',
        "role_type IN ('system', 'custom', 'superadmin', 'operator')"
    )


def downgrade() -> None:
    """Revert role_type constraint to original values."""
    # Drop the new constraint
    op.drop_constraint('ck_roles_role_type', 'roles', type_='check')
    # Restore the original constraint
    op.create_check_constraint(
        'ck_roles_role_type',
        'roles',
        "role_type IN ('system', 'custom')"
    )
