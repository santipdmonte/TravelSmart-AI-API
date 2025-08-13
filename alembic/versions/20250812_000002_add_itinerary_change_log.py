"""add itinerary change log table

Revision ID: 20250812_add_change_log
Revises: 20250811_000001_add_multi_select_to_questions
Create Date: 2025-08-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20250812_add_change_log'
down_revision = '20250811_000001'
branch_labels = None
depends_on = None


def upgrade() -> None:
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
    op.create_index(op.f('ix_itinerary_change_logs_itinerary_id'), 'itinerary_change_logs', ['itinerary_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_itinerary_change_logs_itinerary_id'), table_name='itinerary_change_logs')
    op.drop_table('itinerary_change_logs')
