"""convert images array to image string

Revision ID: 0f1e2d3c4b5a
Revises: a1b2c3d4e5f6
Create Date: 2026-05-14 20:10:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0f1e2d3c4b5a'
down_revision: str | Sequence[str] | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # If an 'images' column exists, drop it and add 'image' column.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns('films')]
    if 'images' in cols:
        op.drop_column('films', 'images')

    op.add_column('films', sa.Column('image', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Restore 'images' array column and drop 'image'
    op.drop_column('films', 'image')
    op.add_column('films', sa.Column('images', sa.ARRAY(sa.String()), nullable=True))
