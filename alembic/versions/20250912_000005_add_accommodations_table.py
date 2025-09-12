"""add accommodations table

Revision ID: 20250912_add_accommodations
Revises: 20250815_remove_change_log
Create Date: 2025-09-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20250912_add_accommodations'
down_revision: Union[str, Sequence[str], None] = '20250815_remove_change_log'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = inspector.get_table_names()
    if 'accommodations' not in existing_tables:
        op.create_table(
            'accommodations',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('itinerary_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('city', sa.String(length=255), nullable=False),
            sa.Column('url', sa.Text(), nullable=False),
            sa.Column('title', sa.Text(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('img_urls', postgresql.JSON(astext_type=sa.Text()), server_default='[]', nullable=False),
            sa.Column('provider', sa.String(length=100), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['itinerary_id'], ['itineraries.itinerary_id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_accommodations_id'), 'accommodations', ['id'], unique=False)
        op.create_index(op.f('ix_accommodations_itinerary_id'), 'accommodations', ['itinerary_id'], unique=False)
        op.create_index(op.f('ix_accommodations_status'), 'accommodations', ['status'], unique=False)
        op.create_unique_constraint('uq_accommodations_itinerary_url', 'accommodations', ['itinerary_id', 'url'])
    else:
        # Table exists; ensure required column, indexes and unique constraint exist
        existing_columns = [c['name'] for c in inspector.get_columns('accommodations')]
        if 'city' not in existing_columns:
            # Add with a temporary default to satisfy NOT NULL, then drop default
            op.add_column('accommodations', sa.Column('city', sa.String(length=255), nullable=True))
            # Backfill nulls with empty string to satisfy not null
            op.execute("UPDATE accommodations SET city = '' WHERE city IS NULL")
            op.alter_column('accommodations', 'city', existing_type=sa.String(length=255), nullable=False)

        existing_indexes = {ix['name'] for ix in inspector.get_indexes('accommodations')}
        if op.f('ix_accommodations_itinerary_id') not in existing_indexes:
            op.create_index(op.f('ix_accommodations_itinerary_id'), 'accommodations', ['itinerary_id'], unique=False)
        if op.f('ix_accommodations_status') not in existing_indexes:
            op.create_index(op.f('ix_accommodations_status'), 'accommodations', ['status'], unique=False)

        existing_uniques = {uc['name'] for uc in inspector.get_unique_constraints('accommodations')}
        if 'uq_accommodations_itinerary_url' not in existing_uniques:
            op.create_unique_constraint('uq_accommodations_itinerary_url', 'accommodations', ['itinerary_id', 'url'])


def downgrade() -> None:
    op.drop_constraint('uq_accommodations_itinerary_url', 'accommodations', type_='unique')
    op.drop_index(op.f('ix_accommodations_status'), table_name='accommodations')
    op.drop_index(op.f('ix_accommodations_itinerary_id'), table_name='accommodations')
    op.drop_index(op.f('ix_accommodations_id'), table_name='accommodations')
    op.drop_table('accommodations')


