"""Change visited_countries from JSON to List[str]

Revision ID: e8e035f66129
Revises: 06ac05114ff3
Create Date: 2025-09-22 10:58:24.545155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e8e035f66129'
down_revision: Union[str, Sequence[str], None] = '06ac05114ff3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Convert users.visited_countries from JSON to TEXT[] while preserving data.
    Avoids subqueries in ALTER ... USING by using a temp column.
    Assumes JSON arrays of strings (e.g., ["ES", "FR"]).
    """
    # 1) Add temporary TEXT[] column
    op.add_column('users', sa.Column('visited_countries_tmp', postgresql.ARRAY(sa.Text()), nullable=True))

    # 2) Populate it from JSON, preserving NULLs and using empty array for []
    op.execute(
        """
        UPDATE users
        SET visited_countries_tmp = CASE
            WHEN visited_countries IS NULL THEN NULL
            ELSE COALESCE(
                (SELECT array_agg(elem)
                 FROM json_array_elements_text(visited_countries) AS elem),
                ARRAY[]::text[]
            )
        END
        """
    )

    # 3) Drop old column and rename temp
    op.drop_column('users', 'visited_countries')
    op.alter_column('users', 'visited_countries_tmp', new_column_name='visited_countries')


def downgrade() -> None:
    """Downgrade schema.

    Convert users.visited_countries from TEXT[] back to JSON.
    Uses a temp JSON column to avoid subqueries in transform expression.
    """
    # 1) Add temporary JSON column
    op.add_column('users', sa.Column('visited_countries_json', sa.JSON(), nullable=True))

    # 2) Populate it from TEXT[]
    op.execute(
        """
        UPDATE users
        SET visited_countries_json = CASE
            WHEN visited_countries IS NULL THEN NULL
            ELSE to_json(visited_countries)
        END
        """
    )

    # 3) Drop array column and rename temp to original
    op.drop_column('users', 'visited_countries')
    op.alter_column('users', 'visited_countries_json', new_column_name='visited_countries')
