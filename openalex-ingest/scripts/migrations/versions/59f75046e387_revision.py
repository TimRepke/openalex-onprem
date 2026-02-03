"""revision

Revision ID: 59f75046e387
Revises: 96c6dfeb6d9d
Create Date: 2026-02-03 21:54:35.469397

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '59f75046e387'
down_revision: Union[str, Sequence[str], None] = '96c6dfeb6d9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('request', sa.Column('queue_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('request', 'queue_id')
