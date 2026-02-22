"""Users email column length 250 -> 255

Revision ID: 008_users_email_255
Revises: 007_users_email_250
Create Date: 2026-02-21 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '008_users_email_255'
down_revision: Union[str, None] = '007_users_email_250'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change users.email from VARCHAR(250) to VARCHAR(255)."""
    op.alter_column(
        'users',
        'email',
        existing_type=sa.String(length=250),
        type_=sa.String(length=255),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Revert users.email from VARCHAR(255) to VARCHAR(250)."""
    op.alter_column(
        'users',
        'email',
        existing_type=sa.String(length=255),
        type_=sa.String(length=250),
        existing_nullable=False,
    )
