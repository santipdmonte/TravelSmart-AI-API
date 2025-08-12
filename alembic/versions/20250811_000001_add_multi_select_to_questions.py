"""add multi_select to questions

Revision ID: 20250811_000001
Revises: b60401dd36dc
Create Date: 2025-08-11 00:00:01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250811_000001'
down_revision: Union[str, Sequence[str], None] = 'b60401dd36dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add multi_select column with default false
    op.add_column('questions', sa.Column('multi_select', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    # Remove multi_select column
    op.drop_column('questions', 'multi_select')
