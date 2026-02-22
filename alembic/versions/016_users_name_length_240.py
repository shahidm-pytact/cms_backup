"""Users name column length 255 -> 240

Revision ID: 016_users_name_240
Revises: 015_users_name_255
Create Date: 2026-02-22 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '016_users_name_240'
down_revision: Union[str, None] = '015_users_name_255'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change users.name from VARCHAR(255) to VARCHAR(240)."""
    op.alter_column(
        'users',
        'name',
        existing_type=sa.String(length=255),
        type_=sa.String(length=240),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Revert users.name from VARCHAR(240) to VARCHAR(255)."""
    op.alter_column(
        'users',
        'name',
        existing_type=sa.String(length=240),
        type_=sa.String(length=255),
        existing_nullable=False,
    )
