"""add full_name to users

Revision ID: 20250919_add_full_name_to_users
Revises: 1bcb4d924950
Create Date: 2025-09-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250919_add_full_name_to_users'
down_revision: Union[str, Sequence[str], None] = 'a73a07d2fba6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_columns = [c['name'] for c in inspector.get_columns('users')]
    if 'full_name' not in user_columns:
        op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_columns = [c['name'] for c in inspector.get_columns('users')]
    if 'full_name' in user_columns:
        op.drop_column('users', 'full_name')


