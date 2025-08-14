"""add traveler_type_id to users

Revision ID: 20250814_000003_add_traveler_type_to_user
Revises: 20250812_add_change_log
Create Date: 2025-08-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20250814_000003_add_traveler_type_to_user'
down_revision: Union[str, Sequence[str], None] = '20250812_add_change_log'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add nullable traveler_type_id column to users
    op.add_column('users', sa.Column('traveler_type_id', postgresql.UUID(as_uuid=True), nullable=True))
    # Create index for faster lookups
    op.create_index(op.f('ix_users_traveler_type_id'), 'users', ['traveler_type_id'], unique=False)
    # Add FK with ON DELETE SET NULL so removing a traveler type doesn't delete users
    op.create_foreign_key(
        'fk_users_traveler_type_id',
        source_table='users',
        referent_table='traveler_types',
        local_cols=['traveler_type_id'],
        remote_cols=['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop FK, index and column in reverse order
    op.drop_constraint('fk_users_traveler_type_id', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_traveler_type_id'), table_name='users')
    op.drop_column('users', 'traveler_type_id')
