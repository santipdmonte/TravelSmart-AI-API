"""remove itinerary change log table

Revision ID: 20250815_remove_change_log
Revises: 20250814_000003_add_traveler_type_to_user
Create Date: 2025-08-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20250815_remove_change_log'
down_revision = '20250814_000003_add_traveler_type_to_user'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove the index first
    op.drop_index(op.f('ix_itinerary_change_logs_itinerary_id'), table_name='itinerary_change_logs')
    # Remove the table
    op.drop_table('itinerary_change_logs')


def downgrade() -> None:
    # Recreate the table
    op.create_table(
        'itinerary_change_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('itinerary_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_prompt', sa.Text(), nullable=False),
        sa.Column('ai_response_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['itinerary_id'], ['itineraries.itinerary_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # Recreate the index
    op.create_index(op.f('ix_itinerary_change_logs_itinerary_id'), 'itinerary_change_logs', ['itinerary_id'], unique=False)
