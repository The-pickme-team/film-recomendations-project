"""CORRECTING ERRORS

Revision ID: ea19d992409e
Revises: 7fc1378747b8
Create Date: 2026-05-07 14:57:19.258825

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ea19d992409e'
down_revision: str | Sequence[str] | None = '7fc1378747b8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table('files', 'films')
    op.execute(sa.text('ALTER TABLE films RENAME CONSTRAINT pk_files TO pk_films'))
    op.execute(
        sa.text(
            'ALTER TABLE vectors RENAME CONSTRAINT fk_vectors_file_id_files '
            'TO fk_vectors_file_id_films'
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text(
            'ALTER TABLE vectors RENAME CONSTRAINT fk_vectors_file_id_films '
            'TO fk_vectors_file_id_files'
        )
    )
    op.execute(sa.text('ALTER TABLE films RENAME CONSTRAINT pk_films TO pk_files'))
    op.rename_table('films', 'files')
