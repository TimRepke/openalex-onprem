"""revision

Revision ID: 96c6dfeb6d9d
Revises: 500ea7c3f0be
Create Date: 2026-02-03 20:03:12.766035

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '96c6dfeb6d9d'
down_revision: Union[str, Sequence[str], None] = '500ea7c3f0be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('api_key', 'dimensions_jwt')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('api_key', sa.Column('dimensions_jwt', sa.VARCHAR(), autoincrement=False, nullable=True))
