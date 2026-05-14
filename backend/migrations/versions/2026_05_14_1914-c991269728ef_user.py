"""user.

Revision ID: c991269728ef
Revises: 260a9e8a9741
Create Date: 2026-05-14 19:14:55.211141

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c991269728ef'
down_revision: Union[str, Sequence[str], None] = '260a9e8a9741'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # placeholder migration created to satisfy missing revision reference
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
