"""revision

Revision ID: 500ea7c3f0be
Revises: 44494e2209a7
Create Date: 2026-02-03 20:01:15.250501

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '500ea7c3f0be'
down_revision: Union[str, Sequence[str], None] = '44494e2209a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('api_key', sa.Column('api_feedback', postgresql.JSONB(none_as_null=True, astext_type=sa.Text()), nullable=True))
    op.drop_column('api_key', 'scopus_requests_limit')
    op.drop_column('api_key', 'scopus_requests_remaining')
    op.drop_column('api_key', 'scopus_requests_reset')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('api_key', sa.Column('scopus_requests_reset', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('api_key', sa.Column('scopus_requests_remaining', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('api_key', sa.Column('scopus_requests_limit', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('api_key', 'api_feedback')
