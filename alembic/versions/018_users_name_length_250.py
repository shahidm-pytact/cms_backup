"""Users name column length 255 -> 250

Revision ID: 018_users_name_250
Revises: 017_users_name_255
Create Date: 2026-02-22 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '018_users_name_250'
down_revision: Union[str, None] = '017_users_name_255'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change users.name from VARCHAR(255) to VARCHAR(250)."""
    op.alter_column(
        'users',
        'name',
        existing_type=sa.String(length=255),
        type_=sa.String(length=250),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Revert users.name from VARCHAR(250) to VARCHAR(255)."""
    op.alter_column(
        'users',
        'name',
        existing_type=sa.String(length=250),
        type_=sa.String(length=255),
        existing_nullable=False,
    )
