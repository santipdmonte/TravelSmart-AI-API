"""Nueva columna visited_countries en users

Revision ID: 06ac05114ff3
Revises: 20250919_add_full_name_to_users
Create Date: 2025-09-22 10:52:51.598402
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import NoSuchTableError

# revision identifiers, used by Alembic.
revision: str = '06ac05114ff3'
down_revision: Union[str, Sequence[str], None] = '20250919_add_full_name_to_users'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = inspect(conn)

    # --- Agrega la nueva columna 'visited_countries' si no existe ---
    if not any(c['name'] == 'visited_countries' for c in inspector.get_columns('users')):
        op.add_column('users', sa.Column('visited_countries', sa.JSON(), nullable=True))

    # --- Elimina índices y tabla 'token_blocklist' si existen ---
    if 'token_blocklist' in inspector.get_table_names():
        try:
            existing_indexes = [i['name'] for i in inspector.get_indexes('token_blocklist')]
        except NoSuchTableError:
            existing_indexes = []

        indexes_to_drop = [
            'idx_blocklist_expires_at',
            'idx_blocklist_jti',
            'ix_token_blocklist_expires_at',
            'ix_token_blocklist_id',
            'ix_token_blocklist_jti',
        ]

        for idx in indexes_to_drop:
            if idx in existing_indexes:
                op.drop_index(idx, table_name='token_blocklist')

        op.drop_table('token_blocklist')
    else:
        print("⚠️ Tabla 'token_blocklist' no existe, se omite eliminación.")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'visited_countries')
    op.create_table(
        'token_blocklist',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('jti', sa.VARCHAR(length=255), nullable=False),
        sa.Column('token_type', sa.VARCHAR(length=20), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('revoked_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('reason', sa.TEXT(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('token_blocklist_user_id_fkey')),
        sa.PrimaryKeyConstraint('id', name=op.f('token_blocklist_pkey')),
    )
    op.create_index(op.f('ix_token_blocklist_jti'), 'token_blocklist', ['jti'], unique=True)
    op.create_index(op.f('ix_token_blocklist_id'), 'token_blocklist', ['id'], unique=False)
    op.create_index(op.f('ix_token_blocklist_expires_at'), 'token_blocklist', ['expires_at'], unique=False)
    op.create_index(op.f('idx_blocklist_jti'), 'token_blocklist', ['jti'], unique=False)
    op.create_index(op.f('idx_blocklist_expires_at'), 'token_blocklist', ['expires_at'], unique=False)
