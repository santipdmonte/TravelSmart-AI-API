"""Add: transportation

Revision ID: 7a30ca90c8ea
Revises: 
Create Date: 2025-07-26 17:47:06.636653

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a30ca90c8ea'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('itineraries', sa.Column('transportation_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_itineraries_transportation_id'), 'itineraries', ['transportation_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_itineraries_transportation_id'), table_name='itineraries')
    op.drop_column('itineraries', 'transportation_id')
    # ### end Alembic commands ###
