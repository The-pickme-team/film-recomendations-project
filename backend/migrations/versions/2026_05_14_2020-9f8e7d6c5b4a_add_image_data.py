"""add image_data column to films

Revision ID: 9f8e7d6c5b4a
Revises: 0f1e2d3c4b5a
Create Date: 2026-05-14 20:20:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9f8e7d6c5b4a'
down_revision: str | Sequence[str] | None = '0f1e2d3c4b5a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add binary column for image storage
    op.add_column('films', sa.Column('image_data', sa.LargeBinary(), nullable=True))
    # Optionally drop legacy 'image' column if present
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns('films')]
    if 'image' in cols:
        op.drop_column('films', 'image')


def downgrade() -> None:
    """Downgrade schema."""
    # Restore previous 'image' text column and drop 'image_data'
    op.drop_column('films', 'image_data')
    op.add_column('films', sa.Column('image', sa.String(), nullable=True))
