"""revision

Revision ID: 7e92682ac511
Revises: 59f75046e387
Create Date: 2026-02-04 11:30:24.856162

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7e92682ac511'
down_revision: Union[str, Sequence[str], None] = '59f75046e387'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('request', sa.Column('solarized', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('request', 'solarized')
