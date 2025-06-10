"""add_pecan_potato_partitions

Revision ID: 8466cecf4550
Revises: 8af4d8da6e9f
Create Date: 2025-06-05 15:01:43.640884

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8466cecf4550'
down_revision: Union[str, None] = '8af4d8da6e9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new partitions for pecan and potato species
    op.execute("""
        CREATE TABLE IF NOT EXISTS sequence_table_pecan PARTITION OF sequence_table FOR VALUES IN ('pecan');
        CREATE TABLE IF NOT EXISTS sequence_table_potato PARTITION OF sequence_table FOR VALUES IN ('potato');
    """)


def downgrade() -> None:
    # Remove the partitions for pecan and potato species
    op.execute("""
        DROP TABLE IF EXISTS sequence_table_pecan;
        DROP TABLE IF EXISTS sequence_table_potato;
    """)
