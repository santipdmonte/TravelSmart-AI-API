"""add username to DB

Revision ID: cec3d8961b5e
Revises: e8e035f66129
Create Date: 2025-09-22 12:22:43.358954
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'cec3d8961b5e'
down_revision: Union[str, Sequence[str], None] = 'e8e035f66129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # 🔧 Intentamos borrar índices sólo si existen
    indexes_to_drop = [
        'idx_blocklist_expires_at',
        'idx_blocklist_jti',
        'ix_token_blocklist_expires_at',
        'ix_token_blocklist_id',
        'ix_token_blocklist_jti',
    ]

    for idx in indexes_to_drop:
        try:
            conn.execute(text(f"DROP INDEX IF EXISTS {idx}"))
        except Exception as e:
            print(f"⚠️  No se pudo eliminar el índice {idx}: {e}")

    # 🔧 Intentamos borrar la tabla sólo si existe
    try:
        conn.execute(text("DROP TABLE IF EXISTS token_blocklist CASCADE"))
    except Exception as e:
        print(f"⚠️  No se pudo eliminar la tabla token_blocklist: {e}")

    # ✅ Agregamos la nueva columna y el índice a 'users'
    op.add_column('users', sa.Column('username', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_column('users', 'username')

    op.create_table(
        'token_blocklist',
        sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('jti', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
        sa.Column('token_type', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
        sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=True),
        sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
        sa.Column('revoked_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
        sa.Column('reason', sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('token_blocklist_user_id_fkey')),
        sa.PrimaryKeyConstraint('id', name=op.f('token_blocklist_pkey'))
    )

    # ✅ Recreamos los índices
    op.create_index(op.f('ix_token_blocklist_jti'), 'token_blocklist', ['jti'], unique=True)
    op.create_index(op.f('ix_token_blocklist_id'), 'token_blocklist', ['id'], unique=False)
    op.create_index(op.f('ix_token_blocklist_expires_at'), 'token_blocklist', ['expires_at'], unique=False)
    op.create_index(op.f('idx_blocklist_jti'), 'token_blocklist', ['jti'], unique=False)
    op.create_index(op.f('idx_blocklist_expires_at'), 'token_blocklist', ['expires_at'], unique=False)
