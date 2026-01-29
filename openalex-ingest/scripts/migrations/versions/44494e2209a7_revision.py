"""revision

Revision ID: 44494e2209a7
Revises:
Create Date: 2026-01-29 21:03:29.525016

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '44494e2209a7'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'queue',
        sa.Column('queue_id', sa.Integer(), nullable=False),
        sa.Column('doi', sa.String(), nullable=False),
        sa.Column('openalex_id', sa.String(), nullable=True),
        sa.Column('pubmed_id', sa.String(), nullable=True),
        sa.Column('s2_id', sa.String(), nullable=True),
        sa.Column('scopus_id', sa.String(), nullable=True),
        sa.Column('wos_id', sa.String(), nullable=True),
        sa.Column('dimensions_id', sa.String(), nullable=True),
        sa.Column('nacsos_id', sa.Uuid(), nullable=True),
        sa.Column('sources', postgresql.JSONB(none_as_null=True, astext_type=sa.Text()), nullable=True),
        sa.Column('on_conflict', sa.Enum('FORCE', 'DO_NOTHING', 'RETRY_ABSTRACT', 'RETRY_RAW', name='onconflict'), nullable=False),
        sa.Column('time_created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('queue_id', name=op.f('pk_queue')),
    )

    op.add_column('request', sa.Column('nacsos_id', sa.Uuid(), nullable=True))
    op.drop_index(op.f('ix_request_time_created'), table_name='request')
    op.create_index(op.f('ix_request_nacsos_id'), 'request', ['nacsos_id'], unique=False)


def downgrade() -> None:
    pass
