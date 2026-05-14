"""add images to films

Revision ID: a1b2c3d4e5f6
Revises: c991269728ef
Create Date: 2026-05-14 20:01:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: str | Sequence[str] | None = 'c991269728ef'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add images column to films as text array (nullable)
    op.add_column(
        'films',
        sa.Column('images', sa.ARRAY(sa.String()), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('films', 'images')
