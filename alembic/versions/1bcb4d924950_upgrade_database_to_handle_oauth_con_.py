"""upgrade database to handle OAuth con Google y Magic Link

Revision ID: 1bcb4d924950
Revises: 20250912_add_accommodations
Create Date: 2025-09-19 17:50:19.306861

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1bcb4d924950'
down_revision: Union[str, Sequence[str], None] = '20250912_add_accommodations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Create user_social_accounts if it doesn't already exist
    existing_tables = inspector.get_table_names()
    if 'user_social_accounts' not in existing_tables:
        op.create_table(
            'user_social_accounts',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('provider', sa.String(length=20), nullable=False),
            sa.Column('provider_id', sa.String(length=255), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=True),
            sa.Column('given_name', sa.String(length=100), nullable=True),
            sa.Column('family_name', sa.String(length=100), nullable=True),
            sa.Column('email', sa.String(length=255), nullable=True),
            sa.Column('picture', sa.String(length=500), nullable=True),
            sa.Column('is_verified', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('last_used', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('provider', 'provider_id', name='uq_provider_social_account'),
        )
        op.create_index('idx_provider_lookup', 'user_social_accounts', ['provider', 'provider_id'], unique=False)
        op.create_index(op.f('ix_user_social_accounts_id'), 'user_social_accounts', ['id'], unique=False)

    # Drop itinerary_change_logs if it exists (legacy table)
    if 'itinerary_change_logs' in existing_tables:
        existing_indexes = {ix['name'] for ix in inspector.get_indexes('itinerary_change_logs')}
        if op.f('ix_itinerary_change_logs_itinerary_id') in existing_indexes:
            op.drop_index(op.f('ix_itinerary_change_logs_itinerary_id'), table_name='itinerary_change_logs')
        op.drop_table('itinerary_change_logs')

    # Drop old unique constraint in user_answers if it exists
    try:
        existing_uniques = {uc['name'] for uc in inspector.get_unique_constraints('user_answers')}
        if op.f('uq_user_test_question_option') in existing_uniques:
            op.drop_constraint(op.f('uq_user_test_question_option'), 'user_answers', type_='unique')
    except Exception:
        # Table may not exist or inspector may fail in some dbs; ignore
        pass

    # Drop legacy username/display_name index and columns if they exist
    try:
        existing_indexes = {ix['name'] for ix in inspector.get_indexes('users')}
        if op.f('ix_users_username') in existing_indexes:
            op.drop_index(op.f('ix_users_username'), table_name='users')
    except Exception:
        pass

    user_columns = [c['name'] for c in inspector.get_columns('users')]
    if 'password_hash' in user_columns:
        op.drop_column('users', 'password_hash')
    if 'username' in user_columns:
        op.drop_column('users', 'username')
    if 'display_name' in user_columns:
        op.drop_column('users', 'display_name')


def downgrade() -> None:
    """Downgrade schema."""
    # Best effort downgrade (recreate removed objects if they do not exist)
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Recreate username/display_name/password_hash
    user_columns = [c['name'] for c in inspector.get_columns('users')]
    if 'display_name' not in user_columns:
        op.add_column('users', sa.Column('display_name', sa.VARCHAR(length=150), nullable=True))
    if 'username' not in user_columns:
        op.add_column('users', sa.Column('username', sa.VARCHAR(length=50), nullable=True))
    if 'password_hash' not in user_columns:
        op.add_column('users', sa.Column('password_hash', sa.VARCHAR(length=255), nullable=False))

    existing_indexes = {ix['name'] for ix in inspector.get_indexes('users')}
    if op.f('ix_users_username') not in existing_indexes:
        op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Recreate old unique constraint if missing
    try:
        existing_uniques = {uc['name'] for uc in inspector.get_unique_constraints('user_answers')}
        if op.f('uq_user_test_question_option') not in existing_uniques:
            op.create_unique_constraint(op.f('uq_user_test_question_option'), 'user_answers', ['user_traveler_test_id', 'question_option_id'], postgresql_nulls_not_distinct=False)
    except Exception:
        pass

    existing_tables = inspector.get_table_names()
    if 'itinerary_change_logs' not in existing_tables:
        op.create_table('itinerary_change_logs',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('itinerary_id', sa.UUID(), nullable=False),
            sa.Column('user_prompt', sa.TEXT(), nullable=False),
            sa.Column('ai_response_summary', sa.TEXT(), nullable=True),
            sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['itinerary_id'], ['itineraries.itinerary_id'], name=op.f('itinerary_change_logs_itinerary_id_fkey'), ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id', name=op.f('itinerary_change_logs_pkey'))
        )
        op.create_index(op.f('ix_itinerary_change_logs_itinerary_id'), 'itinerary_change_logs', ['itinerary_id'], unique=False)

    if 'user_social_accounts' in existing_tables:
        op.drop_index(op.f('ix_user_social_accounts_id'), table_name='user_social_accounts')
        op.drop_index('idx_provider_lookup', table_name='user_social_accounts')
        op.drop_table('user_social_accounts')
